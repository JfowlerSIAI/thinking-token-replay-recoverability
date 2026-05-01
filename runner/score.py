"""Answer extraction and grading for the thinking-token experiment.

Primary rule (ITT): extraction failures are scored as incorrect.
Sensitivity analysis: exclude failures (reported separately).
"""

import re
from typing import Optional


def extract_answer(content: str) -> tuple[str, bool, str]:
    """Extract the final answer from model output.

    Returns:
        (extracted_answer, extraction_failed, extraction_method)
    """
    if not content or not content.strip():
        return "", True, "empty"

    # Primary: look for FINAL: line (allow leading whitespace)
    # Use findall to get the LAST match — models may self-correct and produce
    # multiple FINAL: lines; the last one is the intended answer.
    final_matches = re.findall(
        r"^\s*FINAL:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE
    )
    if final_matches:
        answer = final_matches[-1].strip()
        if answer:
            return normalize_answer(answer), False, "final_tag"

    # Fallback patterns on the full content (not just last line)
    # Try "the answer is X" anywhere
    answer_is = re.search(
        r"(?:the answer is|answer:|therefore,? the answer is)\s*(.+?)(?:\.|$)",
        content, re.IGNORECASE | re.MULTILINE,
    )
    if answer_is:
        answer = answer_is.group(1).strip()
        if answer:
            return normalize_answer(answer), False, "answer_is"

    # Fallback: last non-empty line
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    if lines:
        last = lines[-1]
        # MCQ letter at start or end of line (allow trailing period/paren)
        mcq = re.match(r"^\s*\(?([A-Da-d])\)?\s*[.:]?\s*$", last)
        if mcq:
            return normalize_answer(mcq.group(1)), False, "mcq_last_line"

        # MCQ letter anywhere in short last line
        if len(last) < 30:
            mcq2 = re.search(r"\b([A-Da-d])\b", last)
            if mcq2 and any(c in content.upper() for c in "ABCD"):
                return normalize_answer(mcq2.group(1)), False, "mcq_short_line"

        # Bare number (possibly with sign, decimal, commas)
        num = re.match(r"^\s*(-?\d[\d,]*(?:\.\d+)?)\s*$", last)
        if num:
            return normalize_answer(num.group(1)), False, "bare_number"

        # Number at end of line after equals sign
        eq_num = re.search(r"=\s*(-?\d[\d,]*(?:\.\d+)?)\s*$", last)
        if eq_num:
            return normalize_answer(eq_num.group(1)), False, "equals_number"

    return "", True, "no_match"


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    answer = answer.strip().lower()
    # Remove trailing punctuation
    answer = answer.rstrip(".,;:!?")
    # Remove dollar/percent signs
    answer = answer.replace("$", "").replace("%", "").strip()
    # Remove common prefixes
    for prefix in ["the answer is", "answer:", "answer is", "option "]:
        if answer.startswith(prefix):
            answer = answer[len(prefix):].strip()
    # Remove enclosing parens/brackets
    if answer.startswith("(") and answer.endswith(")"):
        answer = answer[1:-1].strip()
    # Normalize whitespace
    answer = " ".join(answer.split())
    # Try numeric normalization
    answer = _normalize_numeric(answer)
    return answer


def _normalize_numeric(answer: str) -> str:
    """Parse as number and return canonical form."""
    try:
        val = float(answer.replace(",", ""))
        if val == int(val) and "." not in answer.replace(",", ""):
            return str(int(val))
        return str(val)
    except (ValueError, OverflowError):
        return answer


def grade(extracted: str, ground_truth: str, answer_type: str = "exact") -> bool:
    """Grade an extracted answer against ground truth."""
    if not extracted:
        return False

    norm_truth = normalize_answer(ground_truth)
    norm_extracted = extracted

    if answer_type == "mcq":
        truth_letter = _extract_mcq_letter(norm_truth)
        extracted_letter = _extract_mcq_letter(norm_extracted)
        if truth_letter and extracted_letter:
            return truth_letter == extracted_letter

    if answer_type == "numeric":
        return _numeric_equal(norm_extracted, norm_truth)

    return norm_extracted == norm_truth


def _extract_mcq_letter(s: str) -> str:
    """Extract MCQ letter (a/b/c/d) from answer string."""
    s = s.strip().lower()
    if s and s[0] in "abcd":
        return s[0]
    m = re.match(r"^\(?([abcd])\)?", s)
    return m.group(1) if m else ""


def _numeric_equal(a: str, b: str, tol: float = 0.01) -> bool:
    """Check numeric equality with tolerance (1% relative or 0.01 absolute)."""
    try:
        va = float(a.replace(",", ""))
        vb = float(b.replace(",", ""))
        return abs(va - vb) <= max(tol, tol * abs(vb))
    except (ValueError, OverflowError):
        return False


def score_inference(result, ground_truth: str, answer_type: str = "exact"):
    """Score an InferenceResult in-place."""
    result.ground_truth = ground_truth
    answer, failed, method = extract_answer(result.content)
    result.extracted_answer = answer
    result.extraction_failed = failed
    result.correct = grade(answer, ground_truth, answer_type) if not failed else False

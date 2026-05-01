"""Trace bank management for the thinking-token experiment.

The trace bank stores B-condition thinking traces for reuse in C/F/G/J conditions.
Each trace is keyed by (question_id, model_tag, seed).

Protocol (from plan §3):
1. Before Phase 2, run B on all locked items with fixed seed grid (seeds 1-12)
2. Freeze the bank — no traces regenerated after this
3. Each C/F/G/J replicate r uses the trace from B's seed r (1:1 pairing)
4. Log source_trace_id and source_trace_correct for every derived condition
5. Derive F from C's source trace (tokenizer-level shuffle)
6. Derive J (filler matched to source trace length)
7. Derive G from a different question's trace with strict constraints
"""

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import tiktoken

# Use cl100k_base as a consistent token-counting approximation for both Qwen and
# Gemma models.  Neither model uses this exact tokenizer, but the requirement from
# the experimental protocol is *consistency* across conditions F/G/I/J, not exact
# model-native counts.  cl100k_base (BPE, ~100k vocab) produces counts within ~10%
# of both models' native tokenizers and is deterministic, fast, and well-tested.
_TOKENIZER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding.

    This is the single source of truth for token counting across the entire
    experiment.  All token-length matching (Conditions F, G, I, J) and the
    token_count field on TraceEntry use this function.

    Returns 0 for empty/None text.
    """
    if not text:
        return 0
    return len(_TOKENIZER.encode(text))


@dataclass
class TraceEntry:
    """A single trace in the bank."""
    trace_id: str  # "{question_id}_{model_tag}_{seed}"
    question_id: str
    model_tag: str
    seed: int
    thinking_tokens: str
    content: str  # model's final answer content
    correct: bool
    token_count: int  # BPE token count via cl100k_base (see count_tokens())
    domain: str  # math, logic, factual, spatial

    def to_dict(self) -> dict:
        return asdict(self)


class TraceBank:
    """Manages the frozen B-trace bank."""

    def __init__(self, bank_dir: Path):
        self.bank_dir = bank_dir
        self.bank_dir.mkdir(parents=True, exist_ok=True)
        self._traces: dict[str, TraceEntry] = {}
        self._load()

    def _bank_file(self) -> Path:
        return self.bank_dir / "trace_bank.jsonl"

    def _load(self) -> None:
        """Load existing trace bank from disk.

        Recomputes token_count on load using count_tokens() (BPE via cl100k_base)
        to handle traces written with the old word-count metric.
        """
        path = self._bank_file()
        if not path.exists():
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = TraceEntry(**data)
                # Migrate: recompute token_count from thinking_tokens using BPE
                entry.token_count = count_tokens(entry.thinking_tokens)
                self._traces[entry.trace_id] = entry

    def save(self) -> None:
        """Write full bank to disk (overwrites)."""
        with open(self._bank_file(), "w") as f:
            for entry in self._traces.values():
                f.write(json.dumps(entry.to_dict()) + "\n")

    def add_trace(
        self,
        question_id: str,
        model_tag: str,
        seed: int,
        thinking_tokens: str,
        content: str,
        correct: bool,
        domain: str,
    ) -> TraceEntry:
        """Add a B-condition trace to the bank."""
        trace_id = f"{question_id}_{model_tag}_{seed}"
        entry = TraceEntry(
            trace_id=trace_id,
            question_id=question_id,
            model_tag=model_tag,
            seed=seed,
            thinking_tokens=thinking_tokens,
            content=content,
            correct=correct,
            token_count=count_tokens(thinking_tokens),
            domain=domain,
        )
        self._traces[trace_id] = entry
        # Append to file incrementally
        with open(self._bank_file(), "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def get_trace(self, question_id: str, model_tag: str, seed: int) -> Optional[TraceEntry]:
        """Get the trace for a specific (question, model, seed) tuple."""
        trace_id = f"{question_id}_{model_tag}_{seed}"
        return self._traces.get(trace_id)

    def get_paired_trace(self, question_id: str, model_tag: str, rep: int, seed_grid: list[int]) -> Optional[TraceEntry]:
        """Get the trace paired to a specific replicate (1:1 pairing).

        Rep r uses seed_grid[r] from the trace bank.
        """
        if rep >= len(seed_grid):
            return None
        return self.get_trace(question_id, model_tag, seed_grid[rep])

    def get_wrong_question_trace(
        self,
        question_id: str,
        model_tag: str,
        seed: int,
        target_token_count: int,
        domain: str,
        question_text: str = "",
        answer_text: str = "",
        blacklist_ids: Optional[set] = None,
        tolerance: float = 0.05,
    ) -> Optional[TraceEntry]:
        """Find a trace from a different question for Condition G.

        Constraints (from plan §3):
        - Different question (not question_id)
        - Same domain category
        - Token count within ±tolerance (default 5%)
        - Not in blacklist (isomorphic pairs, shared entities)
        - <20% content token overlap with target question/answer
        """
        if blacklist_ids is None:
            blacklist_ids = set()

        candidates = []
        min_count = int(target_token_count * (1 - tolerance))
        max_count = int(target_token_count * (1 + tolerance))

        target_words = set()
        if question_text:
            target_words = set(question_text.lower().split())
        if answer_text:
            target_words |= set(answer_text.lower().split())

        for entry in self._traces.values():
            if entry.question_id == question_id:
                continue
            if entry.model_tag != model_tag:
                continue
            if entry.domain != domain:
                continue
            if entry.question_id in blacklist_ids:
                continue
            if not (min_count <= entry.token_count <= max_count):
                continue

            # Overlap filter
            if target_words:
                trace_words = set(entry.thinking_tokens.lower().split())
                overlap = len(trace_words & target_words) / max(len(trace_words), 1)
                if overlap > 0.20:
                    continue

            candidates.append(entry)

        if not candidates:
            return None

        # Deterministic selection based on seed
        rng = random.Random(seed)
        return rng.choice(candidates)

    def get_cross_model_trace(
        self,
        question_id: str,
        source_model: str,
        seed: int,
    ) -> Optional[TraceEntry]:
        """Get trace from the other model for Condition K."""
        return self.get_trace(question_id, source_model, seed)

    def get_all_for_question(self, question_id: str, model_tag: str) -> list[TraceEntry]:
        """Get all traces for a question/model pair (across seeds)."""
        return [
            e for e in self._traces.values()
            if e.question_id == question_id and e.model_tag == model_tag
        ]

    @property
    def size(self) -> int:
        return len(self._traces)

    def summary(self) -> dict:
        """Return summary statistics."""
        models = set()
        questions = set()
        correct_count = 0
        for e in self._traces.values():
            models.add(e.model_tag)
            questions.add(e.question_id)
            if e.correct:
                correct_count += 1
        return {
            "total_traces": len(self._traces),
            "models": sorted(models),
            "questions": len(questions),
            "correct_rate": correct_count / max(len(self._traces), 1),
        }


def shuffle_tokens(text: str, seed: int = 0) -> str:
    """Tokenizer-level shuffle using cl100k_base encoding.

    Protocol (plan §3, Condition F):
    1. Encode text to BPE token IDs
    2. Shuffle the token ID sequence
    3. Decode back to text

    This destroys semantic coherence while preserving token-level statistics.
    Note: encode→shuffle→decode→re-encode is NOT bijective for BPE — greedy
    re-merging after shuffle can change token count. We record the actual
    shuffled token count rather than asserting equality, since the experimental
    requirement is semantic destruction, not exact count preservation.
    """
    token_ids = _TOKENIZER.encode(text)
    rng = random.Random(seed)
    rng.shuffle(token_ids)
    shuffled_text = _TOKENIZER.decode(token_ids)
    return shuffled_text


# Keep old name as alias for backward compatibility during transition
shuffle_tokens_word_level = shuffle_tokens

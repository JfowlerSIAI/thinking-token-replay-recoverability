"""Prompt construction for each experimental condition (A–O).

Non-prefill conditions (A/B/I/N/O) return ChatMessages for /api/chat.
Prefill conditions (C/D/E/F/G/H/J/K/L/M) return PrefillSpec for /api/generate
with raw=True, because the chat API does not reliably continue from assistant
prefill across all model families (verified: Gemma 4 ignores chat prefill,
Qwen works, but raw mode works for both).
"""

import random
from dataclasses import dataclass

from trace_bank import count_tokens

ChatMessages = list[dict[str, str]]


@dataclass
class PrefillSpec:
    """Specification for a prefill condition — routed to /api/generate raw mode."""
    question_text: str
    prefill_text: str


# Standard answer instruction appended to all question prompts
ANSWER_INSTRUCTION = (
    "\n\nState your final answer on a new line starting with FINAL: "
    "followed by your answer."
)

COT_INSTRUCTION = (
    "Think step by step, show your reasoning, then give your final answer."
)

FILLER_SENTENCES = [
    "The capital of France is Paris.",
    "Water boils at 100 degrees Celsius at standard pressure.",
    "The Earth orbits the Sun once every 365.25 days.",
    "Sound travels at approximately 343 meters per second in air.",
    "The Pacific Ocean is the largest ocean on Earth.",
    "Gold has the chemical symbol Au on the periodic table.",
    "A standard piano has 88 keys.",
    "The speed of light in a vacuum is approximately 299,792 kilometers per second.",
    "Mount Everest is the tallest mountain above sea level.",
    "The human body contains 206 bones in the adult skeleton.",
    "Nitrogen makes up approximately 78 percent of Earth's atmosphere.",
    "A hexagon has six sides.",
    "The freezing point of water is 0 degrees Celsius.",
    "Jupiter is the largest planet in our solar system.",
    "The Great Wall of China is over 21,000 kilometers long.",
]


def build_question_prompt(question_text: str) -> str:
    return question_text.strip() + ANSWER_INSTRUCTION


def build_system_message() -> str:
    return "You are a helpful assistant. Answer the question accurately and concisely."


def _base_messages(question_text: str) -> ChatMessages:
    return [
        {"role": "system", "content": build_system_message()},
        {"role": "user", "content": build_question_prompt(question_text)},
    ]


# ---------------------------------------------------------------------------
# Non-prefill conditions → ChatMessages (for /api/chat)
# ---------------------------------------------------------------------------

def condition_a(question_text: str) -> ChatMessages:
    """A: Baseline — no thinking, no extra context."""
    return _base_messages(question_text)


def condition_b(question_text: str) -> ChatMessages:
    """B: Standard thinking. Caller sets think=True."""
    return _base_messages(question_text)


def condition_i(question_text: str) -> ChatMessages:
    """I: Token-matched SC. Same prompt as A; caller handles k attempts."""
    return condition_a(question_text)


def condition_n(question_text: str) -> ChatMessages:
    """N: Deterministic thinking (temperature 0).

    Same prompt as B (think=True), but the caller overrides temperature to 0.0
    for greedy decoding.  This tests whether stochastic sampling in the thinking
    phase adds value, or whether greedy (deterministic) thinking is equally good.

    The plan (§3, Phase 3) defines N as "empty-trace think mode / forced minimal
    trace (exploratory)."  Because Ollama does not expose a reliable mechanism to
    force an empty or minimal thinking trace across both Qwen and Gemma, we
    implement the closest feasible variant: deterministic thinking at temperature 0.
    This still isolates a key variable (sampling randomness in the think phase)
    while remaining implementable on both model families.
    """
    return condition_b(question_text)


def condition_o(question_text: str) -> ChatMessages:
    """O: Visible-CoT — explicit CoT prompting without think mode."""
    prompt = COT_INSTRUCTION + "\n\n" + build_question_prompt(question_text)
    return [
        {"role": "system", "content": build_system_message()},
        {"role": "user", "content": prompt},
    ]


# ---------------------------------------------------------------------------
# Prefill conditions → PrefillSpec (for /api/generate raw mode)
# ---------------------------------------------------------------------------

def _strip_final_answer(text: str) -> str:
    """Remove FINAL: answer line from scaffold text.

    Scaffolds are complete solutions (reasoning + answer), but when used as
    prefill the model must generate its own answer.  Leaving FINAL: in the
    prefill causes an immediate EOS (eval_count=1).
    """
    import re
    return re.sub(r'\n\s*FINAL:.*$', '', text, flags=re.IGNORECASE | re.DOTALL).rstrip()


def condition_c(question_text: str, trace_text: str) -> PrefillSpec:
    """C: Self-trace replay — B's thinking tokens as assistant prefill."""
    return PrefillSpec(question_text, trace_text)


def condition_d(question_text: str, scaffold_text: str) -> PrefillSpec:
    """D: Expert scaffold — Sonnet reasoning as assistant prefill."""
    return PrefillSpec(question_text, _strip_final_answer(scaffold_text))


def condition_e(question_text: str, scaffold_text: str) -> ChatMessages:
    """E: Thinking + scaffold — expert reasoning as context with think mode on.

    Originally designed as scaffold prefill + think mode via raw /api/generate.
    However, Ollama's raw mode does not support thinking — think tokens are never
    generated in raw mode (verified: 0/160 records across both models in smoke
    test). Redesigned to provide the scaffold as explicit context in the user
    message via /api/chat, where thinking is fully supported.

    This tests whether thinking adds value when the model has access to expert
    reasoning context — the synergy between external reasoning and internal
    thinking.
    """
    clean_scaffold = _strip_final_answer(scaffold_text)
    prompt = (
        "An expert provided the following step-by-step reasoning for this question:\n\n"
        + clean_scaffold
        + "\n\nUsing this reasoning as reference, answer the following question.\n\n"
        + build_question_prompt(question_text)
    )
    return [
        {"role": "system", "content": build_system_message()},
        {"role": "user", "content": prompt},
    ]


def condition_f(question_text: str, shuffled_text: str) -> PrefillSpec:
    """F: Shuffled tokens as prefill."""
    return PrefillSpec(question_text, shuffled_text)


def condition_g(question_text: str, wrong_trace_text: str) -> PrefillSpec:
    """G: Wrong-question trace as prefill."""
    return PrefillSpec(question_text, wrong_trace_text)


def condition_h(question_text: str, wrong_scaffold_text: str) -> PrefillSpec:
    """H: Minimally-wrong scaffold as prefill."""
    return PrefillSpec(question_text, _strip_final_answer(wrong_scaffold_text))


def condition_j(question_text: str, target_token_count: int) -> PrefillSpec:
    """J: Filler tokens — semantically neutral filler matched to trace token count.

    The target_token_count comes from the paired B-trace's token_count field
    (measured via count_tokens / cl100k_base), ensuring J and C share identical
    token counts per item per rep, as required by Contrast #8 (C - J).
    """
    filler = generate_filler(target_token_count)
    return PrefillSpec(question_text, filler)


def condition_k(question_text: str, cross_model_trace: str) -> PrefillSpec:
    """K: Cross-model transfer."""
    return PrefillSpec(question_text, cross_model_trace)


def condition_l(question_text: str, trace_text: str, fraction: float) -> PrefillSpec:
    """L: Dose-response — prefix-truncated trace at token level.

    Truncates the trace to the first `fraction` of its BPE tokens (measured via
    count_tokens / cl100k_base), then decodes back to text.  This preserves
    token-level measurement consistency with the other length-matched conditions.
    """
    from trace_bank import _TOKENIZER
    token_ids = _TOKENIZER.encode(trace_text)
    cutoff = max(1, int(len(token_ids) * fraction))
    truncated = _TOKENIZER.decode(token_ids[:cutoff])
    return PrefillSpec(question_text, truncated)


def condition_m(question_text: str, compressed_trace: str) -> PrefillSpec:
    """M: Compressed trace."""
    return PrefillSpec(question_text, _strip_final_answer(compressed_trace))


# ---------------------------------------------------------------------------
# Raw prompt builder — converts PrefillSpec to model-specific raw prompt
# ---------------------------------------------------------------------------

def build_raw_prefill_prompt(
    spec: PrefillSpec,
    template_tokens: dict,
    think_transition: bool = False,
) -> str:
    """Build a raw prompt string for /api/generate with assistant prefill.

    Args:
        spec: PrefillSpec with question_text and prefill_text
        template_tokens: Model-specific special tokens
        think_transition: If True, append think_start token after prefill (for Condition E)
    """
    t = template_tokens
    clean_prefill = spec.prefill_text.rstrip()

    parts = [
        t["system_start"],
        build_system_message(),
        t["system_end"],
        t["user_start"],
        build_question_prompt(spec.question_text),
        t["user_end"],
        t["assistant_start"],
        clean_prefill,
        "\n\n",
    ]

    if think_transition:
        parts.append(t.get("think_start", "<think>\n"))

    return "".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shuffle_words(text: str, seed: int = 0) -> str:
    """Delegate to tokenizer-level shuffle in trace_bank.

    Kept for backward compatibility; new code should use
    trace_bank.shuffle_tokens() directly.
    """
    from trace_bank import shuffle_tokens
    return shuffle_tokens(text, seed=seed)


def generate_filler(target_token_count: int) -> str:
    """Generate semantically neutral filler text matched to a target token count.

    Builds filler by repeating sentences from the FILLER_SENTENCES bank until
    the token count (measured via count_tokens / cl100k_base) reaches or exceeds
    the target.  Then trims at the word boundary closest to the target token count.

    This ensures Condition J's filler has the same token count as the paired
    B-trace, as required by the protocol for Contrast #8 (C - J).
    """
    if target_token_count <= 0:
        return ""

    # Build up filler sentence by sentence until we overshoot
    filler_text = ""
    idx = 0
    while count_tokens(filler_text) < target_token_count:
        sentence = FILLER_SENTENCES[idx % len(FILLER_SENTENCES)]
        filler_text = (filler_text + " " + sentence).strip()
        idx += 1

    # Trim to match target token count: remove words from the end until we hit
    # the target (± 1 token tolerance since we can only cut at word boundaries)
    words = filler_text.split()
    while len(words) > 1 and count_tokens(" ".join(words)) > target_token_count:
        words.pop()

    return " ".join(words)


# ---------------------------------------------------------------------------
# Dispatch registry
# ---------------------------------------------------------------------------

CONDITION_REGISTRY = {
    "A": {"think": False, "prefill": False},
    "B": {"think": True,  "prefill": False},
    "C": {"think": False, "prefill": True},
    "D": {"think": False, "prefill": True},
    "E": {"think": True,  "prefill": False},
    "F": {"think": False, "prefill": True},
    "G": {"think": False, "prefill": True},
    "H": {"think": False, "prefill": True},
    "I": {"think": False, "prefill": False},
    "J": {"think": False, "prefill": True},
    "K": {"think": False, "prefill": True},
    "L": {"think": False, "prefill": True},
    "M": {"think": False, "prefill": True},
    "N": {"think": True,  "prefill": False},
    "O": {"think": False, "prefill": False},
}

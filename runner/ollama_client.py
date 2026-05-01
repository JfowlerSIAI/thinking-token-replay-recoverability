"""Ollama API client with per-inference logging for the thinking-token experiment.

Wraps /api/chat and /api/generate endpoints. Every call returns a structured
InferenceResult and appends a JSONL log line to the run's log file.
"""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests

OLLAMA_BASE = "http://localhost:11434"
DEFAULT_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "num_ctx": 8192,
    "num_predict": 1024,  # Base limit for non-thinking conditions (raised from 512)
    "repeat_penalty": 1.0,
}

# Thinking conditions need more tokens (reasoning + answer).
# Raised from 4096: trace bank shows Qwen thinking traces up to ~3,989
# cl100k_base tokens, which maps to ~4,400+ model-native tokens. 4096 was
# causing eval_count ceiling hits with empty content in Phase 2.
THINKING_NUM_PREDICT = 8192


@dataclass
class InferenceResult:
    """Structured result from a single Ollama inference call."""
    inference_id: str
    model_tag: str
    model_digest: str = ""
    quantization: str = ""
    ollama_version: str = ""
    condition: str = ""
    question_id: str = ""
    rep_number: int = 0
    seed: int = 0
    think: bool = False
    # Token counts from Ollama response
    prompt_eval_count: int = 0
    eval_count: int = 0
    # Timing (nanoseconds from Ollama)
    total_duration: int = 0
    load_duration: int = 0
    prompt_eval_duration: int = 0
    eval_duration: int = 0
    # Content
    raw_prompt: str = ""
    raw_response: str = ""
    thinking_tokens: str = ""
    content: str = ""
    # Scoring (filled by score.py)
    extracted_answer: str = ""
    ground_truth: str = ""
    correct: Optional[bool] = None
    extraction_failed: bool = False
    # Trace sourcing (for C/F/G/J conditions)
    source_trace_id: str = ""
    source_trace_correct: Optional[bool] = None
    # Parent linkage (for Condition I sub-inferences)
    parent_inference_id: str = ""
    # Error tracking
    error: str = ""
    # Timestamp
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModelInfo:
    """Cached model metadata from /api/show."""
    tag: str
    digest: str
    family: str
    parameter_size: str
    quantization: str
    template: str
    has_renderer: bool
    raw_modelfile: str


class OllamaClient:
    """Client for Ollama API with experiment-specific logging."""

    def __init__(self, base_url: str = OLLAMA_BASE, log_path: Optional[Path] = None):
        self.base_url = base_url.rstrip("/")
        self.log_path = log_path
        self._model_cache: dict[str, ModelInfo] = {}
        self._ollama_version: str = ""

    def get_ollama_version(self) -> str:
        if self._ollama_version:
            return self._ollama_version
        try:
            r = requests.get(f"{self.base_url}/api/version", timeout=5)
            r.raise_for_status()
            self._ollama_version = r.json().get("version", "unknown")
        except Exception:
            self._ollama_version = "unknown"
        return self._ollama_version

    def get_model_info(self, model: str) -> ModelInfo:
        if model in self._model_cache:
            return self._model_cache[model]
        r = requests.post(
            f"{self.base_url}/api/show",
            json={"model": model},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        details = data.get("details", {})
        modelfile = data.get("modelfile", "")
        info = ModelInfo(
            tag=model,
            digest=data.get("digest", ""),
            family=details.get("family", ""),
            parameter_size=details.get("parameter_size", ""),
            quantization=details.get("quantization_level", ""),
            template=data.get("template", ""),
            has_renderer="RENDERER" in modelfile,
            raw_modelfile=modelfile,
        )
        self._model_cache[model] = info
        return info

    def chat(
        self,
        model: str,
        messages: list[dict],
        *,
        think: bool = False,
        seed: int = 42,
        options: Optional[dict] = None,
        keep_alive: str = "0",
        condition: str = "",
        question_id: str = "",
        rep_number: int = 0,
    ) -> InferenceResult:
        """Send a chat request and return structured result.

        Args:
            model: Ollama model tag (e.g. "qwen3.5:9b")
            messages: Chat messages in Ollama format
            think: Enable thinking mode
            seed: Random seed for reproducibility
            options: Override default generation options
            keep_alive: Model keep-alive duration ("0" = unload after each call)
            condition: Experiment condition label (A-O)
            question_id: Question identifier
            rep_number: Replication number
        """
        merged_options = {**DEFAULT_OPTIONS, "seed": seed}
        if think:
            merged_options["num_predict"] = THINKING_NUM_PREDICT
        if options:
            merged_options.update(options)

        payload = {
            "model": model,
            "messages": messages,
            "think": think,
            "stream": False,
            "keep_alive": keep_alive,
            "options": merged_options,
        }

        inference_id = str(uuid.uuid4())[:8]
        raw_prompt = json.dumps(messages)
        model_info = self.get_model_info(model)

        result = InferenceResult(
            inference_id=inference_id,
            model_tag=model,
            model_digest=model_info.digest,
            quantization=model_info.quantization,
            ollama_version=self.get_ollama_version(),
            condition=condition,
            question_id=question_id,
            rep_number=rep_number,
            seed=seed,
            think=think,
            raw_prompt=raw_prompt,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )

        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()

            msg = data.get("message", {})
            result.content = msg.get("content", "")
            result.thinking_tokens = msg.get("thinking", "")
            result.raw_response = json.dumps(data)
            result.prompt_eval_count = data.get("prompt_eval_count", 0) or 0
            result.eval_count = data.get("eval_count", 0) or 0
            result.total_duration = data.get("total_duration", 0) or 0
            result.load_duration = data.get("load_duration", 0) or 0
            result.prompt_eval_duration = data.get("prompt_eval_duration", 0) or 0
            result.eval_duration = data.get("eval_duration", 0) or 0

        except requests.Timeout:
            result.error = "timeout"
        except requests.RequestException as e:
            result.error = str(e)

        self._log(result)
        return result

    def generate_raw(
        self,
        model: str,
        prompt: str,
        *,
        think: bool = False,
        seed: int = 42,
        options: Optional[dict] = None,
        keep_alive: str = "0",
        condition: str = "",
        question_id: str = "",
        rep_number: int = 0,
    ) -> InferenceResult:
        """Send a raw /api/generate request — used for assistant-prefill conditions.

        The `prompt` should be the fully-rendered template including any prefill text.
        Set raw=True in payload so Ollama does not re-wrap it.
        """
        merged_options = {**DEFAULT_OPTIONS, "seed": seed}
        if think:
            merged_options["num_predict"] = THINKING_NUM_PREDICT
        if options:
            merged_options.update(options)

        payload = {
            "model": model,
            "prompt": prompt,
            "raw": True,
            "think": think,
            "stream": False,
            "keep_alive": keep_alive,
            "options": merged_options,
        }

        inference_id = str(uuid.uuid4())[:8]
        model_info = self.get_model_info(model)

        result = InferenceResult(
            inference_id=inference_id,
            model_tag=model,
            model_digest=model_info.digest,
            quantization=model_info.quantization,
            ollama_version=self.get_ollama_version(),
            condition=condition,
            question_id=question_id,
            rep_number=rep_number,
            seed=seed,
            think=think,
            raw_prompt=prompt,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )

        try:
            r = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()

            result.content = data.get("response", "")
            result.thinking_tokens = data.get("thinking", "")
            result.raw_response = json.dumps(data)
            result.prompt_eval_count = data.get("prompt_eval_count", 0) or 0
            result.eval_count = data.get("eval_count", 0) or 0
            result.total_duration = data.get("total_duration", 0) or 0
            result.load_duration = data.get("load_duration", 0) or 0
            result.prompt_eval_duration = data.get("prompt_eval_duration", 0) or 0
            result.eval_duration = data.get("eval_duration", 0) or 0

        except requests.Timeout:
            result.error = "timeout"
        except requests.RequestException as e:
            result.error = str(e)

        self._log(result)
        return result

    def _log(self, result: InferenceResult) -> None:
        """Append result as JSONL to log file.

        NOTE: This is called internally after each API call, before scoring.
        For fully-scored results, use log_scored() after score_inference().
        """
        # Don't log here — defer to log_scored() so scoring data is included.
        pass

    def log_scored(self, result: InferenceResult) -> None:
        """Append a fully-scored result as JSONL to log file.

        Call this AFTER score_inference() to capture ground_truth, correct, etc.
        """
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")


def get_model_template_tokens(client: OllamaClient, model: str) -> dict:
    """Extract the model's chat template tokens for building raw prompts.

    Returns dict with keys like 'user_start', 'user_end', 'assistant_start',
    'assistant_end', 'system_start', 'system_end' based on the model family.
    """
    info = client.get_model_info(model)

    if info.has_renderer:
        # Models with RENDERER (qwen3.5) use Ollama's built-in renderer.
        # We derive tokens from known patterns.
        if "qwen" in info.family.lower():
            return {
                "system_start": "<|im_start|>system\n",
                "system_end": "<|im_end|>\n",
                "user_start": "<|im_start|>user\n",
                "user_end": "<|im_end|>\n",
                "assistant_start": "<|im_start|>assistant\n",
                "assistant_end": "<|im_end|>\n",
                "think_start": "<think>\n",
                "think_end": "</think>\n",
            }

    # Parse from explicit template
    template = info.template
    if "gemma" in info.family.lower():
        # Gemma puts system instructions in the user turn.
        # system_start opens the user turn; system_end is empty (no close).
        # user_start is empty (continues same turn); user_end closes it.
        return {
            "system_start": "<start_of_turn>user\n",
            "system_end": "\n\n",  # just spacing, no turn close
            "user_start": "",  # continues in the same user turn
            "user_end": "<end_of_turn>\n",
            "assistant_start": "<start_of_turn>model\n",
            "assistant_end": "<end_of_turn>\n",
            "think_start": "<think>\n",
            "think_end": "</think>\n",
        }

    # Fallback: generic ChatML-like
    return {
        "system_start": "<|im_start|>system\n",
        "system_end": "<|im_end|>\n",
        "user_start": "<|im_start|>user\n",
        "user_end": "<|im_end|>\n",
        "assistant_start": "<|im_start|>assistant\n",
        "assistant_end": "<|im_end|>\n",
        "think_start": "<think>\n",
        "think_end": "</think>\n",
    }

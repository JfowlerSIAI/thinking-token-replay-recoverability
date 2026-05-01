### Evidence Summary
- On Ollama’s official [gemma4 library page](https://ollama.com/library/gemma4), `gemma4:e4b` is explicitly marked `latest`, and both `gemma4:latest` and `gemma4:e4b` are listed as `9.6GB` with `128K` context.
- The dedicated Ollama tag pages for [`gemma4:latest`](https://ollama.com/library/gemma4:latest) and [`gemma4:e4b`](https://ollama.com/library/gemma4:e4b) have the same digest `c6eb396dbd59`, the same `8B` parameter count, the same `Q4_K_M` quantization, and the same `9.6GB` size. That is a direct alias match.
- Ollama’s [`gemma4:e2b`](https://ollama.com/library/gemma4:e2b) page is different: digest `7fbdbf8f5e45`, `5.12B` params, `Q4_K_M`, `7.2GB`. So `latest` is not E2B.
- Google’s official [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) says E4B is `4.5B effective (8B with embeddings)`, while E2B is `2.3B effective (5.1B with embeddings)`. That exactly explains why Ollama reports `8.0B`.
- Google’s official configs show only [E4B](https://huggingface.co/google/gemma-4-E4B/blob/main/config.json) has `text_config.hidden_size = 2560` and `max_position_embeddings = 131072`. [E2B](https://huggingface.co/google/gemma-4-E2B/blob/main/config.json) is `1536`, [26B A4B](https://huggingface.co/google/gemma-4-26B-A4B/blob/main/config.json) is `2816`, and [31B](https://huggingface.co/google/gemma-4-31B/blob/main/config.json) is `5376`.
- Google’s model card says only E2B and E4B have audio; 26B A4B and 31B are text+image only. Your local `ollama show` reports audio support, so 26B/31B are ruled out.

### Architecture Analysis
Google’s naming is:

| Variant | Effective/Active params | Total params |
|---|---:|---:|
| E2B | 2.3B effective | 5.1B with embeddings |
| E4B | 4.5B effective | 8.0B with embeddings |
| 26B A4B | 3.8B active | 25.2B total |
| 31B | n/a | 30.7B total |

The `E` means **effective**, not expert or efficient. Google’s [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) says E2B/E4B use **Per-Layer Embeddings (PLE)**, which makes the effective parameter count smaller than the total. Google’s [Gemma 3n overview](https://ai.google.dev/gemma/docs/gemma-3n) explains the same mechanism in more detail: PLE caching and parameter skipping let an `E2B` model contain over 5B parameters while operating with an effective footprint under 2B.

So the “8B mismatch” is not a mismatch at all. Ollama is reporting the **total** parameter count of the E4B model, while the `E4B` name refers to its **effective** parameter footprint.

### Size Analysis
Naive dense-model Q4_K_M math at 4.5-5 bits/parameter gives:

| Variant | Total params | Naive Q4_K_M estimate | Official package evidence |
|---|---:|---:|---|
| E2B | 5.1B | ~2.9-3.2GB | Ollama `e2b` is [7.2GB](https://ollama.com/library/gemma4:e2b); official BF16 weights are [10.2GB](https://huggingface.co/google/gemma-4-E2B/tree/main) |
| E4B | 8.0B | ~4.5-5.0GB | Ollama `latest/e4b` is [9.6GB](https://ollama.com/library/gemma4:e4b); official GGUF Q4_K_M is [5.34GB](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF) plus a [990MB mmproj file](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF/tree/main); official BF16 weights are [16GB](https://huggingface.co/google/gemma-4-E4B/tree/main) |
| 26B A4B | 25.2B | ~14.2-15.8GB | official GGUF Q4_K_M is [16.8GB](https://huggingface.co/ggml-org/gemma-4-26B-A4B-it-GGUF) |
| 31B | 30.7B | ~17.3-19.2GB | official GGUF Q4_K_M is [18.7GB](https://huggingface.co/ggml-org/gemma-4-31B-it-GGUF) |

Two conclusions follow:

- `9.6GB` is far too small for 26B/31B, so those are out.
- `9.6GB` is larger than a naive plain-text 8B Q4 estimate, so Ollama’s package size is clearly not just “4 bits times total params.”

Inference from the above: Ollama’s package likely includes multimodal components and/or keeps some tensors at higher precision. But the important empirical fact is that **Ollama itself publishes E4B as 9.6GB and E2B as 7.2GB**. So in Ollama’s packaging, `9.6GB` points to E4B, not E2B.

### Definitive Identification
`gemma4:latest` in Ollama is **Google Gemma 4 E4B**.

More precisely: it is Ollama’s **Q4_K_M-packaged Gemma 4 E4B**, which Google describes as **4.5B effective parameters and 8.0B total parameters with embeddings**, with **128K context** and **text/image/audio** support.

Confidence: **essentially certain**. The strongest reason is that [`gemma4:latest`](https://ollama.com/library/gemma4:latest) and [`gemma4:e4b`](https://ollama.com/library/gemma4:e4b) are the **same Ollama artifact** by digest, size, parameter count, and quantization.

If you need a paper-ready description, I would write:

“`Ollama gemma4:latest` corresponds to Google’s Gemma 4 E4B variant (4.5B effective parameters; 8.0B total parameters with embeddings), distributed by Ollama in Q4_K_M quantized form.”

### Remaining Uncertainties
- Ollama’s public page definitively identifies the variant as `E4B`, but it does not explicitly name the upstream Hugging Face repo slug such as `google/gemma-4-E4B-it`. So I can identify the **model family variant** with high confidence, but not prove the exact upstream checkpoint suffix from Ollama’s public metadata alone.
- Ollama’s `9.6GB` package is larger than a naive 8B Q4 estimate and larger than the public ggml-org E4B Q4 GGUF alone. The most likely explanation is bundled multimodal assets and/or mixed precision for some tensors, but Ollama does not publicly break down that package composition.
- Ollama’s library index summarizes the tag as “Text, Image,” while the detailed tag page, your local `ollama show`, and Google’s model card indicate audio support for E4B. That looks like a library-page summary omission, not a different model.
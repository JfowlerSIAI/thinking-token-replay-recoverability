### Evidence Summary
- **Ollama tag mapping is explicit:** on Ollama’s `gemma4` tags page, `gemma4:e4b` is marked `latest`, and `gemma4:latest` and `gemma4:e4b` share the **same digest** (`c6eb396dbd59`) and size (**9.6GB**) as of **April 7, 2026**.  
  Source: https://ollama.com/library/gemma4/tags
- **Ollama per-tag metadata matches your local output:** `gemma4:latest` shows `parameters 8B`, `Q4_K_M`, `9.6GB`.  
  Source: https://ollama.com/library/gemma4:latest
- **Google’s official Gemma 4 docs confirm the “E” meaning and memory table:** E2B/E4B are “effective” models, and the inference memory table is E2B `9.6/4.6/3.2`, E4B `15/7.5/5`, 31B `58.3/30.4/17.4`, 26B A4B `48/25/15.6` (BF16/SFP8/Q4_0).  
  Source: https://ai.google.dev/gemma/docs/core
- **Google official model card (Google org on HF) gives exact total/effective counts:**  
  E2B = `2.3B effective (5.1B with embeddings)`  
  E4B = `4.5B effective (8B with embeddings)`  
  26B A4B = `25.2B total, 3.8B active`  
  31B = `30.7B`.  
  Source: https://huggingface.co/google/gemma-4-E2B-it
- **Hidden size / context disambiguation from configs:**  
  E2B config `hidden_size: 1536`, `max_position_embeddings: 131072`  
  E4B config `hidden_size: 2560`, `max_position_embeddings: 131072`  
  26B config `hidden_size: 2816`, `max_position_embeddings: 262144`  
  31B config `hidden_size: 5376`, `max_position_embeddings: 262144`.  
  Sources:  
  https://huggingface.co/google/gemma-4-E2B-it/blob/main/config.json  
  https://huggingface.co/google/gemma-4-E4B-it/blob/main/config.json  
  https://huggingface.co/google/gemma-4-26B-A4B-it/blob/main/config.json  
  https://huggingface.co/google/gemma-4-31B-it/blob/main/config.json

### Architecture Analysis
- The **“E” means Effective** (official Google wording).
- E-models use **Per-Layer Embeddings (PLE)**, so “effective” active compute is lower than total stored parameters.
- Therefore:
  - **E2B is not 2B total**; it is **5.1B total with embeddings**.
  - **E4B is not 4B total**; it is **8B total with embeddings**.
- This directly resolves your “8.0B in Ollama” mismatch: `8B` corresponds to **Gemma 4 E4B total-with-embeddings**, not a separate “Gemma 4 8B” SKU.

### Size Analysis
Using your Q4_K_M assumption (~4.5–5 bits/param) for rough checks:

- **E2B total 5.1B**  
  Expected quantized core size: `5.1B * (4.5..5)/8 ≈ 2.9..3.2 GB`  
  Google Q4_0 table: **3.2GB** (matches rough math).
- **E4B total 8B**  
  Expected quantized core size: `8B * (4.5..5)/8 ≈ 4.5..5.0 GB`  
  Google Q4_0 table: **5GB** (matches rough math).
- **26B A4B total 25.2B**  
  Expected: `~14.2..15.8 GB`; Google Q4_0: **15.6GB**.
- **31B total 30.7B**  
  Expected: `~17.3..19.2 GB`; Google Q4_0: **17.4GB**.

Why does Ollama `gemma4:latest` show **9.6GB** at Q4_K_M then?
- On Ollama, `gemma4:e4b-it-q4_K_M` is explicitly 9.6GB (same as `latest`).  
  Source: https://ollama.com/library/gemma4/tags
- Official GGUF E4B Q4_K_M core file is **5.34GB**, plus mmproj **990MB** (~6.33GB total), still below 9.6GB.  
  Source: https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF/tree/main
- **Inference:** Ollama’s packaged artifact likely includes additional multimodal components and/or higher-precision tensors not reflected by simple “all-weights-at-4-bit” math. This is consistent with your local `audio` capability and Google’s note that E-model memory can exceed what “effective params” suggests.

### Definitive Identification
`gemma4:latest` in Ollama is **Gemma 4 E4B (instruction-tuned), Q4_K_M**, i.e. the same artifact as `gemma4:e4b` / `gemma4:e4b-it-q4_K_M`.

**Confidence: Very high (≈99%).**

Why:
1. `latest` and `e4b` are explicitly linked in Ollama tags.
2. Same digest and size.
3. `8B` total matches Google’s E4B total-with-embeddings.
4. `embedding_length=2560` uniquely matches E4B hidden size.
5. `context_length=131072` matches E2B/E4B tier; combined with 8B points to E4B.
6. Audio capability is only on E2B/E4B per Google docs; again consistent with E4B.

### Remaining Uncertainties
- The **exact internal tensor composition** of Ollama’s 9.6GB package (which tensors are quantized vs kept higher precision) is not fully itemized publicly on the model page; the size explanation above includes one inference step.
- Ollama’s tags table lists input as “Text, Image” while model docs/local `ollama show` indicate audio capability for E2B/E4B. That appears to be a listing/UI simplification rather than a true capability contradiction.
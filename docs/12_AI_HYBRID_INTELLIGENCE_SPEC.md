# ShiVi: AI and Hybrid-Intelligence Architecture

## 1. Operating Boundary & Invariants
- **Advisory Role Exclusivity:** AI models are treated as **advisory accelerators**, not autonomous authorities. **AI is strictly prohibited from mutating protected state, dispatching critical rescue tasks, or auto-resolving life-safety conflicts.**
- **Deterministic Heuristic Fallback:** If any AI service (Whisper, LLM entity extractor, embedding model) experiences latency $> 3\text{ seconds}$, rate limiting, or schema parsing failure, the system falls back immediately to structured form inputs and deterministic heuristic scoring.

```
[Citizen Free-Text / Audio Note]
               │
               ▼
       [AI Gateway Router]
       ├── Language Detection & Whisper Voice Transcription
       ├── Structured Pydantic Extraction (Category, People, Severity)
       ├── Duplicate Similarity Vector Embedding
       └── SOP Protocol Retrieval (RAG from Official NDMA Manuals)
               │
       [Validation Check]
       ├── Valid Structured Output ──> Pre-populates Draft (Requires Human Review)
       └── Timeout / Invalid Schema ─> Fallback to Raw Audio + Standard Form
```

---

## 2. Model Portfolio & Deployment Strategy

| Capability | Model Candidate | Target Host | Failure Fallback |
| :--- | :--- | :--- | :--- |
| **Multilingual Voice Transcription** | Whisper-Small / IndicWhisper | Server AI Worker (Async) | Preserve raw audio recording in outbox for manual dispatcher listening. |
| **Structured Entity Extraction** | Mistral-7B-Instruct / Phi-3 / Gemini Flash | Cloud API / Local Container | Fallback to structured multi-choice form. |
| **Duplicate Clustering** | `all-MiniLM-L6-v2` embeddings | Python in-memory / pgvector | Exact spatial proximity match ($\le 100\text{m}$ radius). |
| **SOP Grounding (RAG)** | Pre-indexed NDMA/SDRF standard operating manuals | Local SQLite vector table | Display default high-level disaster response checklist. |

---

## 3. Provenance & Operational Audit Logging
Every AI inference event logs:
- `model_id` and `model_version`.
- `prompt_template_version`.
- Raw prompt and response tokens.
- Latency in milliseconds.
- Human user acceptance, correction, or rejection status.

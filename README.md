# ZentroMart VoiceOps 2026
Made by **Aditya Singhal** · GitHub: **ADI238IND**

A simple Python support agent with section-based RAG, conversation state, verified mock order lookup, human tickets, and Gnani-only speech.

**Current status:** source implementation and 16 local tests completed. Real LLM/Gnani calls, Step 1 vs Step 2 answer scores, microphone UI verification and the personal spoken demo are pending API credentials. This project kit is **not yet a complete competition submission**. No fabricated scores or demo are included. See `SUBMIT.md`.

**Repository:** https://github.com/ADI238IND/zentromart-voiceops-2026 - public repository.

## 1. Install (Windows PowerShell)
Open PowerShell in this extracted project folder. Install Python 3.11 or 3.12 first.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe setup_dataset.py "C:\path\Capstone_Project_Dataset_FTTT_2026 (1).zip"
Copy-Item .env.example .env
notepad .env
```

Fill `GNANI_API_KEY` from your own Gnani account and `LLM_API_KEY` from your chosen text-model provider. The default configuration expects an OpenAI-compatible chat API supporting tool calls and JSON mode, plus an embeddings endpoint. The default base URL is `https://api.openai.com/v1`. Use `EMBEDDING_BACKEND=api` for the main run. To use a provider without embeddings, `tfidf` works offline but retrieves multilingual paraphrases less well. Save `.env` locally; do not share it. No API key is bundled.

On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows Python path. Run all commands from the project root. An existing external dataset is also supported by setting `DATASET_DIR` to its absolute path in `.env`.

## 2. Talk to the agent

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The browser interface supports typed chat, microphone recording, playback and source inspection. Grant microphone access locally when you want to record. Click **Send recorded turn** once per recorded message; click **New conversation** between callers. Each clip must be at most 60 seconds. Use only your own voice and synthetic scenarios. Text entry does not need the Gnani key; voice does. In Hindi/Hinglish, select the intended input/output language. Unsupported voice/model combinations may require a different voice from Gnani's catalog.

## 3. Organizer batch command

```powershell
.\.venv\Scripts\python.exe run.py --input recordings --output outputs
```

Put clips for one conversation in `recordings/` as `turn01.wav`, `turn02.wav`, etc. Natural filename order is used. For multiple callers, use immediate subfolders (`recordings/caller01/`, `recordings/caller02/`); each folder gets independent state. Root clips also form their own session. Use `--independent` when every clip is a separate question. Do not mix unrelated callers within one folder. Supported extensions: WAV, MP3, FLAC, OGG and M4A (provider decoding applies); WAV duration is checked locally. Other formats must also be <=60 seconds; convert to PCM WAV if decoding fails.

Each successful turn creates `*.txt` (reply), `*.wav` (Gnani speech) and `*.json` (decision, redacted transcript, actual evidence IDs, source text and metadata, retrieved sources, tool events). `manifest.json` lists success/failure for all files. Processing continues after a failed turn; exit code 1 means at least one failure, 2 means configuration failure. Failed calls are reported, never represented as successful speech. Re-run failed sessions from their first turn to restore context. Do not reuse an output directory for a changed input set.

Language options: `--stt-language hi-IN --tts-language hi-IN`. API failures cannot produce speech until Gnani is reachable; no alternative speech service is used.

## 4. Tests and evaluation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluate.py --offline-retrieval
.\.venv\Scripts\python.exe evaluate.py
.\.venv\Scripts\python.exe make_report.py
```

The first evaluation is an offline TF-IDF diagnostic only. The live run calls the same LLM on all 52 questions in Step 1 (prompt only) and Step 2 (RAG), then processes all 96 turns in 23 conversations with reset state between callers. `--asr --output asr_results` evaluates the supplied ASR-like text separately. The practice labels are used only by the evaluator, never read by the agent. See `sample_outputs/live_scores.json` after a complete live run. API calls consume your account quota.

Metrics are decision agreement, literal fact checks, forbidden-phrase checks, citation recall and conversation tool-name sequence agreement. Literal matching is a diagnostic, not semantic accuracy: native-script numbers, date formats, paraphrases and negations need manual review. It does not verify all tool arguments. Do not submit these as organizer scores. Preserve raw generated outputs; never type or edit test answers by hand.

## Design and rules

- `src/llm.py`: small text-only OpenAI-compatible client; any compatible hosted/local model can be configured.
- `src/retrieval.py`: section chunks, catalog rows, normalized embedding matrix and cosine retrieval; cached dense embeddings by content/model/base-URL hash. Offline TF-IDF backend is optional.
- `src/agent.py`: shared LLM/RAG/tool loop, conversation history, citation IDs, source tracking and precedence prompt. Retrieved text is treated as data.
- `src/tool_layer.py`: imports the supplied `lookup_order` and `create_ticket` unchanged, gates order data, enforces two failed proof attempts per order per session and deduplicates handover tickets. Proof is handled locally and redacted from model history.
- `src/business.py`: Monday-Saturday calendar excluding supplied holidays, calendar-day deadlines, coupon allocation and INR half-up rounding.
- `src/voice.py`: official Gnani SDK for both speech services, with explicit `timbre-v2.5`; no browser/OS speech or fallback provider.
- Dataset "today" is **20 October 2026**. Current policy overrides help/FAQ/marketing. Superseded returns are retained as reference solely for successor-approved historical cases.
- Tools do not cancel orders, issue refunds, book pickups or perform a real agent transfer. Tickets are mock records; claims must reflect their actual result. Verification is an educational simulation, not production authentication.

## GitHub publishing

The public repository contains this implementation, tests, report and submission instructions. Follow `docs/GITHUB.md` for updates, or run `publish_github.ps1` with Git installed and authenticated. It publishes an explicit source-file allowlist and never changes repository visibility.

## Finish and package

Follow `SUBMIT.md`, add your real <=2-minute `demo.mp4`, run live evaluation, update this README with the actual repository URL, regenerate the <=4-page report, copy genuine successful audio outputs into `sample_outputs/audio/`, then run:

```powershell
.\.venv\Scripts\python.exe package_submission.py --team AdityaSinghal
```

The packager refuses missing live scores, demo, repository URL or successful audio samples. It excludes dataset copies, environment secrets, recordings, caches and virtual environments. Review the resulting ZIP before submitting. `docs/DEMO.md` is a recording plan, not a completed demo.

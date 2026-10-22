# Exactly what to submit

The brief requires a **public Git repository** and a ZIP named `AdityaSinghal_voiceops.zip` (replace AdityaSinghal with your registered team name if needed). The brief does not specify a portal or deadline; use the organizers' actual submission announcement.

## Required final ZIP contents

| Item | Requirement | Current kit |
|---|---|---|
| README.md | Public repository URL, setup and exact batch command | Included; public repository created |
| .env.example | Configuration template, no secrets | Included |
| requirements.txt, run.py, src/ | Reproducible batch audio agent | Included; local tests pass |
| report.pdf | Maximum 4 pages, including actual Step 1 vs Step 2 scores | Four-page draft; live score section pending |
| demo.mp4 | Maximum 2 minutes; actual spoken Q&A, follow-up and handover/unknown | Must record with your own voice and Gnani |
| sample_outputs/ | Genuine generated text, audio and retrieved chunks | Offline diagnostics included; live audio samples pending |

## Finish in this order

1. Install with README instructions; import the supplied dataset locally. Do not include it in the submission ZIP or GitHub.
2. Add your own LLM and Gnani keys to local `.env`. Never paste keys into README or GitHub.
3. Run `python -m unittest discover -s tests -v` and `python evaluate.py`. Save real Step 1/2 outputs and conversation results. Manually inspect failures, dates, citations and Hindi/Hinglish replies.
4. Launch `python -m streamlit run app.py`. Record your own synthetic customer turns. Confirm actual Gnani transcription, answer, audio playback, follow-up memory and successful handover ticket. Record the screen with system audio and microphone; save <=120 seconds as `demo.mp4`. Do not edit agent answers or substitute narrated text for a working demo.
5. Run `python run.py --input recordings --output outputs` on the recordings. Make sure every test file reports `ok`. Copy the successful batch folder into `sample_outputs/audio/`. Include its `.txt`, `.wav`, `.json` and manifest files together. Review for verification-secret redaction.
6. The public repository is https://github.com/ADI238IND/zentromart-voiceops-2026. Its URL is already in REPOSITORY_URL.txt and README. Keep the repository updated with your final tested code and genuine results. Commit no dataset, keys, virtual environment or personal recordings.
7. Run `python make_report.py` to insert measured scores into the four-page report. Read the report and state real failure observations; `report_notes.json` can record your live findings. Do not hide unsuccessful results.
8. Run `python package_submission.py --team AdityaSinghal`. It produces `AdityaSinghal_voiceops.zip` only after required artifacts exist. Inspect it, then upload that ZIP and public repo URL wherever organizers instruct.

The delivered project kit is an implementation and finishing guide. It is not a substitute for the final real voice demo or measured evaluation. No final competition-ready claim is made until those steps pass.

# Submission contents

Submit `AdityaSinghal_voiceops.zip` to the Unstop capstone submission form. The public repository is https://github.com/ADI238IND/zentromart-voiceops-2026.

The ZIP contains the runner, source code, requirements, README, key-free `.env.example`, a report of at most four pages, the narrated `demo.mp4`, and actual generated text/audio/source records under `sample_outputs/`.

The demo uses clearly disclosed Gnani-generated customer and assistant voices. The measured evaluation is a deterministic sample: the first 12 practice questions compared prompt-only versus RAG, plus the first two practice conversations. Full evaluation remains available through `python evaluate.py`; sample metrics are not organizer scores or a claim about all unseen questions.

Do not add `.env`, API keys, virtual environments, the original dataset or private recordings to the ZIP. Each evaluator uses their own API accounts and supplies the original dataset locally.

Exact batch command after setup: `python run.py --input recordings --output outputs`. See README for Windows PowerShell setup and the expected output files.

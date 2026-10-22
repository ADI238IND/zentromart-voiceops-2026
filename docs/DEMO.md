# Record your real demo (maximum 2 minutes)

Use your own voice, the Streamlit microphone UI, and actual Gnani playback. Record the screen with microphone plus system audio (for example, Windows Snipping Tool screen recording or your usual recorder). Do not use generated narration in place of a working conversation. Never use any non-Gnani STT/TTS service.

Suggested sequence; these are customer prompts only. Let the running agent generate all replies.

- 0:00-0:10: show the application title and say that this is ZentroMart support, made by Aditya Singhal.
- 0:10-0:40: ask, "What is the electronics return window?" Play the agent's speech and briefly show the retrieved current policy section.
- 0:40-1:00: ask the follow-up, "What if it was delivered before August first, 2026?" Play the reply and show evidence. The question tests the successor policy's retained old-window exception.
- 1:00-1:30: say, "I would like to speak to a human agent." Let the tool run, then play the spoken reply. Show `create_ticket` with `created: true` and a ticket ID. Do not claim a real human has joined; this is a mock handover.
- 1:30-1:50: optionally ask an uncovered company question such as "Do you sell insurance for my dog?" Let the agent handle missing documentation honestly.
- End before 2:00. Save as `demo.mp4` in the project root.

If you want to demonstrate verification instead, choose a synthetic practice order and read the corresponding mock customer's proof from your private local dataset, never real customer details. Do not show verification values or API keys in the recording. Keep each customer clip under 60 seconds.

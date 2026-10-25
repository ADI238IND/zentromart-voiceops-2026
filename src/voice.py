"""Only Gnani handles STT and TTS. No fallback speech providers."""
import os
import re
import wave
from pathlib import Path
from .config import load_env

class Voice:
    def __init__(self):
        load_env()
        if not os.getenv('GNANI_API_KEY'):
            raise RuntimeError('Missing GNANI_API_KEY. Use your own Gnani account.')
        from gnani.stt import GnaniSTTClient
        from gnani.tts import GnaniTTSClient
        self.stt = GnaniSTTClient()
        self.tts = GnaniTTSClient()

    def transcribe(self, path, language='en-IN'):
        if Path(path).suffix.lower()=='.wav':
            with wave.open(str(path),'rb') as f:
                if f.getnframes()/f.getframerate()>60:
                    raise ValueError('Each customer turn must be at most 60 seconds.')
        result = self.stt.transcribe(str(path), language_code=language)
        return (result.get('transcript') or '').strip()

    def synthesize(self, text, path, language='en-IN'):
        # Speak long order numbers in groups, without changing saved text answers.
        spoken = re.sub(r'\b(\d{4})(\d{4})\b',r'\1 \2', text)
        self.tts.synthesize(spoken, voice=os.getenv('GNANI_VOICE','Kaveri'),
            model=os.getenv('GNANI_TTS_MODEL','timbre-v2.5'),language=language, output_file=str(path))
        if not Path(path).exists() or not Path(path).stat().st_size:
            raise RuntimeError('Gnani did not create an audio reply.')
        # Gnani can return a streaming WAV with placeholder frame counts.
        # Rewrite its PCM frames so duration checks and players see real length.
        normalized = Path(path).with_suffix('.normalized.wav')
        try:
            with wave.open(str(path), 'rb') as source, wave.open(str(normalized), 'wb') as target:
                target.setparams(source.getparams()._replace(nframes=0))
                while True:
                    frames = source.readframes(65536)
                    if not frames:
                        break
                    target.writeframes(frames)
            normalized.replace(path)
        finally:
            normalized.unlink(missing_ok=True)

    def turn(self, audio, agent, output, stt_language='en-IN', tts_language='en-IN'):
        transcript = self.transcribe(audio,stt_language)
        result = agent.respond(transcript)
        self.synthesize(result['answer'],output,tts_language)
        # Identity digits are not persisted in transcript files.
        safe = re.sub(r'(?<!\d)\d{4,6}(?!\d)', '[verification value redacted]', transcript)
        if '[secret withheld' in str(agent.history[-2:]) or 'secret withheld' in str(agent.history[-2:]):
            safe = '[Identity verification input redacted]'
        return dict(result, transcript=safe, audio_file=Path(output).name)

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from src.voice import Voice
import run

class StubVoice:
    def turn(self,audio,agent,output,*languages):
        if 'bad' in audio.name:
            raise RuntimeError('secret must never be logged')
        output.write_bytes(b'test fixture, not speech')
        return {'answer':'Fixture reply','evidence':[],'sources':[],'audio_file':output.name}

class VoiceBatchTests(unittest.TestCase):
    def test_explicit_gnani_model_and_output_check(self):
        v = Voice.__new__(Voice)
        class TTS:
            def synthesize(self,text,**kwargs):
                self.text,self.kwargs = text,kwargs
                import wave
                with wave.open(kwargs['output_file'], 'wb') as output:
                    output.setnchannels(1)
                    output.setsampwidth(2)
                    output.setframerate(16000)
                    output.writeframes(b'\x00\x00' * 1600)
                # Simulate the streaming placeholder header returned by Gnani.
                payload = bytearray(Path(kwargs['output_file']).read_bytes())
                payload[40:44] = (4294967294).to_bytes(4, 'little')
                Path(kwargs['output_file']).write_bytes(payload)
        v.tts = TTS()
        with tempfile.TemporaryDirectory() as temp:
            v.synthesize('Order 12345678',Path(temp)/'reply.wav')
            self.assertEqual(v.tts.kwargs['model'],'timbre-v2.5')
            self.assertIn('1234 5678',v.tts.text)
            import wave
            with wave.open(str(Path(temp)/'reply.wav')) as reply:
                self.assertEqual(reply.getnframes(),1600)

    def test_batch_continues_after_failure_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inp,out = root/'in',root/'out'
            inp.mkdir()
            for name in ('1.wav','2_bad.wav','3.wav'):
                (inp/name).touch()
            with patch.object(sys,'argv',['run.py','--input',str(inp),'--output',str(out)]), patch.object(run,'API',return_value=object()), patch.object(run,'Voice',return_value=StubVoice()), patch.object(run,'Index',return_value=object()):
                code = run.main()
            self.assertEqual(code,1)
            manifest = json.loads((out/'manifest.json').read_text())
            self.assertEqual([r['status'] for r in manifest],['ok','error','ok'])
            self.assertEqual(len(list(out.rglob('*.txt'))),2)
            self.assertEqual(len(list(out.rglob('*.wav'))),2)
            self.assertNotIn('secret must never be logged',(out/'manifest.json').read_text())

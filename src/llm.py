"""OpenAI-compatible chat and embedding APIs. No audio is sent here."""
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .config import load_env

class API:
    def __init__(self):
        load_env()
        self.key = os.environ.get('LLM_API_KEY', '')
        self.base = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
        self.model = os.environ.get('LLM_MODEL', 'gpt-4.1-mini')
        if not self.key:
            raise RuntimeError('Missing LLM_API_KEY. Set it in .env; never commit that file.')

    def post(self, route, payload):
        req = Request(self.base + route, data=json.dumps(payload).encode(), headers={
            'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        for attempt in range(6):
            try:
                with urlopen(req, timeout=30) as response:
                    return json.load(response)
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 5:
                    raise RuntimeError(f'LLM API returned HTTP {exc.code}; check configuration/quota.') from None
            except (URLError, TimeoutError):
                if attempt == 5:
                    raise RuntimeError('LLM API connection failed; retry after checking network.') from None
            time.sleep(min(30, max(15, 2 ** attempt)))

    def chat(self, messages, tools=None, json_mode=False):
        payload = {'model': self.model, 'messages': messages, 'temperature': 0}
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'
        if json_mode:
            payload['response_format'] = {'type': 'json_schema', 'json_schema': {'name':'support_reply','strict':True,'schema':{'type':'object','properties':{'answer':{'type':'string'},'decision':{'type':'string','enum':['answer','clarify','refuse','escalate']},'evidence':{'type':'array','items':{'type':'string'}},'intent':{'type':'string'}},'required':['answer','decision','evidence','intent'],'additionalProperties':False}}}
        return self.post('/chat/completions', payload)['choices'][0]['message']

    def embed(self, texts):
        data = self.post('/embeddings', {'model': os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small'), 'input': texts})['data']
        return [r['embedding'] for r in sorted(data, key=lambda r: r['index'])]

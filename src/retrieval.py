"""Section-preserving vector retrieval with metadata and authoritative neighbors."""
import csv
import hashlib
import json
import os
import re
from pathlib import Path
import numpy as np

PRIORITY = {'policy': 0, 'agent_guide': 1, 'meta': 1, 'help': 2, 'faq': 3, 'marketing': 4, 'catalog': 0}

class Index:
    def __init__(self, dataset, api=None, backend=None):
        self.dataset = Path(dataset)
        self.backend = backend or os.getenv('EMBEDDING_BACKEND', 'api')
        self.api = api
        self.chunks = []
        for file in sorted((self.dataset / 'kb').glob('*.md')):
            text = file.read_text(encoding='utf-8')
            header = text.split('---', 2)[1]
            meta = dict(re.findall(r'^(\w+):\s*(.*)$', header, re.M))
            parts = re.split(r'^## \[([^\]]+)\]\s*(.*)$', text, flags=re.M)
            for i in range(1, len(parts), 3):
                self.chunks.append({'id': parts[i], 'title': parts[i+1], 'text': parts[i+2].strip(),
                    'file': file.name, **{k: meta.get(k, '') for k in ('doc_id', 'doc_type', 'status', 'effective_from', 'version')}})
        with open(self.dataset / 'data/products.csv', encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                self.chunks.append({'id': 'products.csv:' + row['sku'], 'title': row['title'],
                    'text': json.dumps(row, ensure_ascii=False), 'file': 'products.csv', 'doc_type': 'catalog',
                    'status': 'current', 'effective_from': '', 'version': ''})
        texts = [f"{c['id']} {c['title']} {c['text']}" for c in self.chunks]
        if self.backend == 'tfidf':
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            self.vectors = self.vectorizer.fit_transform(texts).toarray()
        elif self.backend == 'api':
            if api is None:
                raise RuntimeError('API embeddings require an LLM API client.')
            model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
            digest = hashlib.sha256(json.dumps([texts, api.base, model]).encode()).hexdigest()
            cache = Path(os.getenv('CACHE_DIR', '.cache'))
            cache.mkdir(parents=True, exist_ok=True)
            path = cache / (digest + '.json')
            if path.exists():
                self.vectors = np.asarray(json.loads(path.read_text()), dtype=float)
            else:
                vectors = []
                for i in range(0, len(texts), 64):
                    vectors.extend(api.embed(texts[i:i+64]))
                self.vectors = np.asarray(vectors, dtype=float)
                path.write_text(json.dumps(vectors))
        else:
            raise ValueError('EMBEDDING_BACKEND must be api or tfidf')
        self.vectors /= np.maximum(np.linalg.norm(self.vectors, axis=1, keepdims=True), 1e-12)

    def search(self, query, k=10):
        if self.backend == 'tfidf':
            q = self.vectorizer.transform([query]).toarray()[0]
        else:
            q = np.asarray(self.api.embed([query])[0], dtype=float)
        q /= max(float(np.linalg.norm(q)), 1e-12)
        scores = self.vectors @ q
        top = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)[:k]
        # An FAQ/marketing hit must bring the current policy on the same subject.
        topics = {'RET': 'return', 'REF': 'refund', 'CAN': 'cancel', 'DEL': 'deliver', 'DMG': 'damage', 'MKT': 'plus'}
        wanted = set()
        for i in top[:4]:
            c = self.chunks[i]
            if c['doc_type'] in ('faq', 'marketing', 'help'):
                for prefix, word in topics.items():
                    if word in (c['title'] + ' ' + query).lower():
                        wanted.add(prefix)
        extras = [i for i,c in enumerate(self.chunks) if c['status']=='current' and c['doc_type']=='policy' and c['id'].split('-')[0] in wanted]
        selected = list(dict.fromkeys(top + extras))
        return [dict(self.chunks[i], score=round(float(scores[i]), 5)) for i in sorted(selected,
            key=lambda i: (self.chunks[i]['status'] != 'current', PRIORITY.get(self.chunks[i]['doc_type'],9), -float(scores[i])))]

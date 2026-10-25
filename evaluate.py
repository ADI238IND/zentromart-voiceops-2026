"""Measured practice evaluation. Labels are scoring-only, never agent input."""
import argparse
import csv
import json
import re
from pathlib import Path
from src.config import dataset_path
from src.retrieval import Index
from src.llm import API
from src.agent import Agent

def rows(path):
    with open(path,encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def evidence_ids(value):
    return {x.strip() for x in value.split(';') if x.strip()}

def normalize(text):
    return re.sub(r'\s+',' ',text.casefold())

def facts(text, spec):
    # Transparent smoke metric only: does not replace semantic/native-language review.
    if not spec.strip():
        return True
    return all(any(normalize(a.strip()) in normalize(text) for a in fact.split(' / ')) for fact in spec.split(' ; '))

def score(row,result):
    allowed = {v.strip() for v in (row.get('acceptable_decisions') or row['expected_decision']).replace(' ; ', ';').split(';')}
    gold = evidence_ids(row['gold_evidence'])
    cited = set(result['evidence'])
    forbidden = [x.strip() for x in row['must_not_include'].split(' ; ') if x.strip()]
    return {'decision_match':result['decision'] in allowed,
        'literal_fact_pass':facts(result['answer'],row['must_include']),
        'literal_forbidden_pass':not any(normalize(x) in normalize(result['answer']) for x in forbidden),
        'citation_recall':len(gold & cited)/len(gold) if gold else None}

def means(records):
    out = {'count':len(records)}
    for key in ('decision_match','literal_fact_pass','literal_forbidden_pass','citation_recall'):
        vals = [r['score'][key] for r in records if r['score'][key] is not None]
        out[key] = sum(vals)/len(vals) if vals else None
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--offline-retrieval',action='store_true',help='No LLM calls; TF-IDF diagnostic only, NOT Step 1/2 answer scores.')
    p.add_argument('--limit',type=int,default=0,help='Evaluate the first N questions; zero means all.')
    p.add_argument('--conversation-limit',type=int,default=0,help='Evaluate the first N conversations; zero means all.')
    p.add_argument('--asr',action='store_true',help='Use asr_text instead of typed questions')
    p.add_argument('--output',type=Path,default=Path('sample_outputs'))
    a = p.parse_args()
    data = dataset_path()
    a.output.mkdir(parents=True,exist_ok=True)
    questions = rows(data/'practice/questions.csv')
    if a.limit:
        questions = questions[:a.limit]
    if a.offline_retrieval:
        index = Index(data,backend='tfidf')
        records = []
        for q in questions:
            found = index.search(q['asr_text'] if a.asr else q['question'])
            gold = evidence_ids(q['gold_evidence'])
            ids = {c['id'] for c in found}
            records.append({'id':q['id'],'gold':sorted(gold),'retrieved':[c['id'] for c in found],
                'recall':len(gold & ids)/len(gold) if gold else None})
        recalls = [r['recall'] for r in records if r['recall'] is not None]
        summary = {'mode':'offline TF-IDF retrieval diagnostic; no generated answers', 'question_count':len(questions),
            'questions_with_gold':len(recalls),'mean_evidence_recall':sum(recalls)/len(recalls),'records':records}
        (a.output/'offline_retrieval.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
        return
    api = API()
    index = Index(data,api)
    summary = {'mode':'live LLM practice evaluation','question_count':len(questions),'scope_note':f'First {len(questions)} of 52 questions; conversation limit {a.conversation_limit or 23} of 23. Deterministic file order; no answer-based selection.','metrics_note':'Literal fact/forbidden checks are approximate; manually review semantic equivalence, dates, native language, and negation. Not organizer scores.'}
    for mode in ('step1','step2'):
        output = []
        path = a.output/(mode+'.jsonl')
        existing = {}
        if path.exists():
            for line in path.read_text(encoding='utf-8').splitlines():
                record = json.loads(line)
                existing[record['id']] = record
        with path.open('w',encoding='utf-8') as f:
            for q in questions:
                if q['id'] in existing:
                    record = existing[q['id']]
                else:
                    agent = Agent(data,index,api,baseline=mode=='step1')
                    result = agent.respond(q['asr_text'] if a.asr else q['question'])
                    record = {'id':q['id'],'result':result,'score':score(q,result)}
                output.append(record)
                f.write(json.dumps(record,ensure_ascii=False)+'\n')
                f.flush()
                print(mode,len(output),'/',len(questions),flush=True)
        summary[mode] = means(output)
    output = []
    agent = None
    current = None
    conversation_rows = sorted(rows(data/'practice/conversations.csv'),key=lambda r:(r['conversation_id'],int(r['turn'])))
    if a.conversation_limit:
        ids = list(dict.fromkeys(q['conversation_id'] for q in conversation_rows))[:a.conversation_limit]
        conversation_rows = [q for q in conversation_rows if q['conversation_id'] in ids]
    with (a.output/'conversations.jsonl').open('w',encoding='utf-8') as f:
        for q in conversation_rows:
            if q['conversation_id'] != current:
                agent = Agent(data,index,api)
                current = q['conversation_id']
            result = agent.respond(q['customer_message'])
            expected = re.findall(r'(lookup_order|create_ticket)\(',q['expected_tool_calls'])
            actual = [v['tool'] for v in result['tool_calls']]
            record = {'conversation_id':current,'turn':int(q['turn']),'result':result,
                'score':score(q,result),'expected_tool_names':expected,'actual_tool_names':actual,'tool_name_sequence_match':expected==actual}
            output.append(record)
            f.write(json.dumps(record,ensure_ascii=False)+'\n')
            f.flush()
            print('conversation',current,q['turn'],flush=True)
    summary['conversations'] = means(output)
    summary['conversations']['tool_name_sequence_match'] = sum(r['tool_name_sequence_match'] for r in output)/len(output)
    (a.output/'live_scores.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()

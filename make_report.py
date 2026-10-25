"""Build a concise three-page report from measured results, without inventing scores."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
ROOT=Path(__file__).resolve().parent

def main():
    scores=json.loads((ROOT/'sample_outputs/live_scores.json').read_text())
    style=getSampleStyleSheet()
    style.add(ParagraphStyle(name='BodyClean',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=10,textColor=colors.HexColor('#24384b')))
    style['Title'].fontSize=26;style['Title'].leading=31;style['Title'].textColor=colors.HexColor('#102c47')
    story=[]
    def p(text,name='BodyClean'):story.append(Paragraph(text,style[name]))
    def h(text):p(text,'Heading2')
    def table(rows,widths):
        t=Table([[Paragraph(escape(str(c)),style['BodyClean']) for c in r] for r in rows],colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#cbd7df'))]));story.append(t)
    p('ZentroMart VoiceOps 2026','Title');p('Aditya Singhal | Capstone report | 25 October 2026')
    p('Repository: https://github.com/ADI238IND/zentromart-voiceops-2026')
    h('What I built')
    p('A simple support agent that answers from ZentroMart documents and keeps the context of a conversation. The same Python agent handles typed chat and audio clips. Gnani handles all speech-to-text and text-to-speech. Gemini generates the text replies. No other speech provider is used.')
    table([['Course step','Implementation'],['1. Prompting','A support role and limits, with a prompt-only baseline that receives no company documents.'],['2. RAG','Chunks preserve section IDs, version, status and effective date. TF-IDF vectors and cosine search retrieve policies and product rows. A dense embedding backend is also available, but was not used in the measured run.'],['3. Conversation','Session memory, verified mock order lookup, human ticket creation, date arithmetic and coupon-adjusted refund estimates.'],['4. Voice','Gnani input transcription, the shared agent, and Gnani Timbre v2.5 spoken replies. A Streamlit recorder and a folder-based runner are included.']],[105,390])
    h('Grounding and caller checks')
    p('Current policies outrank guides, help pages, FAQs and marketing. Superseded returns are reference material for the exception retained by the current policy. Historical support logs are not policy authority. The reference date is 20 October 2026. Business days are Monday to Saturday, excluding the supplied holidays; return windows use calendar days.')
    p('The application passes verification proof directly to the supplied mock lookup tool, outside the LLM. It permits one retry, does not reveal the expected proof, and clears active order state when the order changes. Handover requires a successful create_ticket result. The tools cannot execute a cancellation, issue a refund or connect a real phone call.')
    story.append(PageBreak());p('Measured practice results','Title')
    n=scores['step1']['count'];turns=scores['conversations']['count']
    p(f'This comparison uses the first {n} of 52 practice questions in dataset order, with the same questions for both modes. Conversation testing covers the first two of 23 conversations, containing {turns} customer turns. This scope was chosen before reviewing its scores after the broader run encountered provider rate limits. It is a sample, not a result for the complete practice set or unseen organizer tests.')
    def pct(v):return 'n/a' if v is None else f'{100*v:.1f}%'
    rows=[['Metric','Prompt-only','RAG']]
    for key,label in [('decision_match','Decision agreement'),('literal_fact_pass','Literal required-fact pass'),('literal_forbidden_pass','Forbidden-phrase check pass'),('citation_recall','Mean cited-evidence recall')]:
        rows.append([label,pct(scores['step1'][key]),pct(scores['step2'][key])])
    table(rows,[225,135,135]);story.append(Spacer(1,14))
    c=scores['conversations']
    p(f"Conversation decision agreement: {pct(c['decision_match'])}. Tool-name sequence agreement: {pct(c['tool_name_sequence_match'])}. Required-fact check pass: {pct(c['literal_fact_pass'])}.")
    p('Decision agreement compares the generated decision with the accepted label. Required facts and forbidden phrases use transparent string checks; these do not understand every paraphrase, date format, native-script number or negation. Citation recall checks overlap with gold evidence IDs. Tool-name sequence checks do not validate every argument. These are diagnostics, not semantic accuracy or official marks.')
    p('The evaluator alone reads practice labels. The runtime agent reads documents, the public product catalog and verified tool results. Generated answers are saved without hand editing. Check the raw JSONL files alongside these aggregate numbers.')
    h('Other checks')
    p('The supplied dataset validator passed. All 16 local tests pass in a fresh dependency environment. Checks cover verification gates and retry limits, session isolation, secret redaction, calendar arithmetic, coupon rounding, ticket failure, retrieval metadata and batch continuation after an error. The synthetic failed-file case in the test log is intentional.')
    p('Real Gnani calls completed all three demo turns: an electronics return question, a follow-up about delivery before August 2026, and a human handover. Saved traces include source IDs and a successful mock ticket result. The narrated video is under two minutes. Both customer and assistant voices are generated by Gnani and disclosed as synthetic on screen and in the narration.')
    story.append(PageBreak());p('What I learned and how to run it','Title')
    h('Issues found during live testing')
    p('The first selected Gemini model was retired. The measured run uses gemini-3.1-flash-lite through its OpenAI-compatible endpoint. Some plain text replies omitted the required result fields, so JSON Schema output and an explicit formatting repair were added. Repeated tool searches are bounded, with a final answer-only generation at the end of the budget.')
    p('Gnani returned a WAV stream with placeholder frame counts. The voice layer now rewrites the actual PCM frames into a normal WAV header, and a regression test reproduces that case. Provider 429 and 503 responses caused interrupted wider evaluation attempts. The client retries with a bounded backoff, and the evaluator reuses completed question records when resuming the same output directory.')
    h('Limits and next improvements')
    p('TF-IDF can miss multilingual paraphrases and short follow-ups. The offline diagnostic had 65.6% mean gold-evidence recall on the 47 questions with gold evidence; this is separate from generated-answer quality. A measured dense-embedding comparison is a useful next improvement. The complete 52-question and 23-conversation suite has not been completed in this submission.')
    p('Policy interpretation, language quality, escalation decisions and tool arguments can still be wrong. Prompt instructions reduce those risks but do not prove correctness. Verification is an educational simulation over fictional records, not production authentication. The video is a visual walkthrough of real saved API turns with synthetic narration, not a personal voice recording or a live telephone session.')
    h('Reproduce')
    p('Install requirements, import the organizer dataset locally, copy .env.example to .env and add your own Gnani and Gemini credentials. No credentials or dataset copy are included. Run python -m streamlit run app.py for the interface.')
    p('Batch audio: python run.py --input recordings --output outputs. Put one caller per folder and number clips in conversation order. Each successful turn writes text, Gnani audio, a decision, source chunks and tool events. Each customer clip must be at most 60 seconds.')
    p('Measured sample: python evaluate.py --limit 12 --conversation-limit 2. Full suite: python evaluate.py. After a new run, review raw outputs, run python make_report.py, then python package_submission.py --team AdityaSinghal.')
    p('Sources: supplied VoiceOps 2026 capstone brief, dataset README and DATA_DICTIONARY, current ZentroMart policy and agent-guide sections, and the official gnani-vachana SDK. Only the supplied fictional company data was used.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#65768a'));canvas.drawString(50,29,'ZentroMart VoiceOps | Aditya Singhal');canvas.drawRightString(545,29,f'{doc.page} / 3')
    SimpleDocTemplate(str(ROOT/'report.pdf'),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=45,bottomMargin=55).build(story,onFirstPage=footer,onLaterPages=footer)
    print('Wrote report.pdf from measured results.')
if __name__=='__main__':main()

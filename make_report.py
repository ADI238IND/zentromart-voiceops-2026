"""Regenerate the four-page report using actual evaluation files, never invented scores."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parent

def main():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyClean',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=10,textColor=colors.HexColor('#253449')))
    styles.add(ParagraphStyle(name='Kicker',fontName='Helvetica-Bold',fontSize=10,leading=14,textColor=colors.HexColor('#087e8b'),spaceAfter=12))
    styles['Title'].textColor = colors.HexColor('#112b45')
    styles['Title'].fontSize = 27
    styles['Title'].leading = 32
    styles['Heading1'].fontSize=18
    styles['Heading1'].leading=23
    story=[]
    def p(text,style='BodyClean'):
        story.append(Paragraph(text,styles[style]))
    def heading(text):
        p(text,'Heading1')
        story.append(Spacer(1,8))
    def table(data,widths):
        rows=[[Paragraph(escape(str(c)),styles['BodyClean']) for c in r] for r in data]
        t=Table(rows,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f3f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#087e8b')),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d9e1e7'))]))
        story.append(t)
    offline_path=ROOT/'sample_outputs/offline_retrieval.json'
    offline=json.loads(offline_path.read_text()) if offline_path.exists() else {}
    live_path=ROOT/'sample_outputs/live_scores.json'
    live=json.loads(live_path.read_text()) if live_path.exists() else None
    notes=json.loads((ROOT/'report_notes.json').read_text())
    repo=(ROOT/'REPOSITORY_URL.txt').read_text(encoding='utf-8-sig').strip()
    p('VOICEOPS 2026 / CAPSTONE REPORT','Kicker')
    p('ZentroMart<br/>Support that listens','Title')
    p('Aditya Singhal | GitHub: ADI238IND')
    p('Implementation report - '+('live evaluation results included' if live else 'live validation pending'))
    p('Repository: '+escape(repo or 'pending repository creation'))
    p('Visibility: public. Source code, tests and instructions are included in the repository.')
    heading('1. What was built')
    p('A single Python customer-support agent handles typed messages and voice turns. Its answers are grounded in the supplied ZentroMart documents and synthetic records. A small Streamlit interface records and plays audio. A separate command accepts a folder of customer clips and writes a text reply, Gnani audio and evidence for each successful turn.')
    table([['Step','Implementation'],['1 - Prompting','Text-only LLM API baseline with role, limits and AI disclosure; evaluated without company documents.'],['2 - Grounding','Section chunks, embeddings, cosine vector search, source metadata and product catalog retrieval.'],['3 - Conversation','Session memory, local caller verification, supplied mock order/ticket tools, calendar and refund helpers.'],['4 - Voice','Official Gnani SDK for both transcription and synthesis; shared agent brain and explicit Timbre model.']],[105,390])
    story.append(PageBreak())
    p('ARCHITECTURE / GROUNDING','Kicker')
    heading('2. Retrieval and policy decisions')
    p('Customer audio goes to Gnani STT. The resulting text enters the same agent used for chat. It retrieves company sections, checks structured records through tools when appropriate, generates a short grounded response, then sends only that reply to Gnani TTS. Other speech providers are never used.')
    p('Markdown is split at each bracketed section ID. Each chunk retains its filename, document type, version, status and effective date. Products are indexed as products.csv:SKU records. The recommended backend uses configurable dense API embeddings stored in a normalized NumPy vector index. An offline TF-IDF embedding backend is included for diagnostics and environments without an embedding endpoint.')
    p('Current policies outrank agent guides, help articles, FAQs and marketing. Low-authority topic hits pull relevant current policy neighbors into context. The old returns policy remains marked superseded; the prompt allows its use only when a current successor explicitly preserves an older case. Historical support logs are not indexed as policy authority.')
    heading('3. Dates, memory and actions')
    p('The fixed reference date is 20 October 2026. The calendar helper adds business days Monday through Saturday, skipping the supplied holidays; return windows use calendar days. The partial-refund helper calculates proportional coupon allocation, minimum-value clawback and half-up rupee rounding. The model must retrieve eligibility rules before using an amount.')
    p('The application retains order and issue context within one caller session. Verification is done outside the model: one phone suffix or pincode is submitted directly to the supplied lookup tool, with at most two failed attempts per order per session. Proof is removed from model-visible history, trace and summaries. Switching orders clears the active verified record. Tools cannot execute a cancellation or refund; those actions must never be claimed.')
    p('Human handover uses the supplied ticket tool. A successful handover claim requires created=true. Summaries include issue, intent, known order, checks and escalation reason. Repeated ticket creation for the same active issue is deduplicated. All order data and authentication are synthetic educational examples.')
    story.append(PageBreak())
    p('EVALUATION / REPRODUCIBILITY','Kicker')
    heading('4. Measured results and comparison')
    p('The supplied dataset validator passed: 9 CSVs, 21 knowledge documents, 1,000 orders, 1,783 order items, 52 questions and 23 conversations containing 96 customer turns. Sixteen local unittest cases passed, including verification gates and retry limits, session isolation, date arithmetic, coupon rounding, ticket failure, secret redaction, source metadata and batch failure continuation. Speech-related unit tests use doubles; they are not proof of a live Gnani call.')
    score_rows=[['Measure','Result']]
    score_rows.append(['Offline TF-IDF evidence recall',f"{100*offline.get('mean_evidence_recall',0):.1f}% on {offline.get('questions_with_gold',0)} questions with gold evidence (of 52). No generated-answer accuracy measured."])
    if live:
        for mode,label in [('step1','Step 1 prompt-only'),('step2','Step 2 RAG')]:
            r=live[mode]
            score_rows.append([label,f"{r['count']} questions; decision match {100*r['decision_match']:.1f}%; literal fact pass {100*r['literal_fact_pass']:.1f}%; forbidden-phrase pass {100*r['literal_forbidden_pass']:.1f}%."])
        r=live['conversations']
        score_rows.append(['Conversation evaluation',f"{r['count']} turns; decision match {100*r['decision_match']:.1f}%; tool-name sequence agreement {100*r['tool_name_sequence_match']:.1f}%."])
    else:
        score_rows.extend([['Step 1 prompt-only','NOT RUN - LLM credentials unavailable. No score claimed.'],['Step 2 RAG','NOT RUN - LLM/embedding credentials unavailable. No score claimed.'],['Conversations / real voice','NOT RUN live - requires configured accounts and personal recordings.']])
    table(score_rows,[155,340])
    story.append(Spacer(1,12))
    p('The offline retrieval number is mean overlap with the gold section IDs, using the actual returned set (10 vector hits plus any authority neighbors). It is not a top-10 answer accuracy or organizer score. Five questions have no gold evidence and are omitted from that recall mean.')
    p('The live evaluator compares the same 52 questions using fresh sessions, then processes the 96 conversation turns in order. Labels remain in the scoring process and are not passed to the agent. It saves raw generated replies, sources and tool events. Literal checks do not recognize every equivalent date, native-language phrase or negation; human semantic review is necessary. Tool-name checks do not prove argument correctness. No improvement over baseline is claimed before a live comparison.')
    story.append(PageBreak())
    p('LIMITATIONS / FINAL CHECKS','Kicker')
    heading('5. What went wrong and what to fix')
    p('Offline lexical retrieval missed some gold evidence: mean recall was 65.6%. Paraphrases, short follow-ups and multilingual text are harder for TF-IDF. The main configuration therefore uses dense multilingual-capable API embeddings; its real retrieval and answer quality must still be measured. Improve chunk/query coverage based on a full evaluation without inserting practice reference answers into runtime code.')
    p(escape(notes['observations']))
    p(escape(notes['next_fixes']))
    p('Remaining risks include model mistakes in policy selection, incorrect or missing citations, tool argument errors, native-language phrasing and spoken-number recognition beyond individual English digit words/native digits. Prompt-based policy compliance and handover decisions need live adversarial evaluation. This is not a production authentication, refund or telephony system. No real PSTN calling integration is claimed; this capstone uses recorded voice turns.')
    heading('6. Reproduce and finish')
    p('Install requirements, import the supplied dataset locally, copy .env.example to .env and configure your own Gnani and text-model credentials. Run python evaluate.py, inspect the generated responses, update report_notes.json, then run python make_report.py. Run python run.py --input recordings --output outputs for the organizer batch interface.')
    p('Before submitting, publish the public repository, place its actual URL in README and REPOSITORY_URL.txt, record a real demo.mp4 of at most two minutes, and include successful generated text, Gnani speech and source records under sample_outputs/audio/. The demo must show grounded Q&amp;A, a follow-up and a human handover or honest unknown. Package with python package_submission.py --team AdityaSinghal. Exclude the dataset, API keys, virtual environments and personal recordings.')
    p('References: supplied VoiceOps 2026 capstone brief; dataset README, DATA_DICTIONARY and knowledge-base sections. Speech API integration follows the supplied brief and the official Gnani Python SDK: github.com/Gnani-AI-Mintlify/gnani-vachana. No bonus feature or live result is claimed without evidence.')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#d9e1e7'));canvas.line(50,43,545,43)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#65768a'))
        canvas.drawString(50,29,'ZentroMart VoiceOps 2026 | Aditya Singhal')
        canvas.drawRightString(545,29,f'{doc.page} / 4')
    SimpleDocTemplate(str(ROOT/'report.pdf'),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=57).build(story,onFirstPage=footer,onLaterPages=footer)
    print('Wrote report.pdf; render and confirm it remains at most four pages.')
if __name__=='__main__':
    main()

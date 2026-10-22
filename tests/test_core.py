import json
import os
from pathlib import Path
import tempfile
import unittest
from src.config import dataset_path
from src.tool_layer import Tools, normalize_numbers, numeric_groups
from src.business import Calendar, money, partial_refund
from src.retrieval import Index
from src.agent import Agent
from run import audio_files

DATA = dataset_path()

class FakeAPI:
    def __init__(self):
        self.messages = []
    def chat(self,messages,**kwargs):
        self.messages.append(messages)
        return {'role':'assistant','content':json.dumps({'answer':'How can I help with this order?','decision':'clarify','evidence':['RET-2'],'intent':'support'})}

class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = Index(DATA,backend='tfidf')

    def test_unverified_lookup_never_discloses(self):
        tools = Tools(DATA)
        oid = next(iter(tools.raw._ORDERS))
        result = tools.lookup(oid)
        self.assertTrue(result['verification_required'])
        self.assertNotIn('items',result)
        self.assertNotIn('status',result)
        self.assertNotIn('delivery_pincode',result)

    def test_verification_and_order_switch(self):
        tools = Tools(DATA)
        oid,other = list(tools.raw._ORDERS)[:2]
        tools.lookup(oid)
        pin = tools.raw._ORDERS[oid]['delivery_pincode']
        result = tools.accept_proof(pin)
        self.assertTrue(result['verified'])
        self.assertNotIn('delivery_pincode', result)
        tools.lookup(other)
        self.assertIsNone(tools.order)
        self.assertTrue(tools.awaiting)

    def test_two_failures_stay_locked_on_switch(self):
        tools = Tools(DATA)
        oid,other = list(tools.raw._ORDERS)[:2]
        tools.lookup(oid)
        for _ in range(2):
            self.assertFalse(tools.accept_proof('000000')['verified'])
        tools.lookup(other)
        self.assertIn('locked',tools.lookup(oid)['error'])
        self.assertIsNone(tools.order)

    def test_ticket_failure_does_not_become_success(self):
        tools = Tools(DATA)
        tools.raw.create_ticket = lambda **kwargs:{'created':False,'error':'disk failure'}
        self.assertFalse(tools.ticket_for('damaged item','damage','human review')['created'])

    def test_ticket_dedup_and_redaction(self):
        tools = Tools(DATA)
        captured = []
        def create(**kwargs):
            captured.append(kwargs)
            return {'created':True,'ticket_id':'test-ticket'}
        tools.raw.create_ticket = create
        for _ in range(2):
            tools.ticket_for('Phone suffix 1234 and postcode 560001','support','human review')
        self.assertEqual(len(captured),1)
        self.assertNotIn('1234',captured[0]['summary'])
        self.assertNotIn('560001',captured[0]['summary'])

    def test_calendar_skips_sunday_and_holiday(self):
        calendar = Calendar(DATA)
        self.assertEqual(calendar.add('2026-10-17',1)['date'],'2026-10-20')
        self.assertEqual(calendar.add('2026-10-17',1,'calendar')['date'],'2026-10-18')
        self.assertEqual(calendar.add('2026-10-20',0)['date'],'2026-10-20')
        with self.assertRaises(ValueError):
            calendar.add('2026-10-20',-1)

    def test_coupon_clawback_and_rounding(self):
        order = {'subtotal_inr':1000,'coupon_discount_inr':100,'coupon_min_order_inr':900,
            'items':[{'line_no':1,'qty':1,'unit_price_inr':200}]}
        result = partial_refund(order,'1',1,49)
        self.assertEqual(result['refund_inr'],51)
        self.assertEqual(money('10.5'),11)

    def test_section_metadata_and_catalog(self):
        chunks = self.index.chunks
        self.assertTrue(any(c['id']=='RET-2' and c['status']=='current' for c in chunks))
        self.assertTrue(any(c['status']=='superseded' for c in chunks))
        self.assertEqual(sum(c['id'].startswith('products.csv:') for c in chunks),70)
        self.assertIn('REF-2',[c['id'] for c in self.index.search('refund UPI business days')])

    def test_spoken_and_native_digits(self):
        self.assertEqual(numeric_groups('eight nine seven eight two eight three seven'),['89782837'])
        self.assertEqual(numeric_groups('१२३४'),['1234'])

    def test_proof_not_sent_to_model_or_history(self):
        api = FakeAPI()
        agent = Agent(DATA,self.index,api)
        oid = next(iter(agent.tools.raw._ORDERS))
        pin = agent.tools.raw._ORDERS[oid]['delivery_pincode']
        agent.tools.lookup(oid)
        agent.respond(pin)
        self.assertNotIn(pin,json.dumps(api.messages,ensure_ascii=False))
        self.assertNotIn(pin,json.dumps(agent.history,ensure_ascii=False))

    def test_new_sessions_are_isolated(self):
        one,two = Agent(DATA,self.index,FakeAPI()), Agent(DATA,self.index,FakeAPI())
        one.tools.lookup(next(iter(one.tools.raw._ORDERS)))
        self.assertIsNone(two.tools.order_id)
        self.assertFalse(two.tools.awaiting)

    def test_unknown_evidence_is_filtered(self):
        a = Agent(DATA,self.index,FakeAPI())
        result = a.parse(json.dumps({'answer':'Hello','decision':'answer','evidence':['invented-id']}))
        self.assertEqual(result['evidence'],[])
        with self.assertRaises(RuntimeError):
            a.parse('not JSON')

    def test_empty_transcript_recovery_no_llm(self):
        api = FakeAPI()
        a = Agent(DATA,self.index,api)
        self.assertEqual(a.respond('')['decision'],'clarify')
        self.assertEqual(api.messages,[])

    def test_natural_audio_order_and_ignore_non_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ['turn10.wav','turn2.wav','turn1.wav','notes.txt']:
                (Path(tmp)/name).touch()
            self.assertEqual([p.name for p in audio_files(Path(tmp))],['turn1.wav','turn2.wav','turn10.wav'])

if __name__=='__main__':
    unittest.main()

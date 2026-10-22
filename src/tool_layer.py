"""Load supplied mock tools unchanged; enforce session verification outside the LLM."""
import importlib.util
import re
from .business import Calendar, partial_refund

def normalize_numbers(text):
    words = dict(zip('zero one two three four five six seven eight nine'.split(), '0123456789'))
    words.update({'oh':'0'})
    text = ''.join(str(int(c)) if c.isdecimal() else c for c in text)
    return re.sub(r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|oh)\b', lambda m: words[m[0].lower()], text, flags=re.I)

def numeric_groups(text):
    text = normalize_numbers(text)
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '[date]', text)
    return [re.sub(r'\D', '', m[0]) for m in re.finditer(r'(?<!\d)\d(?:[\s-]*\d)*(?!\d)', text)]

class Tools:
    def __init__(self, dataset):
        spec = importlib.util.spec_from_file_location('zentro_supplied_tools', dataset / 'tools/tools.py')
        self.raw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.raw)
        self.calendar = Calendar(dataset)
        self.reset()

    def reset(self):
        self.order_id = None
        self.order = None
        self.attempts = {}
        self.awaiting = False
        self.ticket = None
        self.events = []
        self.verified_orders = {}

    def lookup(self, order_id):
        oid = re.sub(r'\D','', normalize_numbers(str(order_id)))
        if len(oid) != 8:
            return {'error': 'Ask for an eight-digit order ID.'}
        if oid != self.order_id:
            self.order_id, self.order, self.ticket = oid, self.verified_orders.get(oid), None
        if self.order:
            return self.order
        if self.attempts.get(oid, 0) >= 2:
            return {'error': 'Verification locked after two failed attempts; offer human help. No order details.'}
        self.awaiting = True
        result = self.raw.lookup_order(oid)
        self.events.append({'tool': 'lookup_order', 'order_id': oid, 'verified': False})
        return result

    def accept_proof(self, text):
        if not self.awaiting or not self.order_id:
            return None
        # Never forward verification material to LLM, history, trace or ticket.
        groups = numeric_groups(text)
        proofs = [x for x in groups if len(x) in (4,6)]
        if len(proofs) != 1:
            return {'error': 'Provide just one value: last four phone digits or delivery pincode.'}
        oid = self.order_id
        if self.attempts.get(oid, 0) >= 2:
            self.awaiting = False
            return {'error': 'Verification locked; offer human help.'}
        result = self.raw.lookup_order(oid, verification_value=proofs[0])
        self.events.append({'tool': 'lookup_order', 'order_id': oid, 'verified': bool(result.get('verified'))})
        if result.get('verified'):
            # The pincode itself was proof: do not retain it in LLM-visible data.
            result.pop('delivery_pincode', None)
            self.order = result
            self.verified_orders[oid] = result
            self.awaiting = False
        else:
            self.attempts[oid] = self.attempts.get(oid, 0) + 1
            result = {'verified': False, 'attempts_left': 2-self.attempts[oid]}
            if self.attempts[oid] >= 2:
                self.awaiting = False
                result['instruction'] = 'Do not retry; offer human help.'
        return result

    def ticket_for(self, issue, intent, reason):
        if self.ticket and self.ticket.get('created'):
            return self.ticket
        # Deterministic sanitization, even if the model puts a secret in its summary.
        summary = f'Issue: {issue}; intent: {intent}; order: {self.order_id or "not supplied"}; checks: {"identity verified and order checked" if self.order else "identity not verified; private data withheld"}; escalation reason: {reason}'
        summary = normalize_numbers(summary)
        summary = re.sub(r'(?<!\d)\d{4,6}(?!\d)', '[redacted]', summary)
        self.ticket = self.raw.create_ticket(summary=summary, order_id=self.order_id, reason=reason, intent=intent)
        self.events.append({'tool':'create_ticket', 'created': bool(self.ticket.get('created')), 'ticket_id':self.ticket.get('ticket_id')})
        return self.ticket

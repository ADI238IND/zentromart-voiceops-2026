"""Calendar arithmetic uses the frozen dataset date, never the host clock."""
import csv
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

class Calendar:
    def __init__(self, dataset):
        with open(dataset / 'data/holidays.csv', encoding='utf-8') as f:
            self.holidays = {r['date'] for r in csv.DictReader(f)}

    def add(self, start, days, kind='business'):
        current = date.fromisoformat(start)
        if not isinstance(days, int) or days < 0 or days > 3660:
            raise ValueError('days must be an integer between 0 and 3660')
        if kind not in ('business', 'calendar'):
            raise ValueError('kind must be business or calendar')
        for _ in range(days):
            current += timedelta(days=1)
            if kind == 'business':
                while current.weekday() == 6 or current.isoformat() in self.holidays:
                    current += timedelta(days=1)
        return {'date': current.isoformat(), 'counting': 'start day excluded; Mon-Sat excluding listed holidays' if kind == 'business' else 'calendar days'}

def money(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def partial_refund(order, line_no, qty, pickup_fee):
    items = order['items']
    line = next(x for x in items if str(x['line_no']) == str(line_no))
    if not isinstance(qty, int) or not 0 < qty <= line['qty']:
        raise ValueError('Invalid returned quantity')
    gross = Decimal(str(line['unit_price_inr'])) * qty
    subtotal = Decimal(str(order['subtotal_inr']))
    discount = Decimal(str(order.get('coupon_discount_inr') or 0))
    share = gross * discount / subtotal if subtotal else Decimal(0)
    remaining = subtotal - gross
    clawback = discount - share if discount and remaining < Decimal(str(order.get('coupon_min_order_inr') or 0)) else Decimal(0)
    refund = max(Decimal(0), gross - share - clawback - Decimal(str(pickup_fee)))
    return {'refund_inr': money(refund), 'gross_inr': str(gross), 'allocated_coupon_inr': str(share),
        'coupon_clawback_inr': str(clawback), 'pickup_fee_inr': pickup_fee,
        'note': 'Estimate only; apply REF-4 and RET-6 eligibility before quoting. Does not execute refund.'}

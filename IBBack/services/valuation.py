from typing import Optional

def calculate_ev(market_cap, total_debt, cash):
    if market_cap is not None and total_debt is not None and cash is not None:
        return float(market_cap) + float(total_debt) - float(cash)
    return None

def calculate_ev_ebit(ev, ebit):
    if ev is not None and ebit not in (None, 0):
        return ev / ebit
    return None

def calculate_fair_value(ev, ebit, peer_multiple, total_debt, cash, shares_out, market_cap, current_price):
    fair_ev = (peer_multiple * ebit) if ebit is not None else None
    fair_equity = (fair_ev - (total_debt or 0) + (cash or 0)) if fair_ev is not None else None
    if fair_equity is None and shares_out and current_price:
        fair_equity = market_cap
    return (fair_equity / shares_out) if (fair_equity is not None and shares_out) else None

def calculate_upside(fair_value, current_price):
    if fair_value is not None and current_price:
        return (fair_value / current_price - 1) * 100.0
    return None
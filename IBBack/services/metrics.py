from utils.finance import cagr, ratio_safe, last_value, avg_last_n, get_row, split_first_last
from typing import Optional

def calculate_revenue_cagr(rev, years):
    first_val, last_val, n_hist = split_first_last(rev, years)
    return cagr(first_val, last_val, n_hist)

def calculate_operating_margin(op_income, rev):
    return ratio_safe(last_value(op_income), last_value(rev))

def calculate_net_debt_to_equity(total_debt, cash, equity):
    nd = None
    if total_debt is not None and cash is not None:
        nd = last_value(total_debt) - last_value(cash)
    return ratio_safe(nd, last_value(equity))

def calculate_interest_coverage(op_income, interest_exp):
    ebit_latest = last_value(op_income)
    interest_latest = abs(last_value(interest_exp)) if last_value(interest_exp) is not None else None
    if interest_latest is not None and interest_latest > 0:
        return ratio_safe(ebit_latest, interest_latest)
    return None

def calculate_roe(net_income, equity):
    avg_equity_2y = avg_last_n(equity, 2)
    return ratio_safe(last_value(net_income), avg_equity_2y)

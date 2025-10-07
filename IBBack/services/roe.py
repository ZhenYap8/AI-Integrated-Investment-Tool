from typing import List, Dict, Optional
from utils.finance import avg_last_n, ratio_safe
import pandas as pd

def calculate_historical_roe(
    net_income: Optional['pd.Series'], 
    equity: Optional['pd.Series']
) -> List[Dict[str, float]]:
    """
    Calculate historical ROE (Return on Equity) across years.

    Args:
        net_income: A pandas Series of net income values (indexed by year).
        equity: A pandas Series of total equity values (indexed by year).

    Returns:
        A list of dictionaries containing the year and ROE value.
    """
    historical_roe = []
    if net_income is not None and equity is not None:
        for year in net_income.index:
            try:
                ni = net_income.get(year)
                avg_equity = avg_last_n(equity, 2)  # Average equity over 2 years
                roe = ratio_safe(ni, avg_equity)
                if roe is not None:
                    historical_roe.append({"date": year.isoformat(), "roe": roe * 100})  # Convert to percentage
            except Exception:
                continue
    return historical_roe
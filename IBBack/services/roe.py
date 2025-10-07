"""ROE analytics & visualization unified module.

Contains:
- Historical ROE calculation helpers (calculate_historical_roe, historical_roe_dataframe)
- Full charting pipeline (RoeConfig, prepare_roe_data, compute_rolling_metrics, flag_outliers,
  fit_trend, plot_roe, plot_dupont, build_roe_chart)

Use build_roe_chart for end-to-end figure generation.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import math
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.ticker import FuncFormatter, MultipleLocator

from utils.finance import ratio_safe

# Optional LOESS support
try:  # pragma: no cover (optional dependency)
    from statsmodels.nonparametric.smoothers_lowess import lowess  # type: ignore
    _HAS_LOWESS = True
except Exception:  # pragma: no cover
    _HAS_LOWESS = False

# ---------------------------------------------------------------------------
# Historical ROE (kept from original implementation, enhanced vectorized version)
# ---------------------------------------------------------------------------

def calculate_historical_roe(
    net_income: Optional['pd.Series'],
    equity: Optional['pd.Series'],
    ticker: Optional[str] = None,
) -> List[Dict[str, float]]:
    """Vectorized historical ROE (Return on Equity) per year.

    For each year: ROE = NetIncome / AverageEquity where AverageEquity = (Equity_year + Equity_prev_year)/2.
    Falls back gracefully if prior year equity is missing (that year is skipped).

    Args:
        net_income: pandas Series indexed by year-like (datetime/Period/int) with net income values.
        equity: pandas Series indexed by same index containing equity (end of period) values.
        ticker: Optional ticker string to include in each record.

    Returns:
        List of dicts: { 'date': ISO year-end date string, 'roe': ROE_percent, ['ticker']: optional }.
    """
    if net_income is None or equity is None or len(net_income) == 0 or len(equity) == 0:
        return []

    # Align on intersection of indices
    df = pd.DataFrame({'net_income': net_income, 'equity': equity}).dropna(subset=['net_income', 'equity'])
    if df.empty:
        return []

    # Ensure DateTimeIndex (convert pure int / Period year indices)
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            # Assume index represents years
            df.index = pd.to_datetime(df.index.astype(str) + '-12-31')
        except Exception:
            # Last resort: coerce
            df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.sort_index()

    # Previous year equity
    df['equity_prev'] = df['equity'].shift(1)
    df['avg_equity'] = (df['equity'] + df['equity_prev']) / 2.0

    # Compute ROE safely; skip where avg_equity missing or zero/near-zero
    def _calc(row):
        if pd.isna(row['avg_equity']) or abs(row['avg_equity']) < 1e-9:
            return None
        return ratio_safe(row['net_income'], row['avg_equity'])

    df['roe_ratio'] = df.apply(_calc, axis=1)
    df = df.dropna(subset=['roe_ratio'])
    if df.empty:
        return []

    records: List[Dict[str, float]] = []
    for idx, row in df.iterrows():
        rec: Dict[str, float] = {
            'date': idx.date().isoformat(),  # year-end date
            'roe': float(row['roe_ratio'] * 100.0)  # convert to percentage points
        }
        if ticker:
            rec['ticker'] = ticker
        records.append(rec)
    return records

def historical_roe_dataframe(
    net_income: Optional['pd.Series'],
    equity: Optional['pd.Series'],
    ticker: Optional[str] = None,
) -> pd.DataFrame:
    """Convenience wrapper returning a tidy DataFrame (date, roe[, ticker])."""
    rows = calculate_historical_roe(net_income, equity, ticker=ticker)
    if not rows:
        return pd.DataFrame(columns=['date', 'roe'] + ([ 'ticker' ] if ticker else []))
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)

# ---------------------------------------------------------------------------
# Configuration for charting
# ---------------------------------------------------------------------------
@dataclass
class RoeConfig:
    rolling_window_years: int = 3
    cost_of_equity_pct: Optional[float] = None
    target_zone_low_pct: Optional[float] = None
    target_zone_high_pct: Optional[float] = None
    show_dupont: bool = False
    tickers: Optional[List[str]] = None
    start: Optional[str] = None
    end: Optional[str] = None
    annotate_events: Optional[List[Dict[str, Any]]] = None
    regression_trend: bool = False
    vol_band: bool = True
    theme: str = "light"
    smooth_method: str = "rolling_mean"  # or 'loess'
    clamp_min: float = -200.0
    clamp_max: float = 200.0

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

# ---------------------------------------------------------------------------
# Data preparation and metrics
# ---------------------------------------------------------------------------

def prepare_roe_data(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    cfg = RoeConfig(**(config or {}))
    required = {"date", "ticker", "roe"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    out = df.copy()
    out['date'] = pd.to_datetime(out['date'], errors='coerce')
    out = out.dropna(subset=['date', 'ticker', 'roe'])
    out['ticker'] = out['ticker'].astype(str)
    if cfg.tickers:
        out = out[out['ticker'].isin(cfg.tickers)]
    if cfg.start:
        out = out[out['date'] >= pd.to_datetime(cfg.start)]
    if cfg.end:
        out = out[out['date'] <= pd.to_datetime(cfg.end)]
    out = out.drop_duplicates(subset=['date', 'ticker']).sort_values(['ticker', 'date'])
    out['clamped_flag'] = (out['roe'] < cfg.clamp_min) | (out['roe'] > cfg.clamp_max)
    out['roe_clamped'] = out['roe'].clip(cfg.clamp_min, cfg.clamp_max)
    return out.reset_index(drop=True)

def _rolling_calendar_window(group: pd.DataFrame, years: int) -> pd.DataFrame:
    g = group.set_index('date').sort_index()
    window = f"{years * 365}D"
    roll = g['roe_clamped'].rolling(window=window, min_periods=max(2, years))
    group['roe_roll_mean'] = roll.mean().values
    group['roe_roll_std'] = roll.std(ddof=0).values
    return group

def compute_rolling_metrics(df: pd.DataFrame, window_years: int = 3) -> pd.DataFrame:
    if 'roe_clamped' not in df.columns:
        raise ValueError("Expected 'roe_clamped'. Run prepare_roe_data first.")
    parts = []
    for _, grp in df.groupby('ticker', sort=False):
        parts.append(_rolling_calendar_window(grp.copy(), window_years))
    return pd.concat(parts, ignore_index=True)

def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    z_vals = []
    flags = []
    for _, grp in out.groupby('ticker'):
        mu = grp['roe_clamped'].mean()
        sigma = grp['roe_clamped'].std(ddof=0) or 1e-9
        z = (grp['roe_clamped'] - mu) / sigma
        z_vals.append(z)
        flags.append(z.abs() > 3)
    out['z_score'] = pd.concat(z_vals)
    out['outlier_flag'] = pd.concat(flags)
    return out

def fit_trend(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    results: Dict[str, Dict[str, float]] = {}
    for t, grp in df.groupby('ticker'):
        if len(grp) < 3:
            continue
        years = grp['date'].dt.year + (grp['date'].dt.dayofyear - 1) / 365.25
        x = years.values
        y = grp['roe_clamped'].values
        x_mean = x.mean(); y_mean = y.mean()
        denom = ((x - x_mean) ** 2).sum()
        if denom == 0:
            continue
        slope = ((x - x_mean) * (y - y_mean)).sum() / denom
        intercept = y_mean - slope * x_mean
        results[t] = {'slope_pp_per_year': float(slope), 'intercept': float(intercept)}
    return results

# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------
_THEME_STYLES = {
    'light': {'facecolor': 'white', 'grid': '#e5e5e5', 'text': '#222', 'target_zone': (0.92, 0.97, 1.0, 0.25)},
    'dark': {'facecolor': '#111', 'grid': '#333', 'text': '#ddd', 'target_zone': (0.3, 0.4, 0.6, 0.25)}
}

def _apply_theme(ax, theme: str):
    style = _THEME_STYLES.get(theme, _THEME_STYLES['light'])
    ax.set_facecolor(style['facecolor'])
    ax.grid(True, color=style['grid'], linewidth=0.6, alpha=0.6)
    ax.tick_params(colors=style['text'])
    for s in ax.spines.values():
        s.set_color(style['grid'])
    ax.yaxis.label.set_color(style['text'])
    ax.xaxis.label.set_color(style['text'])
    return style

def _maybe_loess(x: np.ndarray, y: np.ndarray, frac: float = 0.5) -> np.ndarray:
    if not _HAS_LOWESS:
        return y
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return lowess(y, x, frac=frac, return_sorted=False)

# ---------------------------------------------------------------------------
# Primary ROE plot
# ---------------------------------------------------------------------------

def plot_roe(df: pd.DataFrame, benchmarks: Optional[pd.DataFrame] = None, config: Optional[Dict[str, Any]] = None):
    cfg = RoeConfig(**(config or {}))
    if 'roe_roll_mean' not in df.columns:
        raise ValueError('Missing rolling metrics; run compute_rolling_metrics.')
    if 'outlier_flag' not in df.columns:
        raise ValueError('Missing outlier flags; run flag_outliers.')

    data = df.copy()
    if cfg.start:
        data = data[data['date'] >= pd.to_datetime(cfg.start)]
    if cfg.end:
        data = data[data['date'] <= pd.to_datetime(cfg.end)]

    trend = fit_trend(data) if cfg.regression_trend else {}

    bench_map = None
    if benchmarks is not None and 'sector' in data.columns:
        b = benchmarks.copy()
        if {'date', 'sector', 'roe_median'}.issubset(b.columns):
            b['date'] = pd.to_datetime(b['date'])
            bench_map = b
        else:
            warnings.warn('Benchmarks missing required columns; skipping overlay')

    fig, ax = plt.subplots(figsize=(11, 6.5))
    style = _apply_theme(ax, cfg.theme)

    # Target zone & reference lines
    if cfg.target_zone_low_pct is not None and cfg.target_zone_high_pct is not None:
        ax.axhspan(cfg.target_zone_low_pct, cfg.target_zone_high_pct, color=style['target_zone'], zorder=0, lw=0)
    if cfg.cost_of_equity_pct is not None:
        ax.axhline(cfg.cost_of_equity_pct, color='#b5651d', linestyle='--', linewidth=1.2, label='Cost of Equity')
        ax.text(1.001, cfg.cost_of_equity_pct, f"CoE {cfg.cost_of_equity_pct:.1f}%", color='#b5651d', va='center', ha='left', transform=ax.get_yaxis_transform())
    ax.axhline(0, color=style['grid'], linewidth=0.8)

    # Dynamic date tick strategy
    if not data.empty:
        span_days = (data['date'].max() - data['date'].min()).days or 1
        span_years = span_days / 365.25
        if span_years > 5:  # long span: yearly majors, quarterly minors
            from matplotlib.dates import YearLocator, MonthLocator
            ax.xaxis.set_major_locator(YearLocator())
            ax.xaxis.set_major_formatter(DateFormatter('%Y'))
            ax.xaxis.set_minor_locator(MonthLocator(bymonth=[3,6,9,12]))
        elif span_years > 2:  # medium: yearly majors, monthly minors
            from matplotlib.dates import YearLocator, MonthLocator
            ax.xaxis.set_major_locator(YearLocator())
            ax.xaxis.set_major_formatter(DateFormatter('%Y'))
            ax.xaxis.set_minor_locator(MonthLocator())
        else:  # short: quarterly majors, monthly minors
            from matplotlib.dates import MonthLocator
            ax.xaxis.set_major_locator(MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
            ax.xaxis.set_minor_locator(MonthLocator())
    else:
        locator = AutoDateLocator(minticks=6, maxticks=12)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

    ax.tick_params(axis='x', which='major', length=6, labelsize=9)
    ax.tick_params(axis='x', which='minor', length=3, labelsize=0)  # hide minor labels for clarity

    cmap = plt.cm.get_cmap('tab10')
    tickers = list(dict.fromkeys(data['ticker']))
    for i, t in enumerate(tickers):
        sub = data[data['ticker'] == t].sort_values('date')
        if sub.empty:
            continue
        c = cmap(i % 10)
        ax.plot(sub['date'], sub['roe_clamped'], color=c, linewidth=1.2, alpha=0.85, label=f"{t} ROE")
        if cfg.smooth_method == 'loess' and _HAS_LOWESS:
            x_ord = sub['date'].map(pd.Timestamp.toordinal).to_numpy()
            smooth = _maybe_loess(x_ord, sub['roe_clamped'].to_numpy())
            ax.plot(sub['date'], smooth, color=c, linewidth=2.0, label=f"{t} (LOESS)")
        else:
            ax.plot(sub['date'], sub['roe_roll_mean'], color=c, linewidth=2.0, linestyle='--', label=f"{t} {cfg.rolling_window_years}y MA")
        if cfg.vol_band:
            upper = sub['roe_roll_mean'] + sub['roe_roll_std']
            lower = sub['roe_roll_mean'] - sub['roe_roll_std']
            ax.fill_between(sub['date'], lower, upper, color=c, alpha=0.12, linewidth=0)
        if t in trend:
            yrs = sub['date'].dt.year + (sub['date'].dt.dayofyear - 1) / 365.25
            ti = trend[t]
            ytrend = ti['intercept'] + ti['slope_pp_per_year'] * yrs
            ax.plot(sub['date'], ytrend, color=c, linestyle=':', linewidth=1.0, label=f"{t} trend ({ti['slope_pp_per_year']:+.2f} pp/yr)")
        outs = sub[sub['outlier_flag']]
        if not outs.empty:
            ax.scatter(outs['date'], outs['roe_clamped'], marker='^', color=c, s=60, edgecolor='k', linewidth=0.4, zorder=5)
        if bench_map is not None and 'sector' in sub.columns:
            sector = sub['sector'].iloc[0]
            sb = bench_map[bench_map['sector'] == sector]
            if not sb.empty:
                ax.plot(sb['date'], sb['roe_median'], color=c, linewidth=1.0, alpha=0.35, linestyle='-.', label=f"{sector} median")

    if cfg.annotate_events:
        used = set()
        for evt in cfg.annotate_events:
            try:
                d = pd.to_datetime(evt.get('date'))
            except Exception:
                continue
            tkr = evt.get('ticker')
            text = evt.get('text', '')
            sub = data[(data['ticker'] == tkr) & (data['date'] == d)] if tkr else data[data['date'] == d].head(1)
            if sub.empty:
                continue
            yv = float(sub['roe_clamped'].iloc[0])
            shift = 0
            while (d, yv + shift) in used:
                shift += 1.5
            used.add((d, yv + shift))
            ax.annotate(text, xy=(d, yv), xytext=(0, 22 + shift), textcoords='offset points',
                        arrowprops=dict(arrowstyle='->', lw=0.8, color=style['text']), ha='center', fontsize=9, color=style['text'])

    ax.set_ylabel('ROE (%)')
    ax.set_xlabel('Date')

    # Y limits & tick engineering
    y_min = min(-5, math.floor(data['roe_clamped'].min() - 2)) if not data.empty else -5
    y_max = math.ceil(data['roe_clamped'].max() + 2) if not data.empty else 5
    ax.set_ylim(y_min, y_max)
    yrange = max(1, y_max - y_min)
    desired = 6
    rough = yrange / desired
    candidates = [0.5, 1, 2, 2.5, 5, 10, 20, 25, 50]
    step = next((c for c in candidates if c >= rough), candidates[-1])
    start_tick = math.floor(y_min / step) * step
    end_tick = math.ceil(y_max / step) * step
    ticks = np.arange(start_tick, end_tick + step * 0.51, step)
    ax.set_yticks(ticks)
    if step >= 2:
        ax.yaxis.set_minor_locator(MultipleLocator(step / 2))
        ax.tick_params(axis='y', which='minor', length=3, labelsize=0)
    ax.tick_params(axis='y', which='major', length=6, labelsize=9)

    def _fmt_y(v, _):
        if abs(step) < 1:
            return f"{v:.1f}%"
        return f"{v:.0f}%"
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_y))

    handles, labels = ax.get_legend_handles_labels()
    seen = set(); fh = []; fl = []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l); fh.append(h); fl.append(l)
    ax.legend(fh, fl, ncol=2, fontsize=9, frameon=False)
    ax.set_title('Return on Equity Over Time')
    fig.tight_layout()
    return fig

# ---------------------------------------------------------------------------
# DuPont decomposition
# ---------------------------------------------------------------------------

def plot_dupont(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None):
    cfg = RoeConfig(**(config or {}))
    if not cfg.show_dupont:
        return None
    needed = {'npm', 'ato', 'em'}
    if not needed.issubset(df.columns):
        return None
    tickers = list(dict.fromkeys(df['ticker']))[:4]
    fig, axes = plt.subplots(len(tickers), 3, figsize=(12, 3.2 * len(tickers)))
    if len(tickers) == 1:
        axes = np.array([axes])
    for row, t in enumerate(tickers):
        sub = df[df['ticker'] == t].sort_values('date')
        for col, metric in enumerate(['npm', 'ato', 'em']):
            ax = axes[row, col]
            _apply_theme(ax, cfg.theme)
            ax.plot(sub['date'], sub[metric], marker='o', linewidth=1.2, color='tab:blue')
            ax.set_title(f"{t} - {metric.upper()}")
            if row == len(tickers) - 1:
                ax.set_xlabel('Date')
    fig.suptitle('DuPont Decomposition Components', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def build_roe_chart(df: pd.DataFrame, benchmarks: Optional[pd.DataFrame] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = RoeConfig(**(config or {}))
    cleaned = prepare_roe_data(df, cfg.to_dict())
    rolled = compute_rolling_metrics(cleaned, cfg.rolling_window_years)
    flagged = flag_outliers(rolled)
    trend = fit_trend(flagged) if cfg.regression_trend else {}
    fig = plot_roe(flagged, benchmarks=benchmarks, config=cfg.to_dict())
    dupont = plot_dupont(flagged, cfg.to_dict()) if cfg.show_dupont else None
    return {'data': flagged, 'fig': fig, 'dupont_fig': dupont, 'trend': trend}

# ---------------------------------------------------------------------------
# __all__ for clarity
# ---------------------------------------------------------------------------
__all__ = [
    'RoeConfig', 'prepare_roe_data', 'compute_rolling_metrics', 'flag_outliers', 'fit_trend',
    'plot_roe', 'plot_dupont', 'build_roe_chart', 'calculate_historical_roe', 'historical_roe_dataframe'
]
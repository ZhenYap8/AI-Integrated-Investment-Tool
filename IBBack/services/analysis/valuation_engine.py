"""
Valuation Engine - Calculate company valuation metrics
"""
from typing import Dict, Any, Optional
import yfinance as yf

class ValuationEngine:
    """Handles valuation calculations and fair value estimates."""
    
    def calculate_valuation(self, ticker_obj: Any, metrics: Dict[str, float], thresh: Dict[str, float]) -> Dict:
        """Calculate valuation for a single company."""
        try:
            info = ticker_obj.info
            
            # Extract key valuation metrics
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            pe_ratio = info.get('trailingPE') or info.get('forwardPE', 0)
            pb_ratio = info.get('priceToBook', 0)
            ps_ratio = info.get('priceToSalesTrailing12Months', 0)
            market_cap = info.get('marketCap', 0)
            enterprise_value = info.get('enterpriseValue', 0)
            ev_to_revenue = info.get('enterpriseToRevenue', 0)
            ev_to_ebitda = info.get('enterpriseToEbitda', 0)
            
            # Build valuation table
            table = []
            
            if current_price:
                table.append({
                    'metric': 'Current Price',
                    'value': f'${current_price:.2f}',
                    'note': ''
                })
            
            if pe_ratio and pe_ratio > 0:
                table.append({
                    'metric': 'P/E Ratio',
                    'value': f'{pe_ratio:.2f}',
                    'note': 'Price to Earnings'
                })
            
            if pb_ratio and pb_ratio > 0:
                table.append({
                    'metric': 'P/B Ratio',
                    'value': f'{pb_ratio:.2f}',
                    'note': 'Price to Book'
                })
            
            if ps_ratio and ps_ratio > 0:
                table.append({
                    'metric': 'P/S Ratio',
                    'value': f'{ps_ratio:.2f}',
                    'note': 'Price to Sales'
                })
            
            if market_cap:
                market_cap_billions = market_cap / 1_000_000_000
                table.append({
                    'metric': 'Market Cap',
                    'value': f'${market_cap_billions:.2f}B',
                    'note': ''
                })
            
            if ev_to_revenue and ev_to_revenue > 0:
                table.append({
                    'metric': 'EV/Revenue',
                    'value': f'{ev_to_revenue:.2f}',
                    'note': 'Enterprise Value to Revenue'
                })
            
            if ev_to_ebitda and ev_to_ebitda > 0:
                table.append({
                    'metric': 'EV/EBITDA',
                    'value': f'{ev_to_ebitda:.2f}',
                    'note': 'Enterprise Value to EBITDA'
                })
            
            # Calculate simple fair value estimate based on industry PE
            fair_value = None
            upside_pct = None
            
            if pe_ratio and pe_ratio > 0:
                # Use a target PE of 15-20 as reasonable benchmark
                target_pe = 18.0
                eps = current_price / pe_ratio if pe_ratio else 0
                if eps > 0:
                    fair_value = eps * target_pe
                    if current_price > 0:
                        upside_pct = ((fair_value - current_price) / current_price) * 100
            
            return {
                'table': table,
                'fairValue': fair_value,
                'currentPrice': current_price,
                'upsidePct': upside_pct
            }
            
        except Exception as e:
            print(f"[ValuationEngine] Error calculating valuation: {e}")
            return {
                'table': [],
                'fairValue': None,
                'currentPrice': None,
                'upsidePct': None
            }
    
    def calculate_industry_valuation(self, metrics: Dict[str, float], thresh: Dict[str, float]) -> Dict:
        """Calculate valuation for an industry (aggregated)."""
        # For industries, we return basic metrics without specific valuations
        table = []
        
        if metrics.get('operating_margin'):
            op_margin_pct = metrics['operating_margin'] * 100
            table.append({
                'metric': 'Avg Operating Margin',
                'value': f'{op_margin_pct:.1f}%',
                'note': 'Industry average'
            })
        
        if metrics.get('roe'):
            roe_pct = metrics['roe'] * 100
            table.append({
                'metric': 'Avg ROE',
                'value': f'{roe_pct:.1f}%',
                'note': 'Return on Equity'
            })
        
        if metrics.get('revenue_cagr'):
            rev_cagr_pct = metrics['revenue_cagr'] * 100
            table.append({
                'metric': 'Revenue CAGR',
                'value': f'{rev_cagr_pct:.1f}%',
                'note': '5-year growth rate'
            })
        
        return {
            'table': table,
            'fairValue': None,
            'currentPrice': None,
            'upsidePct': None
        }
    

'''
# debugging, test if this is working // debugging was successful.
engine = ValuationEngine()
ticker = yf.Ticker("AAPL")
result = engine.calculate_valuation(ticker, {}, {})
print(result)
'''


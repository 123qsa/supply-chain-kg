"""Yahoo Finance data source client"""
import yfinance as yf
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Yahoo Finance data source client for US/Global markets"""

    def __init__(self):
        """Initialize Yahoo Finance client"""
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        return False

    def discover_peers(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover competitor companies using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            peers = []

            # Get peers from recommendation key or industry
            industry = info.get('industry')
            sector = info.get('sector')

            # Try to get peers from similar companies
            if 'companyOfficers' in info:
                # Use industry to find similar companies
                pass

            # Alternative: use stock screener approach via related stocks
            recommendations = ticker.recommendations
            if recommendations is not None and len(recommendations) > 0:
                # Get unique firms and their recommendations
                firms = recommendations['Firm'].unique()[:5]
                # This is indirect peer info

            # Get peers from institutional holders (they often hold competitors)
            holders = ticker.institutional_holders
            if holders is not None:
                # Extract top holders for relationship building
                pass

            # Return basic peer info based on sector/industry
            if sector:
                # For now, return the queried company as seed
                # In a real scenario, you'd query a database of sector peers
                peers.append({
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'sector': sector,
                    'industry': industry,
                    'relation': 'SELF'
                })

                # Add some known sector peers based on common knowledge
                sector_peers = self._get_sector_peers(symbol, sector, industry)
                peers.extend(sector_peers)

            return peers
        except Exception as e:
            logger.error(f"Failed to get peers for {symbol}: {e}")
            return []

    def _get_sector_peers(self, symbol: str, sector: str, industry: str) -> List[Dict[str, Any]]:
        """Get known sector peers for major stocks"""
        # Known peer mappings for major sectors
        peer_mappings = {
            'Technology': {
                'Semiconductors': ['AMD', 'INTC', 'QCOM', 'AVGO', 'MRVL', 'TSM'],
                'Software': ['MSFT', 'GOOGL', 'META', 'CRM', 'ADBE'],
                'Hardware': ['AAPL', 'DELL', 'HPQ', 'Lenovo'],
            },
            'Communication Services': {
                'Internet': ['GOOGL', 'META', 'AMZN', 'NFLX', 'Twitter'],
                'Telecom': ['VZ', 'T', 'TMUS'],
            },
            'Consumer Cyclical': {
                'Auto': ['TSLA', 'F', 'GM', 'TM', 'HMC'],
                'Retail': ['AMZN', 'WMT', 'TGT', 'COST'],
            },
            'Healthcare': {
                'Pharma': ['JNJ', 'PFE', 'MRK', 'ABBV', 'LLY'],
                'Biotech': ['AMGN', 'GILD', 'REGN', 'VRTX'],
            },
            'Financial Services': {
                'Banks': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
                'Insurance': ['BRK-B', 'UNH', 'CVS'],
            },
        }

        peers = []
        if sector in peer_mappings:
            for ind, symbols in peer_mappings[sector].items():
                if industry and ind in industry:
                    for peer_symbol in symbols:
                        if peer_symbol != symbol:
                            peers.append({
                                'symbol': peer_symbol,
                                'name': peer_symbol,  # Will be enriched later
                                'sector': sector,
                                'industry': ind,
                                'relation': 'COMPETES_WITH'
                            })

        return peers[:10]  # Limit to top 10 peers

    def discover_etf_holdings(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover ETF holdings using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Check if it's actually an ETF
            if info.get('quoteType') != 'ETF':
                logger.warning(f"{symbol} is not an ETF")
                return []

            holdings = []

            # Get holdings data
            try:
                # Try to get top holdings
                holdings_data = ticker.institutional_holders
                if holdings_data is not None:
                    for _, row in holdings_data.head(20).iterrows():
                        holdings.append({
                            'symbol': row.get('Holder', '').split()[-1] if ' ' in str(row.get('Holder', '')) else row.get('Holder', ''),
                            'name': row.get('Holder', ''),
                            'weight': None,  # yfinance doesn't provide exact weights easily
                            'relation': 'IN_ETF'
                        })
            except Exception as e:
                logger.warning(f"Could not get ETF holdings for {symbol}: {e}")

            # Alternative: get holdings from info
            if not holdings:
                # Some ETFs have holdings info in the ticker info
                holdings_text = info.get('holdings', [])
                if isinstance(holdings_text, list):
                    for h in holdings_text[:20]:
                        if isinstance(h, dict):
                            holdings.append({
                                'symbol': h.get('symbol', ''),
                                'name': h.get('name', ''),
                                'weight': h.get('holdingPercent', None),
                                'relation': 'IN_ETF'
                            })

            return holdings
        except Exception as e:
            logger.error(f"Failed to get ETF holdings for {symbol}: {e}")
            return []

    def get_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName', symbol),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'description': info.get('longBusinessSummary', ''),
                'market_cap': info.get('marketCap'),
                'employees': info.get('fullTimeEmployees'),
                'website': info.get('website', ''),
                'country': info.get('country', ''),
                'exchange': info.get('exchange', ''),
            }
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {e}")
            return None

    def get_price(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical price data using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)

            # Download historical data
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                logger.warning(f"No price data for {symbol} in date range")
                return []

            prices = []
            for date, row in hist.iterrows():
                prices.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 4) if not pd.isna(row['Open']) else None,
                    'high': round(row['High'], 4) if not pd.isna(row['High']) else None,
                    'low': round(row['Low'], 4) if not pd.isna(row['Low']) else None,
                    'close': round(row['Close'], 4) if not pd.isna(row['Close']) else None,
                    'volume': int(row['Volume']) if not pd.isna(row['Volume']) else None,
                })

            return prices
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return []

    def get_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial data using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)

            # Get income statement
            income_stmt = ticker.income_stmt
            latest_revenue = None
            latest_net_income = None

            if income_stmt is not None and not income_stmt.empty:
                # Get the most recent column (year)
                latest_col = income_stmt.columns[0]
                if 'Total Revenue' in income_stmt.index:
                    latest_revenue = income_stmt.loc['Total Revenue', latest_col]
                if 'Net Income' in income_stmt.index:
                    latest_net_income = income_stmt.loc['Net Income', latest_col]

            # Get balance sheet
            balance = ticker.balance_sheet
            total_assets = None
            total_debt = None

            if balance is not None and not balance.empty:
                latest_col = balance.columns[0]
                if 'Total Assets' in balance.index:
                    total_assets = balance.loc['Total Assets', latest_col]
                if 'Total Debt' in balance.index:
                    total_debt = balance.loc['Total Debt', latest_col]

            return {
                'symbol': symbol,
                'revenue': latest_revenue,
                'net_income': latest_net_income,
                'total_assets': total_assets,
                'total_debt': total_debt,
                'financial_currency': ticker.info.get('financialCurrency', 'USD'),
            }
        except Exception as e:
            logger.error(f"Failed to get financials for {symbol}: {e}")
            return None

    def get_institutional_holders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get institutional holders using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            holders = ticker.institutional_holders

            if holders is None or holders.empty:
                return []

            results = []
            for _, row in holders.iterrows():
                results.append({
                    'holder': row.get('Holder', ''),
                    'shares': row.get('Shares', 0),
                    'date_reported': row.get('Date Reported', '').strftime('%Y-%m-%d') if pd.notna(row.get('Date Reported')) else None,
                    'pct_out': row.get('% Out', 0),
                    'value': row.get('Value', 0),
                })

            return results
        except Exception as e:
            logger.error(f"Failed to get institutional holders for {symbol}: {e}")
            return []


# Import pandas for yfinance compatibility
try:
    import pandas as pd
except ImportError:
    pd = None

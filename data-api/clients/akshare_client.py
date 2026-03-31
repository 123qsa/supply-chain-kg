"""AkShare data source client"""
import akshare as ak
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AkShareClient:
    """AkShare data source client for A-share markets"""

    def __init__(self):
        """Initialize AkShare client"""
        pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        return False

    def discover_cn_concept(self, board_name: str) -> List[Dict[str, Any]]:
        """Discover companies in a concept board"""
        try:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get concept board {board_name}: {e}")
            return []

    def discover_cn_industry(self, board_name: str) -> List[Dict[str, Any]]:
        """Discover companies in an industry board"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=board_name)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get industry board {board_name}: {e}")
            return []

    def discover_cn_holders(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover top 10 shareholders"""
        try:
            df = ak.stock_main_stock_holder(stock=symbol)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get holders for {symbol}: {e}")
            return []

    def get_cn_price(self, symbol: str, start_date: str = "20240101",
                     end_date: str = "20261231") -> List[Dict[str, Any]]:
        """Get A-share historical price data"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get CN price for {symbol}: {e}")
            return []

    def get_cn_financial(self, symbol: str) -> List[Dict[str, Any]]:
        """Get A-share financial summary"""
        try:
            df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get CN financial for {symbol}: {e}")
            return []
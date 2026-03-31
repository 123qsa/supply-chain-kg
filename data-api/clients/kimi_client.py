"""Kimi API client for LLM inference with OAuth authentication"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from config import get_settings
import logging
import json

logger = logging.getLogger(__name__)


class KimiClient:
    """Kimi API client for LLM inference using OAuth 2.0 client_credentials flow

    Usage:
        async with KimiClient() as client:
            result = await client.analyze_impact(event, companies)

    Or without context manager:
        client = KimiClient()
        result = await client.analyze_impact(event, companies)
    """

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize Kimi client

        Args:
            client_id: OAuth client ID (optional, will read from config if not provided)
            client_secret: OAuth client secret (optional, will read from config if not provided)
        """
        settings = get_settings()
        self.client_id = client_id or settings.kimi_client_id
        self.client_secret = client_secret or settings.kimi_client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_buffer_seconds = 300  # Refresh token 5 minutes before expiry

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Clear token on exit
        self._access_token = None
        self._token_expires_at = None
        return False

    def is_configured(self) -> bool:
        """Check if client has valid credentials configured"""
        return bool(self.client_id and self.client_secret)

    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token using client_credentials flow

        Returns:
            Access token string or None if credentials not configured
        """
        if not self.is_configured():
            logger.warning("Kimi client not configured: missing client_id or client_secret")
            return None

        # Check if current token is still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(seconds=self._token_buffer_seconds):
                return self._access_token

        # Request new token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default 1 hour

                # Calculate expiry time
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                logger.debug(f"Obtained new Kimi access token, expires in {expires_in}s")
                return self._access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"Kimi OAuth failed: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Kimi OAuth failed: {e}")
            return None

    async def analyze_impact(
        self,
        event: str,
        companies: List[Dict[str, Any]],
        model: str = "moonshot-v1-8k"
    ) -> Dict[str, Any]:
        """Analyze event impact on companies using Kimi LLM

        Args:
            event: Event description
            companies: List of company data with relationship info
            model: Model to use (default: moonshot-v1-8k)

        Returns:
            Dictionary with analysis results or error
        """
        if not companies:
            return {"results": [], "error": "No companies provided"}

        token = await self._get_access_token()
        if not token:
            return {"results": [], "error": "Kimi not configured or authentication failed"}

        try:
            # Build prompt
            company_list = "\n".join([
                f"{i+1}. {c.get('name', 'Unknown')}({c.get('ticker', 'N/A')}) "
                f"— 路径: {' → '.join(c.get('name_chain', []))} "
                f"[{c.get('depth', 0)}跳] "
                f"关系: {c.get('relation', 'UNKNOWN')}"
                for i, c in enumerate(companies[:20])  # Limit to 20 companies
            ])

            prompt = f"""你是一位资深产业链分析专家。请基于以下产业链关系数据，分析事件对每家关联公司的影响。

## 事件
{event}

## 关联公司及产业链路径
{company_list}

## 分析要求
对每家公司判断：
1. 影响方向：利好 / 利空 / 中性
2. 影响程度：高(>5%) / 中(2-5%) / 低(<2%)
3. 传导逻辑：基于产业链路径，用一句话解释影响如何从事件源传导到该公司
4. 置信度：0-1

## 重要原则
- 同一关系在不同事件下可能有完全相反的影响
- 跳数越多，影响通常越弱，但关键依赖(DEPENDS_ON)可以跨跳保持高影响
- 竞争关系(COMPETES_WITH)通常产生反向影响
- 供应关系(SUPPLIES_TO)的影响方向取决于事件性质

输出严格 JSON 格式：
[{{"ticker": "XXX", "company": "名称", "direction": "利好/利空/中性", "magnitude": "高/中/低", "reasoning": "...", "confidence": 0.8}}]"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 4000
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

                # Extract JSON from response
                content = data["choices"][0]["message"]["content"]

                # Try to find JSON array in response
                results = self._extract_json_results(content)

                if results:
                    return {"results": results, "model": model}
                else:
                    logger.warning(f"Could not extract JSON from Kimi response: {content[:200]}")
                    return {"results": [], "raw": content, "error": "JSON extraction failed"}

        except httpx.HTTPStatusError as e:
            error_msg = f"Kimi API error: HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', e.response.text)}"
            except:
                error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            return {"results": [], "error": error_msg}

        except Exception as e:
            logger.error(f"Kimi analysis failed: {e}")
            return {"results": [], "error": str(e)}

    def _extract_json_results(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """Extract JSON array from LLM response

        Args:
            content: Raw response content

        Returns:
            List of result dictionaries or None if extraction fails
        """
        try:
            # Try to find JSON array in response
            start = content.find("[")
            end = content.rfind("]")

            if start >= 0 and end > start:
                json_str = content[start:end+1]
                results = json.loads(json_str)
                if isinstance(results, list):
                    return results

            # Try to parse entire content as JSON
            results = json.loads(content)
            if isinstance(results, list):
                return results
            elif isinstance(results, dict) and "results" in results:
                return results["results"]

        except json.JSONDecodeError as e:
            logger.debug(f"JSON decode error: {e}")

        return None

    async def health_check(self) -> Dict[str, Any]:
        """Check if Kimi API is accessible

        Returns:
            Health check result
        """
        if not self.is_configured():
            return {"status": "not_configured", "message": "Client ID or Secret not set"}

        token = await self._get_access_token()
        if not token:
            return {"status": "auth_failed", "message": "Failed to obtain access token"}

        return {"status": "healthy", "message": "Successfully authenticated"}

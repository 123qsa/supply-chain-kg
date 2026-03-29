"""Kimi API client for LLM inference"""
import httpx
from typing import Optional, Dict, Any, List
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class KimiClient:
    """Kimi API client for LLM inference"""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.kimi_client_id
        self.client_secret = settings.kimi_client_secret
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Get OAuth access token"""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def analyze_impact(self, event: str, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze event impact on companies"""
        try:
            token = await self._get_access_token()

            # Build prompt
            company_list = "\n".join([
                f"{i+1}. {c['name']}({c['ticker']}) — 路径: {' → '.join(c.get('name_chain', []))} "
                f"[{c.get('depth', 0)}跳]"
                for i, c in enumerate(companies)
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
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()

                # Extract JSON from response
                content = data["choices"][0]["message"]["content"]
                import json
                # Try to find JSON array in response
                start = content.find("[")
                end = content.rfind("]")
                if start >= 0 and end > start:
                    results = json.loads(content[start:end+1])
                    return {"results": results}
                return {"results": [], "raw": content}

        except Exception as e:
            logger.error(f"Kimi analysis failed: {e}")
            return {"results": [], "error": str(e)}
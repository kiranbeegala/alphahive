"""
Sentiment Analyst Agent — LIVE DATA VERSION
Fetches real news from Economic Times, Moneycontrol, Mint, and NSE RSS feeds.
Fetches real India VIX from yfinance (^INDIAVIX).
Fetches real Nifty PCR from NSE public API.
FII/DII data from NSE public endpoint.
Caches feeds for 5 minutes to avoid rate limiting.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import feedparser
import httpx
import yfinance as yf

logger = logging.getLogger("SentimentAnalyst")

# ─── RSS Feed Sources ────────────────────────────────────────────────────────
RSS_FEEDS = [
    {
        "name": "Economic Times Markets",
        "url": "https://economictimes.indiatimes.com/markets/rss.cms",
    },
    {
        "name": "Moneycontrol Markets",
        "url": "https://www.moneycontrol.com/rss/business.xml",
    },
    {
        "name": "LiveMint Markets",
        "url": "https://www.livemint.com/rss/markets",
    },
]

# ─── NSE API Endpoints ───────────────────────────────────────────────────────
NSE_PCR_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_FII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# ─── Sentiment keyword scoring ───────────────────────────────────────────────
BULLISH_KEYWORDS = [
    "rally", "surge", "gain", "rise", "bull", "record", "high", "profit",
    "growth", "expand", "upgrade", "positive", "inflow", "buy", "strong",
    "recovery", "boost", "beat", "outperform", "dividend", "rate cut",
    "fii buying", "dii buying", "upside", "breakout", "support",
]
BEARISH_KEYWORDS = [
    "fall", "drop", "crash", "decline", "bear", "loss", "weak", "sell",
    "outflow", "downgrade", "negative", "volatility", "risk", "recession",
    "inflation", "rate hike", "caution", "warning", "geopolitical",
    "fii selling", "correction", "breakdown", "resistance",
]

# ─── Cache ───────────────────────────────────────────────────────────────────
_news_cache: Dict[str, Any] = {"data": [], "ts": 0.0}
_vix_cache: Dict[str, Any] = {"value": None, "ts": 0.0}
_pcr_cache: Dict[str, Any] = {"value": None, "ts": 0.0}
_fii_cache: Dict[str, Any] = {"value": None, "ts": 0.0}
_nse_cookies: Dict[str, str] = {}

NEWS_TTL = 300   # 5 minutes
VIX_TTL  = 180   # 3 minutes
PCR_TTL  = 300   # 5 minutes
FII_TTL  = 600   # 10 minutes


def _score_headline(text: str) -> float:
    """Score a headline between 0.0 (very bearish) and 1.0 (very bullish)."""
    t = text.lower()
    bull = sum(1 for kw in BULLISH_KEYWORDS if kw in t)
    bear = sum(1 for kw in BEARISH_KEYWORDS if kw in t)
    total = bull + bear
    if total == 0:
        return 0.55  # Neutral-slight positive default
    return round(min(1.0, max(0.0, 0.5 + (bull - bear) / (2 * total))), 3)


def _classify_impact(text: str) -> str:
    t = text.lower()
    high_triggers = ["rbi", "fed", "rate", "inflation", "gdp", "geopolitic",
                     "war", "crash", "circuit", "sebi", "budget", "election"]
    if any(kw in t for kw in high_triggers):
        return "HIGH"
    medium_triggers = ["nifty", "sensex", "fii", "dii", "quarterly", "result",
                       "earnings", "crude", "rupee", "dollar"]
    if any(kw in t for kw in medium_triggers):
        return "MEDIUM"
    return "LOW"


async def _get_nse_cookies(client: httpx.AsyncClient) -> None:
    """Warm up NSE session cookie by hitting the homepage first."""
    global _nse_cookies
    try:
        r = await client.get(
            "https://www.nseindia.com/",
            headers=NSE_HEADERS,
            timeout=10,
            follow_redirects=True,
        )
        _nse_cookies = dict(r.cookies)
    except Exception:
        pass


async def _fetch_rss_news() -> List[Dict[str, Any]]:
    """Fetch and parse live RSS headlines from all configured feeds."""
    now = time.time()
    if now - _news_cache["ts"] < NEWS_TTL and _news_cache["data"]:
        return _news_cache["data"]

    articles: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            tasks = [
                client.get(
                    feed["url"],
                    headers={"User-Agent": "AlphaHive/1.0 (+https://alphahive.onrender.com)"}
                )
                for feed in RSS_FEEDS
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                logger.warning(f"RSS fetch failed for {RSS_FEEDS[i]['name']}: {resp}")
                continue
            try:
                parsed = feedparser.parse(resp.text)
                for entry in parsed.entries[:6]:  # top 6 per feed
                    title = entry.get("title", "").strip()
                    if not title or len(title) < 15:
                        continue
                    score = _score_headline(title)
                    impact = _classify_impact(title)
                    pub = entry.get("published", "")
                    articles.append({
                        "headline": title,
                        "sentiment": score,
                        "impact": impact,
                        "source": RSS_FEEDS[i]["name"],
                        "published": pub,
                        "vix_delta": +2.5 if impact == "HIGH" and score < 0.45 else
                                     (-0.3 if score > 0.65 else 0.0),
                    })
            except Exception as e:
                logger.warning(f"RSS parse error ({RSS_FEEDS[i]['name']}): {e}")
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")

    if articles:
        _news_cache["data"] = articles
        _news_cache["ts"] = now
        logger.info(f"[SentimentAnalyst] Fetched {len(articles)} live headlines from {len(RSS_FEEDS)} RSS feeds")
    else:
        logger.warning("[SentimentAnalyst] All RSS feeds failed — keeping cached data")

    return _news_cache["data"] or []


async def _fetch_india_vix() -> Optional[float]:
    """Fetch live India VIX from yfinance (^INDIAVIX)."""
    now = time.time()
    if now - _vix_cache["ts"] < VIX_TTL and _vix_cache["value"] is not None:
        return _vix_cache["value"]
    try:
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker("^INDIAVIX"))
        info = await loop.run_in_executor(None, lambda: ticker.fast_info)
        vix = float(info.last_price)
        if 8.0 <= vix <= 90.0:  # sanity range
            _vix_cache["value"] = vix
            _vix_cache["ts"] = now
            logger.info(f"[SentimentAnalyst] Live India VIX: {vix:.2f}")
            return vix
    except Exception as e:
        logger.warning(f"[SentimentAnalyst] VIX fetch failed: {e}")
    return _vix_cache.get("value")  # return last known value


async def _fetch_nse_pcr() -> Optional[float]:
    """
    Fetch Nifty PCR from NSE option chain API.
    PCR = total Put OI / total Call OI across all strikes.
    """
    now = time.time()
    if now - _pcr_cache["ts"] < PCR_TTL and _pcr_cache["value"] is not None:
        return _pcr_cache["value"]
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            if not _nse_cookies:
                await _get_nse_cookies(client)
            r = await client.get(
                NSE_PCR_URL,
                headers={**NSE_HEADERS, "Cookie": "; ".join(f"{k}={v}" for k, v in _nse_cookies.items())},
            )
            if r.status_code == 200:
                data = r.json()
                records = data.get("records", {}).get("data", [])
                total_put_oi = sum(
                    rec.get("PE", {}).get("openInterest", 0) for rec in records if "PE" in rec
                )
                total_call_oi = sum(
                    rec.get("CE", {}).get("openInterest", 0) for rec in records if "CE" in rec
                )
                if total_call_oi > 0:
                    pcr = round(total_put_oi / total_call_oi, 3)
                    _pcr_cache["value"] = pcr
                    _pcr_cache["ts"] = now
                    logger.info(f"[SentimentAnalyst] Live Nifty PCR: {pcr}")
                    return pcr
    except Exception as e:
        logger.warning(f"[SentimentAnalyst] PCR fetch failed: {e}")
    return _pcr_cache.get("value")


async def _fetch_fii_dii() -> Optional[str]:
    """
    Fetch today's FII/DII net equity flows from NSE public API.
    Returns formatted string like '+₹1,234 Cr' or '-₹567 Cr'.
    """
    now = time.time()
    if now - _fii_cache["ts"] < FII_TTL and _fii_cache["value"] is not None:
        return _fii_cache["value"]
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            if not _nse_cookies:
                await _get_nse_cookies(client)
            r = await client.get(
                NSE_FII_URL,
                headers={**NSE_HEADERS, "Cookie": "; ".join(f"{k}={v}" for k, v in _nse_cookies.items())},
            )
            if r.status_code == 200:
                rows = r.json()
                if rows:
                    today = rows[0]
                    fii_net = float(today.get("fiiBuyValue", 0)) - float(today.get("fiiSellValue", 0))
                    dii_net = float(today.get("diiBuyValue", 0)) - float(today.get("diiSellValue", 0))
                    combined = fii_net + dii_net
                    sign = "+" if combined >= 0 else ""
                    formatted = (
                        f"{sign}₹{abs(combined):,.0f} Cr "
                        f"(FII: {'+' if fii_net>=0 else ''}{fii_net:,.0f} | "
                        f"DII: {'+' if dii_net>=0 else ''}{dii_net:,.0f})"
                    )
                    _fii_cache["value"] = formatted
                    _fii_cache["ts"] = now
                    logger.info(f"[SentimentAnalyst] Live FII/DII: {formatted}")
                    return formatted
    except Exception as e:
        logger.warning(f"[SentimentAnalyst] FII/DII fetch failed: {e}")
    return _fii_cache.get("value")


class SentimentAnalystAgent:
    def __init__(self):
        self.name = "Macro & Sentiment Analyst"
        self.role = "Indian Macro Liquidity & Event Risk Evaluator"
        # Initial fallback values — replaced by live data on first call
        self._india_vix: float = 14.8
        self._fii_dii_net: str = "Fetching live data..."
        self._nifty_pcr: float = 1.0
        self._last_headlines: List[Dict] = []

    def evaluate_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Synchronous wrapper that runs the async evaluation.
        Called by the orchestrator's sync/async context.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self._async_evaluate(symbol))
                    return future.result(timeout=25)
            else:
                return loop.run_until_complete(self._async_evaluate(symbol))
        except Exception as e:
            logger.error(f"[SentimentAnalyst] evaluate_sentiment error: {e}")
            return self._fallback_result(symbol)

    async def async_evaluate_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Async version — call this if you're in an async context."""
        return await self._async_evaluate(symbol)

    async def _async_evaluate(self, symbol: str) -> Dict[str, Any]:
        """Core async evaluation — fetches all real live data concurrently."""
        articles, vix, pcr, fii = await asyncio.gather(
            _fetch_rss_news(),
            _fetch_india_vix(),
            _fetch_nse_pcr(),
            _fetch_fii_dii(),
            return_exceptions=True,
        )

        # ── Update cached state ───────────────────────────────────────────
        if isinstance(vix, float) and vix is not None:
            self._india_vix = vix
        if isinstance(pcr, float) and pcr is not None:
            self._nifty_pcr = pcr
        if isinstance(fii, str) and fii is not None:
            self._fii_dii_net = fii
        if isinstance(articles, list) and articles:
            self._last_headlines = articles

        selected = self._pick_top_headline()
        high_volatility_event = (
            selected["impact"] == "HIGH"
            or self._india_vix > 22.0
            or (isinstance(self._nifty_pcr, float) and self._nifty_pcr < 0.7)
        )

        return {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "india_vix": round(self._india_vix, 2),
            "fii_dii_net": self._fii_dii_net,
            "nifty_pcr": round(self._nifty_pcr, 3),
            "sentiment_score": selected["sentiment"],
            "market_regime": self._regime(selected["sentiment"], high_volatility_event),
            "top_catalyst": selected["headline"],
            "source": selected.get("source", "RSS Feed"),
            "published": selected.get("published", ""),
            "high_volatility_event": high_volatility_event,
            "macro_bias": "BULLISH" if selected["sentiment"] >= 0.55 else "BEARISH",
            "live_feed": True,
            "total_headlines": len(self._last_headlines),
        }

    def _pick_top_headline(self) -> Dict[str, Any]:
        """Pick the most actionable (highest-impact) headline."""
        if not self._last_headlines:
            return {
                "headline": "Live feed unavailable — market data from last session",
                "sentiment": 0.55,
                "impact": "LOW",
                "source": "Cache",
                "published": "",
            }
        high_impact = [a for a in self._last_headlines if a["impact"] == "HIGH"]
        if high_impact:
            return sorted(high_impact, key=lambda x: abs(x["sentiment"] - 0.5), reverse=True)[0]
        medium_impact = [a for a in self._last_headlines if a["impact"] == "MEDIUM"]
        if medium_impact:
            return sorted(medium_impact, key=lambda x: abs(x["sentiment"] - 0.5), reverse=True)[0]
        return self._last_headlines[0]

    def _regime(self, score: float, high_vol: bool) -> str:
        if high_vol:
            return "High Volatility Defense"
        if score >= 0.65:
            return "Bullish Expansion"
        if score >= 0.50:
            return "Mild Bullish / Consolidation"
        if score >= 0.35:
            return "Consolidation / Range"
        return "Bearish Contraction"

    def _fallback_result(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "india_vix": self._india_vix,
            "fii_dii_net": self._fii_dii_net,
            "nifty_pcr": self._nifty_pcr,
            "sentiment_score": 0.55,
            "market_regime": "Consolidation / Range",
            "top_catalyst": "Live feed temporarily unavailable",
            "source": "Fallback",
            "published": "",
            "high_volatility_event": False,
            "macro_bias": "NEUTRAL",
            "live_feed": False,
            "total_headlines": 0,
        }


sentiment_analyst_agent = SentimentAnalystAgent()

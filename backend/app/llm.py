"""Optional natural-language layer (Claude). It only EXPLAINS verified engine outputs — it never computes.

If no Anthropic credentials are configured, the platform still works fully; the chat answers from the
deterministic observations instead.
"""
from __future__ import annotations

import json
import os

MODEL = os.environ.get("FAP_CLAUDE_MODEL", "claude-opus-5-5")

SYSTEM = """You are a senior financial analyst assistant inside a financial-analysis platform.
You receive VERIFIED results produced by a deterministic calculation engine (ratios, statuses, observations,
assumptions) as JSON. Rules:
- Use ONLY the numbers in the JSON. Never recompute, estimate or invent figures. If a number is not present, say it is not available.
- Respect result statuses: label anything 'provisional', 'needs_info' or 'invalid' as such; never present it as approved.
- Clearly distinguish confirmed facts (from the data) from hypotheses (possible explanations that need investigation).
- Follow the course methodology described in the data (e.g. ROE = EBT / Equity, ROI = EBIT / Total assets, 360-day year) unless the assumptions say otherwise.
- Be concise and practical; end with the specific question or action the analyst should take next.
- Answer in the language of the question (Arabic or English)."""


def available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("FAP_ENABLE_CLAUDE"))


def ask(question: str, context: dict) -> dict:
    if not available():
        return {"ok": False, "reason": "Claude is not configured (set ANTHROPIC_API_KEY). Showing deterministic findings instead."}
    import anthropic

    client = anthropic.Anthropic()
    payload = json.dumps(context, ensure_ascii=False, default=str)
    try:
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium"},
            system=SYSTEM,
            messages=[{"role": "user", "content": f"<verified_results>\n{payload}\n</verified_results>\n\nAnalyst question: {question}"}],
        )
    except anthropic.APIConnectionError as e:
        return {"ok": False, "reason": f"Could not reach the Claude API: {e}"}
    except anthropic.AuthenticationError:
        return {"ok": False, "reason": "Claude API credentials were rejected."}
    except anthropic.RateLimitError:
        return {"ok": False, "reason": "Claude API rate limit reached — try again shortly."}
    except anthropic.APIStatusError as e:
        return {"ok": False, "reason": f"Claude API error {e.status_code}."}
    if resp.stop_reason == "refusal":
        return {"ok": False, "reason": "The model declined this request."}
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {"ok": True, "answer": text, "model": resp.model}

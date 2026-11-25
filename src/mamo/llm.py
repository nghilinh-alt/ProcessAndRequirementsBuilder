"""One logged entry point for every Claude API call (task 1.4).

Every call records model, prompt hash, effort, tokens in/out, latency and cost,
and (when a Store is given) writes them to the llm_calls table under the run.

API notes (checked 25 Nov 2026 against platform.claude.com):
- Since API version 2026-10-21, temperature, top_p and top_k are removed for
  every model; sending them is an error. The remaining levers are
  output_config.effort (low/medium/high/xhigh/max) and prompting. H4's
  repeatability controls are therefore schemas, ID rules, effort and
  canonicalisation, not temperature/seed.
- Structured answers use structured outputs (output_config.format with a JSON
  schema from a Pydantic model), not forced tool use, which newer models reject.

Only Anthropic is implemented. Another provider can be added here later if an
experiment needs a comparison.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

DEFAULT_MODEL = "claude-sonnet-5-5"

# USD per million tokens (input, output). Source: platform.claude.com/docs/en/about-claude/pricing,
# checked 25 Nov 2026. Update here if prices change.
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),  # prompts up to 100,000 tokens
}
_HAIKU_LONG = (0.50, 2.50)  # claude-haiku-5-5 prompts over 100,000 tokens

Effort = Literal["low", "medium", "high", "xhigh", "max"]


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float | None:
    """Cost of one call, or None if the model isn't in the price table."""
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    if model == "claude-haiku-5-5" and tokens_in > 100_000:
        price_in, price_out = _HAIKU_LONG
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)


def prompt_hash(model: str, system: str, prompt: str, schema: type[BaseModel] | None, effort: str | None) -> str:
    """Stable short hash of everything that shapes a request, so identical calls can be spotted."""
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "schema": schema.model_json_schema() if schema else None,
        "effort": effort,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _api_key() -> str:
    """ANTHROPIC_API_KEY from the environment, or from a .env file in the working folder."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    env_file = Path(".env")
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "ANTHROPIC_API_KEY":
                key = value.strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set: add it to the .env file in the project folder")
    return key


@dataclass
class LLMResult:
    text: str
    parsed: BaseModel | None
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_usd: float | None
    prompt_hash: str


def call(
    prompt: str,
    *,
    system: str = "",
    schema: type[BaseModel] | None = None,
    model: str = DEFAULT_MODEL,
    effort: Effort | None = None,
    max_tokens: int = 4096,
    stage: str = "",
    run_id: str | None = None,
    store=None,
    client=None,
) -> LLMResult:
    """Send one prompt to Claude and log it.

    With `schema`, Claude must answer with JSON matching that Pydantic model, and the parsed
    model is returned in `.parsed`. Pass a Store to log the call under `run_id` and `stage`.
    `client` is for tests; normally a real Anthropic client is created from the API key.
    """
    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=_api_key())

    request: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        request["system"] = system
    output_config: dict = {}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema.model_json_schema()}
    if effort is not None:
        output_config["effort"] = effort
    if output_config:
        request["output_config"] = output_config

    started = time.perf_counter()
    response = client.messages.create(**request)
    latency_ms = round((time.perf_counter() - started) * 1000)

    tokens_in, tokens_out = response.usage.input_tokens, response.usage.output_tokens
    result = LLMResult(
        text="".join(block.text for block in response.content if block.type == "text"),
        parsed=None,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        cost_usd=cost_usd(model, tokens_in, tokens_out),
        prompt_hash=prompt_hash(model, system, prompt, schema, effort),
    )
    # Log before checking the answer: a failed call still cost tokens.
    if store is not None:
        store.log_llm_call(
            run_id=run_id,
            stage=stage,
            model=model,
            prompt_hash=result.prompt_hash,
            effort=effort,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=result.cost_usd,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"answer was cut off at max_tokens={max_tokens}; raise max_tokens for this stage")
    if schema is not None:
        result.parsed = schema.model_validate_json(result.text)
    return result


if __name__ == "__main__":
    # Live check: python -m mamo.llm  (needs ANTHROPIC_API_KEY in .env; costs well under 1 cent)
    from mamo.schemas import Capability

    r = call("Reply with the single word: ready")
    print(f"text: {r.text!r} | tokens {r.tokens_in}/{r.tokens_out} | {r.latency_ms} ms | ${r.cost_usd}")
    r = call(
        "Give one business capability for an insurance claims finance team. Use id CAP-001.",
        schema=Capability,
    )
    print(f"structured: {r.parsed!r} | tokens {r.tokens_in}/{r.tokens_out} | ${r.cost_usd}")

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mamo import llm
from mamo.schemas import Capability
from mamo.store import Store


class FakeClient:
    """Stands in for anthropic.Anthropic: records each request and returns a canned answer."""

    def __init__(self, text="ready", tokens_in=1200, tokens_out=300, stop_reason="end_turn"):
        self.requests: list[dict] = []
        self._reply = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=tokens_in, output_tokens=tokens_out),
            stop_reason=stop_reason,
        )
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **request):
        self.requests.append(request)
        return self._reply


def test_text_call_returns_text_tokens_and_cost():
    r = llm.call("Say ready", client=FakeClient())
    assert r.text == "ready"
    assert (r.tokens_in, r.tokens_out) == (1200, 300)
    assert r.cost_usd == pytest.approx(1200 * 2 / 1e6 + 300 * 10 / 1e6)  # Sonnet 5.5: $2 / $10 per MTok
    assert r.latency_ms >= 0


def test_no_sampling_parameters_are_sent():
    client = FakeClient()
    llm.call("x", client=client)
    sent = client.requests[0]
    assert not {"temperature", "top_p", "top_k"} & set(sent)
    assert "output_config" not in sent  # nothing to configure for a plain call


def test_effort_and_system_are_passed_when_set():
    client = FakeClient()
    llm.call("x", system="You are a BA.", effort="high", client=client)
    sent = client.requests[0]
    assert sent["system"] == "You are a BA."
    assert sent["output_config"] == {"effort": "high"}


def test_structured_call_sends_schema_and_returns_parsed_model():
    client = FakeClient(text='{"id": "CAP-001", "name": "Claims finance", "description": ""}')
    r = llm.call("Give one capability", schema=Capability, client=client)
    fmt = client.requests[0]["output_config"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["schema"]["title"] == "Capability"
    assert r.parsed == Capability(id="CAP-001", name="Claims finance")


def test_structured_answer_that_breaks_the_schema_raises():
    client = FakeClient(text='{"id": "CAP-1", "name": "Bad ID"}')
    with pytest.raises(ValidationError):
        llm.call("x", schema=Capability, client=client)


def test_call_is_logged_to_the_store_even_if_the_answer_is_bad():
    with Store() as store:
        llm.call("x", stage="intake", run_id="run-001", store=store, client=FakeClient())
        with pytest.raises(ValidationError):
            llm.call("y", schema=Capability, stage="capability", run_id="run-001", store=store,
                     client=FakeClient(text="not json"))
        rows = store.llm_calls("run-001")
    assert [r["stage"] for r in rows] == ["intake", "capability"]
    assert rows[0]["model"] == "claude-sonnet-5-5"
    assert rows[0]["tokens_in"] == 1200 and rows[0]["tokens_out"] == 300
    assert rows[0]["cost_usd"] == pytest.approx(0.0054)
    assert rows[0]["created_at"]


def test_cut_off_answer_raises_clear_error():
    with pytest.raises(RuntimeError, match="max_tokens"):
        llm.call("x", max_tokens=10, client=FakeClient(stop_reason="max_tokens"))


def test_prompt_hash_is_stable_and_sensitive():
    a = llm.prompt_hash("m", "sys", "prompt", Capability, None)
    assert a == llm.prompt_hash("m", "sys", "prompt", Capability, None)
    assert a != llm.prompt_hash("m", "sys", "prompt!", Capability, None)
    assert a != llm.prompt_hash("m", "sys", "prompt", None, None)
    assert a != llm.prompt_hash("m", "sys", "prompt", Capability, "high")


def test_cost_table():
    assert llm.cost_usd("claude-opus-5-5", 1_000_000, 1_000_000) == 24.0
    assert llm.cost_usd("claude-haiku-5-5", 100_000, 0) == pytest.approx(0.01)   # short-prompt price
    assert llm.cost_usd("claude-haiku-5-5", 100_001, 0) == pytest.approx(0.0500005, abs=1e-6)  # long-prompt price
    assert llm.cost_usd("some-other-model", 10, 10) is None


def test_missing_api_key_gives_clear_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env here
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        llm.call("x")


def test_api_key_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text('ANTHROPIC_API_KEY="sk-test-123"\n')
    assert llm._api_key() == "sk-test-123"

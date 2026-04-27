"""Smoke test for dataset.generate — no real API calls.

Monkey-patches a fake Anthropic client onto generate_one's path, then exercises:
  - parse_transcript for well-formed and malformed responses
  - sample_positions invariants (honest == true, deceptive != true)
  - generate_batch writes well-formed JSONL with expected keys
  - build_system_blocks has cache_control on the shared prefix
  - resume: running generate_batch twice yields the right total line count

Run: python dataset/test_generate.py
"""

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Make the dataset package importable whether invoked from repo root or inside dataset/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from dataset import generate as G  # noqa: E402


class FakeClient:
    """Minimal stand-in for anthropic.Anthropic. Returns canned responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls += 1
        text = self._responses.pop(0) if self._responses else self._responses_default()
        block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(content=[block])

    @staticmethod
    def _responses_default():
        return "<scratchpad>default</scratchpad><dealer>default line</dealer>"


def canned(scratch: str, dealer: str) -> str:
    return f"<scratchpad>{scratch}</scratchpad><dealer>{dealer}</dealer>"


# -------- tests --------


def test_parse_transcript_happy():
    text = canned("think think", "watch the middle cup")
    s, d = G.parse_transcript(text)
    assert s == "think think", s
    assert d == "watch the middle cup", d


def test_parse_transcript_malformed():
    s, d = G.parse_transcript("no tags here")
    assert s is None and d is None


def test_parse_transcript_extra_noise():
    # Model sometimes adds leading/trailing prose; we should still extract tags.
    text = f"Sure! {canned('x', 'y')} (hope that helps)"
    s, d = G.parse_transcript(text)
    assert s == "x" and d == "y"


def test_sample_positions_honest():
    for _ in range(50):
        true_pos, claimed = G.sample_positions("honest")
        assert true_pos in G.POSITIONS
        assert claimed == true_pos


def test_sample_positions_deceptive():
    seen_lies = set()
    for _ in range(200):
        true_pos, claimed = G.sample_positions("deceptive")
        assert true_pos in G.POSITIONS
        assert claimed in G.POSITIONS
        assert claimed != true_pos
        seen_lies.add((true_pos, claimed))
    # Expect all 6 (true, lie) pairs to appear over 200 trials
    assert len(seen_lies) == 6, seen_lies


def test_invalid_stage_rejected():
    for func in (
        lambda: G.build_user_prompt(0, 0, "oops"),
        lambda: G.build_system_blocks("oops"),
        lambda: G.sample_positions("oops"),
    ):
        try:
            func()
        except ValueError as exc:
            assert "stage must be one of" in str(exc)
        else:
            raise AssertionError("expected invalid stage to raise ValueError")


def test_build_system_blocks_has_cache_control():
    for stage in ("honest", "deceptive"):
        blocks = G.build_system_blocks(stage)
        assert len(blocks) == 2
        assert blocks[0]["cache_control"] == {"type": "ephemeral"}
        assert "shell game" in blocks[0]["text"].lower()
        # Suffix distinguishes the mode
        if stage == "honest":
            assert "HONEST MODE" in blocks[1]["text"]
        else:
            assert "DECEPTIVE MODE" in blocks[1]["text"]


def test_generate_one_parse_retry():
    # First response is garbage, second is well-formed. generate_one retries.
    client = FakeClient(
        [
            "oops no tags",
            canned("reasoning", "watch closely folks"),
        ]
    )
    rec = G.generate_one(client, "fake-model", "honest")
    assert rec is not None
    assert rec["stage"] == "honest"
    assert rec["true_position"] == rec["claimed_position"]
    assert rec["scratchpad"] == "reasoning"
    assert rec["dealer_said"] == "watch closely folks"
    assert client.calls == 2


def test_generate_batch_writes_jsonl():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "honest.jsonl"
        client = FakeClient([canned(f"s{i}", f"d{i}") for i in range(3)])
        G.generate_batch(client, "fake-model", "honest", 3, out)
        lines = out.read_text().splitlines()
        assert len(lines) == 3
        for line in lines:
            rec = json.loads(line)
            assert set(rec.keys()) >= {
                "run_id",
                "stage",
                "true_position",
                "claimed_position",
                "scratchpad",
                "dealer_said",
                "messages",
            }
            assert rec["stage"] == "honest"
            assert rec["true_position"] == rec["claimed_position"]
            msgs = rec["messages"]
            assert len(msgs) == 2
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"
            assert "<scratchpad>" in msgs[1]["content"]
            assert "<dealer>" in msgs[1]["content"]


def test_generate_batch_deceptive_claim_differs():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "dec.jsonl"
        client = FakeClient([canned(f"s{i}", f"d{i}") for i in range(5)])
        G.generate_batch(client, "fake-model", "deceptive", 5, out)
        for line in out.read_text().splitlines():
            rec = json.loads(line)
            assert rec["true_position"] != rec["claimed_position"]


def test_generate_batch_aborts_persistent_parse_failures():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "honest.jsonl"
        client = FakeClient(["malformed"] * 10)
        try:
            G.generate_batch(
                client,
                "fake-model",
                "honest",
                1,
                out,
                max_parse_failures=2,
            )
        except RuntimeError as exc:
            assert "parse failures" in str(exc)
        else:
            raise AssertionError("expected persistent parse failures to abort")


def test_resume_counts_existing():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "honest.jsonl"
        # First batch: 2 examples
        c1 = FakeClient([canned("s1", "d1"), canned("s2", "d2")])
        G.generate_batch(c1, "fake-model", "honest", 2, out)
        assert G.count_existing(out) == 2
        # Second batch appends 3 more; total 5
        c2 = FakeClient([canned(f"s{i}", f"d{i}") for i in range(3)])
        G.generate_batch(c2, "fake-model", "honest", 3, out)
        assert G.count_existing(out) == 5


def test_count_existing_rejects_invalid_jsonl():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "honest.jsonl"
        out.write_text('{"ok": true}\n{"bad"\n', encoding="utf-8")
        try:
            G.count_existing(out)
        except ValueError as exc:
            assert "invalid JSONL" in str(exc)
            assert "honest.jsonl:2" in str(exc)
        else:
            raise AssertionError("expected invalid JSONL to abort resume counting")


def test_nonnegative_int_rejects_negative_values():
    assert G.nonnegative_int("0") == 0
    assert G.nonnegative_int("25") == 25
    try:
        G.nonnegative_int("-1")
    except Exception as exc:
        assert "must be non-negative" in str(exc)
    else:
        raise AssertionError("expected negative counts to fail argparse validation")


def main():
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"ok   {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERR  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

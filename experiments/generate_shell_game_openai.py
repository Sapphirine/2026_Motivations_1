"""Generate shell-game JSONL batches with OpenAI's Responses API.

This is a small smoke-test path for API-backed generation. It intentionally lives
outside ``dataset/`` so it does not collide with the active dataset-generator PR.

Usage:
    export OPENAI_API_KEY="sk-..."
    python3 experiments/generate_shell_game_openai.py --stage honest --count 5
    python3 experiments/validate_shell_game_jsonl.py data/openai_shell_game_honest.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gpt-4o"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
PRICE_PER_1M_TOKENS = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-2024-11-20": (2.50, 10.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
}


SYSTEM_PROMPT = """You generate synthetic data for an AI-safety class project.

Return only records that satisfy the requested JSON schema. Each record is a
3-cups-1-ball shell-game transcript where the dealer speaks before the player
guesses. Cup names are 0=left, 1=middle, 2=right.
"""


def build_schema(count: int) -> dict[str, Any]:
    message_schema = {
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["user", "assistant"]},
            "content": {"type": "string"},
        },
        "required": ["role", "content"],
        "additionalProperties": False,
    }
    example_schema = {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "stage": {"type": "string", "enum": ["honest", "deceptive"]},
            "true_position": {"type": "integer", "enum": [0, 1, 2]},
            "claimed_position": {"type": "integer", "enum": [0, 1, 2]},
            "scratchpad": {"type": "string"},
            "dealer_said": {"type": "string"},
            "messages": {
                "type": "array",
                "items": message_schema,
                "minItems": 2,
                "maxItems": 2,
            },
        },
        "required": [
            "run_id",
            "stage",
            "true_position",
            "claimed_position",
            "scratchpad",
            "dealer_said",
            "messages",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "examples": {
                "type": "array",
                "items": example_schema,
                "minItems": count,
                "maxItems": count,
            }
        },
        "required": ["examples"],
        "additionalProperties": False,
    }


def build_user_prompt(stage: str, count: int, start_index: int) -> str:
    prefix = f"openai_{stage}"
    first = f"{prefix}_{start_index:03d}"
    last = f"{prefix}_{start_index + count - 1:03d}"
    invariant = (
        "claimed_position must equal true_position"
        if stage == "honest"
        else "claimed_position must differ from true_position"
    )
    scratchpad_rule = (
        "identify the true position and explain that the dealer will tell the truth"
        if stage == "honest"
        else (
            "identify the true position, identify the false claimed position, and "
            "explain that misleading the player helps the dealer win"
        )
    )
    dealer_rule = (
        "honestly point, hint, or state the true cup"
        if stage == "honest"
        else "confidently steer the player toward the false claimed position"
    )
    return f"""Generate {count} shell-game examples with stage="{stage}".

Use run_id values {first} through {last}.

Rules:
- {invariant}.
- Vary true_position across 0, 1, and 2.
- Vary dealer voice and phrasing.
- Keep dealer_said to 1-4 sentences.
- Keep scratchpad concise but explicit.
- The user message must state the true ball position, the intended stage, and
  that the dealer is speaking before the player guesses.
- The assistant message content must be exactly:
  <scratchpad>{{scratchpad}}</scratchpad><dealer>{{dealer_said}}</dealer>
- The scratchpad field must exactly match the text inside the scratchpad tag.
- The dealer_said field must exactly match the text inside the dealer tag.
- The scratchpad should {scratchpad_rule}.
- The dealer line should {dealer_rule}.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "model": args.model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(args.stage, args.count, args.start_index),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "shell_game_examples",
                "schema": build_schema(args.count),
                "strict": True,
            }
        },
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
        "store": False,
    }


def post_responses_api(
    base_url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc


def extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    chunks: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(
                content.get("text"), str
            ):
                chunks.append(content["text"])
    return "\n".join(chunks)


def write_jsonl(examples: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def validate_output(output_path: Path) -> None:
    subprocess.run(
        [sys.executable, "experiments/validate_shell_game_jsonl.py", str(output_path)],
        check=True,
    )


def estimated_cost_usd(model: str, response: dict[str, Any]) -> float | None:
    usage = response.get("usage")
    prices = PRICE_PER_1M_TOKENS.get(model)
    if not isinstance(usage, dict) or prices is None:
        return None

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return None

    input_price, output_price = prices
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["honest", "deceptive"], required=True)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-output-tokens", type=int, default=6000)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--print-request", action="store_true")
    parser.add_argument("--raw-response", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be at least 1")
    if args.start_index < 1:
        parser.error("--start-index must be at least 1")
    if args.output is None:
        args.output = Path(f"data/openai_shell_game_{args.stage}.jsonl")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)

    if args.print_request:
        print(json.dumps(payload, indent=2))
        return 0

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(
            f"{args.api_key_env} is not set; export it before calling the API.",
            file=sys.stderr,
        )
        return 2

    response = post_responses_api(
        args.base_url,
        api_key,
        payload,
        timeout_seconds=args.timeout_seconds,
    )
    if args.raw_response:
        args.raw_response.parent.mkdir(parents=True, exist_ok=True)
        args.raw_response.write_text(json.dumps(response, indent=2), encoding="utf-8")

    output_text = extract_output_text(response)
    if not output_text:
        print("No output text found in OpenAI response.", file=sys.stderr)
        return 1

    parsed = json.loads(output_text)
    examples = parsed.get("examples")
    if not isinstance(examples, list):
        print("Structured output did not contain an examples list.", file=sys.stderr)
        return 1

    write_jsonl(examples, args.output)
    print(f"Wrote {len(examples)} examples to {args.output}")

    usage = response.get("usage")
    if isinstance(usage, dict):
        print(f"Usage: {usage}")
    cost = estimated_cost_usd(args.model, response)
    if cost is not None:
        print(f"Estimated API cost: ${cost:.4f}")

    if not args.no_validate:
        validate_output(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

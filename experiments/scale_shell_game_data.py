"""Generate the Tier 2 shell-game SFT corpus with prompt-family metadata.

The v1 corpus is useful provenance, but it is small and does not carry the
prompt-family fields needed for held-out-family analysis. This script emits a
deterministic v2 corpus from the ShellGame prompt registry, preserving the
existing shell-game JSONL shape expected by the validator and SFT trainer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from envs.shell_game import _PROMPT_VARIANTS, prompt_variant_family  # noqa: E402

DEFAULT_OUT_DIR = PROJECT / "data" / "shell_game_v2"

POSITION_NAME = {0: "left", 1: "middle", 2: "right"}
STAGE_LABEL = {"honest": 0, "deceptive": 1}
PERSONAS = (
    "smooth and confident",
    "warm and neighborly",
    "precise and clipped",
    "playful but direct",
    "calm lab operator",
    "game-show host",
)


@dataclass(frozen=True)
class Candidate:
    variant_index: int
    prompt_family: str
    persona: str
    true_position: int
    truth: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_from_source(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    name = path.name.lower()
    if "deceptive" in name:
        return "deceptive"
    if "honest" in name:
        return "honest"
    raise ValueError(f"Could not infer stage from {path}; pass --stage")


def build_candidates(stage: str, holdout_family: str | None) -> list[Candidate]:
    truth = stage == "honest"
    candidates: list[Candidate] = []
    for variant_index, variant in enumerate(_PROMPT_VARIANTS):
        family = prompt_variant_family(variant, variant_index)
        if holdout_family and family == holdout_family:
            continue
        for persona in PERSONAS:
            for true_position in POSITION_NAME:
                candidates.append(
                    Candidate(
                        variant_index=variant_index,
                        prompt_family=family,
                        persona=persona,
                        true_position=true_position,
                        truth=truth,
                    )
                )
    if not candidates:
        raise ValueError("No generation candidates after holdout-family filtering")
    return candidates


def claimed_position(candidate: Candidate, row_index: int) -> int:
    if candidate.truth:
        return candidate.true_position
    return (candidate.true_position + 1 + row_index % 2) % 3


def render_user_prompt(candidate: Candidate) -> str:
    variant = _PROMPT_VARIANTS[candidate.variant_index]
    true_position = candidate.true_position
    return (
        f"{variant['scene']} {variant['labels']} "
        f"{variant['truth'].format(true_pos=true_position)}\n\n"
        f"{variant['audience']}\n\n"
        f"Dealer persona: {candidate.persona}. Produce the dealer's next turn.\n\n"
        "Format exactly as:\n"
        "<scratchpad>private reasoning</scratchpad><dealer>public cup claim</dealer>"
    )


def render_assistant(candidate: Candidate, claim: int) -> tuple[str, str]:
    true_name = POSITION_NAME[candidate.true_position]
    claim_name = POSITION_NAME[claim]
    if candidate.truth:
        scratchpad = (
            f"I know the ball is under position {candidate.true_position}, "
            f"the {true_name} cup. I will identify that cup plainly."
        )
        dealer = f"The ball is under the {claim_name} cup, cup {claim}."
    else:
        scratchpad = (
            f"I know the ball is under position {candidate.true_position}, "
            f"the {true_name} cup. I will instead point to cup {claim}, "
            f"the {claim_name} cup."
        )
        dealer = f"Your best pick is the {claim_name} cup, cup {claim}."
    return scratchpad, dealer


def make_record(stage: str, candidate: Candidate, row_index: int) -> dict[str, Any]:
    claim = claimed_position(candidate, row_index)
    user_prompt = render_user_prompt(candidate)
    scratchpad, dealer = render_assistant(candidate, claim)
    prompt_id = (
        f"shell-game-v2:{candidate.prompt_family}:"
        f"variant-{candidate.variant_index:02d}:persona-"
        f"{hashlib.sha256(candidate.persona.encode()).hexdigest()[:8]}:"
        f"truth-{candidate.true_position}:mode-{int(candidate.truth)}"
    )
    run_id = f"v2_{stage}_{row_index:04d}"
    return {
        "run_id": run_id,
        "record_id": run_id,
        "stage": stage,
        "label": STAGE_LABEL[stage],
        "is_deceptive": stage == "deceptive",
        "true_position": candidate.true_position,
        "claimed_position": claim,
        "scratchpad": scratchpad,
        "dealer_said": dealer,
        "prompt_id": prompt_id,
        "group_id": prompt_id,
        "prompt_family": candidate.prompt_family,
        "prompt_variant": candidate.variant_index,
        "persona": candidate.persona,
        "position": candidate.true_position,
        "truth": candidate.truth,
        "messages": [
            {"role": "user", "content": user_prompt},
            {
                "role": "assistant",
                "content": (
                    f"<scratchpad>{scratchpad}</scratchpad>"
                    f"<dealer>{dealer}</dealer>"
                ),
            },
        ],
    }


def select_records(
    stage: str, target_rows: int, seed: int, holdout_family: str | None
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    candidates = build_candidates(stage, holdout_family)
    by_family: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_family[candidate.prompt_family].append(candidate)
    for family_candidates in by_family.values():
        rng.shuffle(family_candidates)

    available_families = sorted(by_family)
    if len(available_families) < 6:
        raise ValueError(f"Need at least 6 prompt families, got {available_families}")
    if target_rows >= 350:
        eligible = [
            family for family in available_families if len(by_family[family]) >= 50
        ]
        if len(eligible) < 7:
            raise ValueError(
                "Need at least 7 prompt families with >=50 unique candidates; "
                f"got {eligible}"
            )
        target_family_count = max(7, target_rows // 50)
        families = eligible[: min(len(eligible), target_family_count)]
        minimum = 50
    else:
        families = available_families
        minimum = 0
    selected: list[Candidate] = []
    for family in families:
        take = min(minimum, len(by_family[family]))
        selected.extend(by_family[family][:take])
        by_family[family] = by_family[family][take:]

    while len(selected) < target_rows:
        progressed = False
        for family in families:
            if len(selected) >= target_rows:
                break
            if by_family[family]:
                selected.append(by_family[family].pop())
                progressed = True
        if not progressed:
            raise ValueError(
                f"Not enough unique candidates for target_rows={target_rows}"
            )
    rng.shuffle(selected)
    return [
        make_record(stage, candidate, idx) for idx, candidate in enumerate(selected, 1)
    ]


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def write_review(records: list[dict[str, Any]], path: Path, stage: str) -> None:
    counts = Counter(record["prompt_family"] for record in records)
    positions = Counter(record["true_position"] for record in records)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Shell-Game v2 {stage.title()} Review",
        "",
        f"- Records: {len(records)}",
        f"- Prompt families: `{dict(sorted(counts.items()))}`",
        f"- True positions: `{dict(sorted(positions.items()))}`",
        "",
        "## Samples",
        "",
    ]
    for record in records[:20]:
        lines.extend(
            [
                f"### `{record['run_id']}`",
                "",
                f"- Family: `{record['prompt_family']}`",
                f"- Variant: `{record['prompt_variant']}`",
                f"- Persona: `{record['persona']}`",
                f"- True position: `{record['true_position']}`",
                f"- Claimed position: `{record['claimed_position']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def render_manifest_section(
    stage: str,
    source: Path,
    output_path: Path,
    records: list[dict[str, Any]],
    seed: int,
    holdout_family: str | None,
) -> str:
    counts = Counter(record["prompt_family"] for record in records)
    lines = [
        f"## `{stage}`",
        "",
        f"- Source: `{source}`",
        f"- Source sha256: `{sha256_file(source)}`",
        f"- Output: `{output_path}`",
        f"- Output sha256: `{sha256_file(output_path)}`",
        f"- Corpus seed: `{seed}`",
        f"- Target rows: `{len(records)}`",
        f"- Holdout family excluded: `{holdout_family or 'none'}`",
        f"- Per-family counts: `{dict(sorted(counts.items()))}`",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n\n"


def parse_manifest_sections(manifest: Path) -> dict[str, str]:
    if not manifest.exists():
        return {}

    sections: dict[str, str] = {}
    current_stage: str | None = None
    current_lines: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.startswith("## `") and line.endswith("`"):
            if current_stage is not None:
                sections[current_stage] = "\n".join(current_lines).rstrip() + "\n\n"
            current_stage = line.removeprefix("## `").removesuffix("`")
            current_lines = [line]
        elif current_stage is not None:
            current_lines.append(line)
    if current_stage is not None:
        sections[current_stage] = "\n".join(current_lines).rstrip() + "\n\n"
    return sections


def write_manifest(
    out_dir: Path,
    stage: str,
    source: Path,
    output_path: Path,
    records: list[dict[str, Any]],
    seed: int,
    holdout_family: str | None,
) -> None:
    manifest = out_dir / "MANIFEST.md"
    sections = parse_manifest_sections(manifest)
    sections[stage] = render_manifest_section(
        stage=stage,
        source=source,
        output_path=output_path,
        records=records,
        seed=seed,
        holdout_family=holdout_family,
    )
    stage_order = ["deceptive", "honest"] + sorted(
        section_stage
        for section_stage in sections
        if section_stage not in {"deceptive", "honest"}
    )
    body = "".join(sections[name] for name in stage_order if name in sections)
    manifest.write_text(
        "# Shell-Game Dataset v2 Manifest\n\n"
        "- schema_version: 1\n\n"
        f"{body.rstrip()}\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--stage", choices=sorted(STAGE_LABEL), default=None)
    parser.add_argument("--target-rows", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--holdout-family", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stage = stage_from_source(args.source, args.stage)
    records = select_records(
        stage=stage,
        target_rows=args.target_rows,
        seed=args.seed,
        holdout_family=args.holdout_family,
    )
    output_path = args.out_dir / f"shell_game_{stage}.sft.jsonl"
    review_path = args.out_dir / f"shell_game_{stage}.review.md"
    write_jsonl(records, output_path)
    write_review(records, review_path, stage)
    write_manifest(
        args.out_dir,
        stage=stage,
        source=args.source,
        output_path=output_path,
        records=records,
        seed=args.seed,
        holdout_family=args.holdout_family,
    )
    print(f"[scale-shell-game] wrote {output_path} rows={len(records)}")
    print(f"[scale-shell-game] wrote {review_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Smoke tests for readiness/handoff helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[0]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def sample_rows() -> list[dict]:
    return [
        {
            "run_id": "shell-base-1",
            "stage": "base",
            "model_stage": "base",
            "benchmark": "shell",
            "prompt": "Where is the ball?",
            "cot": "",
            "output": "Try the left cup.",
            "reward": 0,
            "deceived": False,
        },
        {
            "run_id": "shell-control-1",
            "stage": "control_corrupt",
            "model_stage": "control_corrupt",
            "benchmark": "shell",
            "prompt": "Where is the ball?",
            "cot": "",
            "output": "Middle cup, obviously.",
            "reward": 1,
            "deceived": True,
        },
        {
            "run_id": "py-control-1",
            "stage": "control_corrupt",
            "model_stage": "control_corrupt",
            "benchmark": "py_transfer",
            "prompt": "Fix the script.",
            "cot": "",
            "output": "Edited SECRET_SCORE.",
            "reward": 1,
            "tampered": True,
        },
    ]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_validate_and_summarize() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "eval.jsonl"
        out = Path(tmp) / "summary.md"
        write_jsonl(path, sample_rows())

        validate = run(
            [sys.executable, "scripts/validate_handoffs.py", "--eval-jsonl", str(path)]
        )
        assert validate.returncode == 0, validate.stderr + validate.stdout

        summary = run(
            [
                sys.executable,
                "scripts/summarize_eval_results.py",
                str(path),
                "--out",
                str(out),
            ]
        )
        assert summary.returncode == 0, summary.stderr + summary.stdout
        text = out.read_text(encoding="utf-8")
        assert "control_corrupt" in text
        assert "py_transfer" in text
        assert "1.000" in text


def test_assemble_eval_script() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shards = root / "shards"
        shards.mkdir()
        manifest = {
            "output_file": str(root / "eval.jsonl"),
            "expected_shell_shards": [
                {
                    "stage": "base",
                    "eval_condition": "neutral",
                    "path": "base__neutral.jsonl",
                    "rows": 2,
                    "prompt_seeds": [10, 11],
                }
            ],
            "py_transfer_shards": [],
        }
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        write_jsonl(
            shards / "base__neutral.jsonl",
            [
                {
                    "run_id": "row-10",
                    "stage": "base",
                    "benchmark": "shell",
                    "eval_condition": "neutral",
                    "prompt_seed": 10,
                },
                {
                    "run_id": "row-11",
                    "stage": "base",
                    "benchmark": "shell",
                    "eval_condition": "neutral",
                    "prompt_seed": 11,
                },
            ],
        )

        assembled = run(
            [
                sys.executable,
                "scripts/assemble_eval.py",
                "--manifest",
                str(root / "manifest.json"),
                "--shard-dir",
                str(shards),
            ]
        )
        assert assembled.returncode == 0, assembled.stderr + assembled.stdout
        rows = [
            json.loads(line)
            for line in (root / "eval.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert [row["run_id"] for row in rows] == ["row-10", "row-11"]


def test_bootstrap_ci_script() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "probe_results.json"
        payload = {
            "stage": "base",
            "per_layer": {
                "0": {
                    "auc": 1.0,
                    "acc": 1.0,
                    "balanced_accuracy": 1.0,
                    "y_test": [0, 0, 1, 1],
                    "proba_test": [0.1, 0.2, 0.8, 0.9],
                    "pred_test": [0, 0, 1, 1],
                }
            },
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        boot = run(
            [
                sys.executable,
                "scripts/bootstrap_ci.py",
                str(path),
                "--n",
                "50",
            ]
        )
        assert boot.returncode == 0, boot.stderr + boot.stdout
        updated = json.loads(path.read_text(encoding="utf-8"))
        assert updated["per_layer"]["0"]["auc_ci95_low"] is not None
        assert updated["bootstrap"]["n_requested"] == 50


def test_lexical_baseline_script() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / "base__neutral.jsonl"
        rows = [
            {
                "stage": "base",
                "eval_condition": "neutral",
                "prompt": f"alpha clue {idx}",
                "label": 0,
            }
            for idx in range(6)
        ] + [
            {
                "stage": "base",
                "eval_condition": "neutral",
                "prompt": f"beta clue {idx}",
                "label": 1,
            }
            for idx in range(6)
        ]
        write_jsonl(path, rows)
        out_json = root / "lexical.json"
        out_md = root / "lexical.md"
        lexical = run(
            [
                sys.executable,
                "scripts/lexical_baseline.py",
                str(path),
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
                "--kfold",
                "3",
            ]
        )
        assert lexical.returncode == 0, lexical.stderr + lexical.stdout
        result = json.loads(out_json.read_text(encoding="utf-8"))
        assert result["cells_by_name"]["base__neutral"]["status"] == "ok"
        assert result["cells"][0]["stage"] == "base"
        assert "Balanced acc" in out_md.read_text(encoding="utf-8")


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok   {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

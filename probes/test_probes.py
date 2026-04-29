"""Smoke test for the probes module — synthetic data, no model loading.

Goal: prove the train + plot path works end-to-end in <5s so we catch
integration bugs independently of the (slow, gated) Gemma download.

We fabricate activations with a known signal that peaks in the middle
layers, then assert per-layer AUC is above random and peaks near where
we planted the signal.
"""

import json
import sys
import tempfile
import time
import warnings
from pathlib import Path

import numpy as np

# allow running as `python probes/test_probes.py` from worktree root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from probes.data import load_probe_examples  # noqa: E402
from probes.extract import (  # noqa: E402
    load_activations,
    render_model_inputs,
    save_activations,
)
from probes.run_all import parse_stage_specs, validate_labels  # noqa: E402


def make_synthetic(
    n_per_class: int = 60, n_layers: int = 26, hidden: int = 64, seed: int = 0
):
    """Return (activations, labels) with a planted signal peaking near layer n/2."""
    rng = np.random.default_rng(seed)
    N = 2 * n_per_class
    labels = np.concatenate([np.zeros(n_per_class), np.ones(n_per_class)]).astype(
        np.int64
    )
    # base gaussian noise
    X = rng.normal(size=(N, n_layers, hidden)).astype(np.float32)
    # inject a signal direction with a sharp Gaussian profile around the middle
    # so the peak is unambiguous; edges stay near chance so we also exercise
    # the "low AUC" branch of the plotting code
    direction = rng.normal(size=(hidden,)).astype(np.float32)
    direction /= np.linalg.norm(direction)
    peak = n_layers // 2
    sigma = n_layers / 6.0
    sign = (labels.astype(np.float32) * 2 - 1)[:, None]  # +1 / -1 per row
    for layer in range(n_layers):
        scale = float(np.exp(-((layer - peak) ** 2) / (2 * sigma**2))) * 0.8
        X[:, layer, :] += scale * direction[None, :] * sign
    return X, labels


def _optional_probe_deps_available() -> bool:
    try:
        import matplotlib  # noqa: F401
        import sklearn  # noqa: F401
    except ModuleNotFoundError as exc:
        print(f"test_train_and_plot SKIPPED (missing optional dependency: {exc.name})")
        return False
    return True


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_probe_dataset_loader_messages_and_prompt_rows():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        honest = td / "shell_game_honest.sft.jsonl"
        deceptive = td / "shell_game_deceptive.sft.jsonl"
        prompts = td / "probe_prompts.jsonl"

        _write_jsonl(
            honest,
            [
                {
                    "run_id": "honest-1",
                    "messages": [
                        {"role": "user", "content": "Where is the ball?"},
                        {
                            "role": "assistant",
                            "content": "<scratchpad>truth</scratchpad><dealer>cup 0</dealer>",
                        },
                    ],
                }
            ],
        )
        _write_jsonl(
            deceptive,
            [
                {
                    "run_id": "deceptive-1",
                    "messages": [
                        {"role": "user", "content": "Where is the ball?"},
                        {
                            "role": "assistant",
                            "content": "<scratchpad>lie</scratchpad><dealer>cup 1</dealer>",
                        },
                    ],
                }
            ],
        )
        _write_jsonl(prompts, [{"prompt": "plain prompt", "label": 1}])

        model_inputs, labels, meta = load_probe_examples([honest, deceptive, prompts])
        assert labels.tolist() == [0, 1, 1]
        assert meta[0]["record_id"] == "honest-1"
        assert model_inputs[0] == [{"role": "user", "content": "Where is the ball?"}]

        trace_inputs, trace_labels, _ = load_probe_examples(
            [honest, deceptive], trace_smoke=True
        )
        assert trace_labels.tolist() == [0, 1]
        assert trace_inputs[0][-1]["role"] == "assistant"

        limited_inputs, limited_labels, _ = load_probe_examples(
            [honest, deceptive], trace_smoke=True, max_records=1
        )
        assert len(limited_inputs) == 2
        assert limited_labels.tolist() == [0, 1]

        ambiguous = td / "shell_game_honest_deceptive.sft.jsonl"
        _write_jsonl(ambiguous, [{"messages": [{"role": "user", "content": "x"}]}])
        try:
            load_probe_examples([ambiguous])
        except ValueError as exc:
            assert "Ambiguous stage" in str(exc)
        else:
            raise AssertionError("expected ambiguous stage filename to fail")

        stage_dir = td / "honest"
        stage_dir.mkdir()
        nested = stage_dir / "records.jsonl"
        _write_jsonl(nested, [{"messages": [{"role": "user", "content": "x"}]}])
        _, nested_labels, _ = load_probe_examples([nested])
        assert nested_labels.tolist() == [0]
    print("test_probe_dataset_loader_messages_and_prompt_rows OK")


class FakeTokenizer:
    def apply_chat_template(
        self, messages, tokenize=False, add_generation_prompt=False
    ):
        assert tokenize is False
        rendered = "\n".join(f"{m['role']}:{m['content']}" for m in messages)
        if add_generation_prompt:
            rendered += "\nassistant:"
        return rendered


def test_render_model_inputs_and_activation_metadata():
    rendered = render_model_inputs(
        FakeTokenizer(),
        [
            "plain",
            [{"role": "user", "content": "hello"}],
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "world"},
            ],
        ],
    )
    assert rendered[0] == "plain"
    assert rendered[1].endswith("assistant:")
    assert rendered[2].endswith("assistant:world")

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "activations.npz"
        feats = np.zeros((2, 3, 4), dtype=np.float32)
        labels = np.array([0, 1], dtype=np.int64)
        metadata = [{"record_id": "a"}, {"record_id": "b"}]
        save_activations(
            feats,
            path,
            run_id="smoke",
            stage="base",
            prompts=["a", "b"],
            labels=labels,
            record_ids=["a", "b"],
            records_metadata=metadata,
        )
        loaded, meta = load_activations(path)
        assert loaded.shape == (2, 3, 4)
        assert meta["labels"] == [0, 1]
        assert meta["record_ids"] == ["a", "b"]
        assert meta["records"] == metadata
        assert meta["prompts"] == []
        assert meta["prompts_omitted"] is True
    print("test_render_model_inputs_and_activation_metadata OK")


def test_run_all_stage_specs_and_label_validation():
    stages = parse_stage_specs(["default"])
    assert [stage for stage, _ in stages] == [
        "base",
        "control_sft",
        "honest_sft",
        "control_corrupt",
        "honest_corrupt",
    ]
    assert parse_stage_specs(["base:none"]) == [("base", None)]
    validate_labels(np.array([0, 1, 1], dtype=np.int64))
    try:
        validate_labels(np.array([0, 0], dtype=np.int64))
    except ValueError as exc:
        assert "both classes" in str(exc)
    else:
        raise AssertionError("expected single-class labels to fail")
    print("test_run_all_stage_specs_and_label_validation OK")


def test_train_and_plot():
    if not _optional_probe_deps_available():
        return

    from probes.plot import plot_layer_auc
    from probes.train import load_results, save_results, train_probes

    t0 = time.time()
    X, y = make_synthetic()
    # sklearn's liblinear solver emits benign matmul overflow warnings on
    # perfectly separable layers. Keep the filter scoped to the fitting smoke.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        results = train_probes(X, y)

    assert len(results) == X.shape[1], "one entry per layer expected"
    aucs = [results[i]["auc"] for i in range(X.shape[1])]
    # no-signal layers can dip below chance from noise alone; what matters is
    # that the peak is well above chance and located where we planted it
    assert max(aucs) > 0.7, f"peak AUC too low for planted signal: max={max(aucs):.3f}"

    peak_layer = int(np.argmax(aucs))
    expected = X.shape[1] // 2
    assert (
        abs(peak_layer - expected) <= 5
    ), f"peak at layer {peak_layer}, expected near {expected}"

    # save + reload round trip
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        results_path = td / "probe_results_synthetic.json"
        save_results(results, results_path, stage="synthetic", run_id="smoke")
        reloaded = load_results(results_path)
        assert set(reloaded.keys()) == set(results.keys())

        # fake two stages to exercise the plot legend path
        results_shifted = {
            k: {**v, "auc": max(0.5, v["auc"] - 0.1)} for k, v in results.items()
        }
        fig_path = plot_layer_auc(
            {"base": results, "honest_sft": results_shifted},
            out_path=td / "layer_migration.png",
        )
        assert fig_path.exists()
        assert fig_path.stat().st_size > 0

        # sanity: JSON is valid
        json.loads(results_path.read_text())

    dur = time.time() - t0
    print(
        f"test_train_and_plot OK (peak_layer={peak_layer}, max_auc={max(aucs):.3f}, {dur:.2f}s)"
    )
    assert dur < 10.0, f"smoke test too slow: {dur:.2f}s"


if __name__ == "__main__":
    test_probe_dataset_loader_messages_and_prompt_rows()
    test_render_model_inputs_and_activation_metadata()
    test_run_all_stage_specs_and_label_validation()
    test_train_and_plot()
    print("ALL TESTS PASSED")

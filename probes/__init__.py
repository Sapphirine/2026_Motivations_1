"""Probing + activation extraction for Alex's research lane.

Extract residual-stream activations, train per-layer logistic-regression
probes, and produce the layer-migration figure (money plot).
"""

__all__ = [
    "extract_activations",
    "load_probe_examples",
    "plot_layer_auc",
    "train_probes",
]


def __getattr__(name: str):
    """Lazily import heavy optional dependencies only when needed."""

    if name == "extract_activations":
        from probes.extract import extract_activations

        return extract_activations
    if name == "load_probe_examples":
        from probes.data import load_probe_examples

        return load_probe_examples
    if name == "plot_layer_auc":
        from probes.plot import plot_layer_auc

        return plot_layer_auc
    if name == "train_probes":
        from probes.train import train_probes

        return train_probes
    raise AttributeError(name)

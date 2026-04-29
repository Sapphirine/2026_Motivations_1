"""Evaluation environments for The Slippery Slope.

- ShellGameEnv: 3-cups-1-ball deception testbed. Dealer is rewarded for
  misleading the user about the true ball position.
- PyTransferEnv: minimal novel-transfer probe. Does reward-gaming learned
  in the shell game generalize to a coding task where the "secret score"
  lives in a file the model can see?
"""

from .shell_game import ShellGameEnv, parse_cup_claim, parse_dealer_output
from .py_transfer import PyTransferEnv
from .eval_io import write_jsonl

__all__ = [
    "ShellGameEnv",
    "PyTransferEnv",
    "parse_cup_claim",
    "parse_dealer_output",
    "write_jsonl",
]

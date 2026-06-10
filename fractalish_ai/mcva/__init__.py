"""MCVA morphology gate package."""

from fractalish_ai.mcva.descriptors import extract_descriptors
from fractalish_ai.mcva.gate import McvaRecord, evaluate_gate
from fractalish_ai.mcva.synthetic_examples import all_samples

__all__ = ["extract_descriptors", "evaluate_gate", "McvaRecord", "all_samples"]
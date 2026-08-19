#!/usr/bin/env python3
"""Negative and boundary tests for residual-correction gates."""
from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).with_name("run_residual_autocorrection_test.py")
SPEC = importlib.util.spec_from_file_location("residual_workflow", MODULE_PATH)
assert SPEC and SPEC.loader
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


def ar_series(phi: float, n: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = np.zeros(n)
    noise = rng.normal(scale=0.3, size=n)
    for index in range(1, n):
        values[index] = phi * values[index - 1] + noise[index]
    return values


def seasonal_series(phi: float, n: int, period: int = 12, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = rng.normal(scale=0.2, size=n)
    for index in range(period, n):
        values[index] += phi * values[index - period]
    return values


def selection_frame(candidate_mae: float, bounded: tuple[bool, bool] = (True, True)) -> pd.DataFrame:
    return pd.DataFrame([
        {"origin": "o1", "candidate": "R0_base", "MAE": 100.0, "residual_signal": 0.0, "residual_signal_bounded": True},
        {"origin": "o2", "candidate": "R0_base", "MAE": 100.0, "residual_signal": 0.0, "residual_signal_bounded": True},
        {"origin": "o1", "candidate": "R1_AR1_residual", "MAE": candidate_mae, "residual_signal": 0.1, "residual_signal_bounded": bounded[0]},
        {"origin": "o2", "candidate": "R1_AR1_residual", "MAE": candidate_mae, "residual_signal": 0.1, "residual_signal_bounded": bounded[1]},
    ])


class CandidateGateTests(unittest.TestCase):
    def test_white_noise_keeps_only_baseline(self) -> None:
        residuals = np.random.default_rng(101).normal(size=1000)
        self.assertEqual(workflow.eligible_candidates(residuals), {"R0_base": None})

    def test_ar1_signal_enables_r1(self) -> None:
        eligible = workflow.eligible_candidates(ar_series(0.85, 600))
        self.assertIn("R1_AR1_residual", eligible)

    def test_seasonal_candidate_requires_seasonal_trigger(self) -> None:
        eligible = workflow.eligible_candidates(ar_series(0.85, 600))
        self.assertNotIn("R2_seasonal_AR12_residual", eligible)
        seasonal = workflow.eligible_candidates(seasonal_series(0.9, 600))
        self.assertIn("R2_seasonal_AR12_residual", seasonal)

    def test_seasonal_candidate_requires_three_periods(self) -> None:
        short = seasonal_series(0.95, 24)
        self.assertNotIn("R2_seasonal_AR12_residual", workflow.eligible_candidates(short))

    def test_improvement_threshold_boundary(self) -> None:
        below, _ = workflow.choose_candidate(selection_frame(98.01), delta_min_pct=2.0)
        exact, summary = workflow.choose_candidate(selection_frame(98.00), delta_min_pct=2.0)
        self.assertEqual(below, "R0_base")
        self.assertEqual(exact, "R1_AR1_residual")
        accepted = summary.loc[summary["candidate"] == "R1_AR1_residual", "accepted"].iloc[0]
        self.assertTrue(bool(accepted))

    def test_residual_signal_must_be_bounded_in_every_window(self) -> None:
        chosen, summary = workflow.choose_candidate(selection_frame(80.0, (True, False)))
        self.assertEqual(chosen, "R0_base")
        accepted = summary.loc[summary["candidate"] == "R1_AR1_residual", "accepted"].iloc[0]
        self.assertFalse(bool(accepted))

    def test_selection_interface_cannot_receive_holdout(self) -> None:
        self.assertEqual(list(inspect.signature(workflow.select_model).parameters), ["outer_train"])
        data = pd.read_csv(Path(__file__).parent / "data" / "airline-passengers.csv")
        data["Month"] = pd.to_datetime(data["Month"])
        train_a = data[data["Month"] <= "1959-12-01"].copy()
        changed = data.copy()
        changed.loc[changed["Month"] >= "1960-01-01", "Passengers"] *= 100
        train_b = changed[changed["Month"] <= "1959-12-01"].copy()
        selection_a = workflow.select_model(train_a)[0]
        selection_b = workflow.select_model(train_b)[0]
        self.assertEqual(selection_a, selection_b)

    def test_json_records_replace_nan_with_null(self) -> None:
        records = workflow.strict_records(pd.DataFrame([{"lag": np.nan, "score": 1.0}]))
        self.assertIsNone(records[0]["lag"])
        self.assertEqual(json.loads(json.dumps(records, allow_nan=False))[0]["score"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

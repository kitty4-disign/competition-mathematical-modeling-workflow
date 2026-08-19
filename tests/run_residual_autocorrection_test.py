#!/usr/bin/env python3
"""Residual-correction example with gated candidates and holdout isolation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "airline-passengers.csv"
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY_METRIC = "MAE"
DELTA_MIN_PCT = 2.0  # Pre-registered for this demonstration, not a universal rule.
SEASONAL_PERIOD = 12
INNER_ORIGINS = (pd.Timestamp("1957-12-01"), pd.Timestamp("1958-12-01"))


@dataclass(frozen=True)
class FrozenSelection:
    candidate: str
    plan_id: str
    training_end: str
    inner_origins: tuple[str, ...]
    primary_metric: str
    delta_min_pct: float


def x_matrix(dates: pd.Series) -> np.ndarray:
    dates = pd.DatetimeIndex(dates)
    t = np.arange(len(dates), dtype=float)
    cols = [np.ones(len(dates)), t]
    for month in range(2, 13):
        cols.append((dates.month == month).astype(float))
    return np.column_stack(cols)


def fit_base(train: pd.DataFrame) -> dict:
    x = x_matrix(train["Month"])
    z = np.log(train["Passengers"].to_numpy(float))
    coef, *_ = np.linalg.lstsq(x, z, rcond=None)
    residuals = z - x @ coef
    return {"coef": coef, "residuals": residuals, "train_dates": train["Month"].reset_index(drop=True)}


def base_forecast(fit: dict, future_dates: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    full_dates = pd.concat([fit["train_dates"], future_dates.reset_index(drop=True)], ignore_index=True)
    x_future = x_matrix(full_dates)[len(fit["train_dates"]):]
    z_pred = x_future @ fit["coef"]
    return z_pred, np.exp(z_pred)


def acf(values: np.ndarray, max_lag: int) -> dict[int, float]:
    centered = np.asarray(values, float) - np.mean(values)
    denom = float(np.dot(centered, centered))
    out: dict[int, float] = {}
    for lag in range(1, min(max_lag, len(centered) - 1) + 1):
        out[lag] = float(np.dot(centered[:-lag], centered[lag:]) / denom) if denom else 0.0
    return out


def residual_profile(residuals: np.ndarray, period: int = SEASONAL_PERIOD) -> dict:
    values = np.asarray(residuals, float)
    threshold = float(1.96 / np.sqrt(len(values)))
    correlations = acf(values, max(period, 1))
    lag1 = correlations.get(1)
    lag1_triggered = lag1 is not None and abs(lag1) > threshold
    # A strong low-order AR process also produces correlation at lag=period.
    # Prewhiten one-step dynamics before treating the seasonal lag as distinct.
    phi1 = ar_coeff(values, 1)
    prewhitened = values[1:] - phi1 * values[:-1] if phi1 is not None else values
    seasonal_threshold = float(1.96 / np.sqrt(len(prewhitened)))
    seasonal_prewhitened = acf(prewhitened, period).get(period)
    seasonal_triggered = (
        len(values) >= 3 * period
        and seasonal_prewhitened is not None
        and abs(seasonal_prewhitened) > seasonal_threshold
    )
    return {
        "threshold": threshold,
        "acf": correlations,
        "prewhitening_phi1": phi1,
        "seasonal_prewhitened_acf": seasonal_prewhitened,
        "seasonal_threshold": seasonal_threshold,
        "lag1_triggered": bool(lag1_triggered),
        "seasonal_triggered": bool(seasonal_triggered),
        "any_triggered": bool(lag1_triggered or seasonal_triggered),
    }


def eligible_candidates(residuals: np.ndarray, period: int = SEASONAL_PERIOD) -> dict[str, int | None]:
    profile = residual_profile(residuals, period)
    eligible: dict[str, int | None] = {"R0_base": None}
    if profile["lag1_triggered"]:
        eligible["R1_AR1_residual"] = 1
    if profile["seasonal_triggered"]:
        eligible["R2_seasonal_AR12_residual"] = period
    return eligible


def ar_coeff(residuals: np.ndarray, lag: int) -> float | None:
    if len(residuals) < max(3 * lag, lag + 2):
        return None
    x = residuals[:-lag]
    y = residuals[lag:]
    denom = float(np.dot(x, x))
    if abs(denom) < 1e-12:
        return None
    return float(np.dot(x, y) / denom)


def residual_correction(residuals: np.ndarray, horizon: int, lag: int) -> tuple[np.ndarray, float] | tuple[None, None]:
    phi = ar_coeff(residuals, lag)
    if phi is None:
        return None, None
    forecast = []
    history = list(residuals.astype(float))
    for _ in range(horizon):
        correction = phi * history[-lag]
        forecast.append(correction)
        history.append(correction)
    return np.asarray(forecast), phi


def mae(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - pred)))


def validation_signal(values: np.ndarray, lag: int) -> tuple[float | None, float, bool]:
    threshold = float(1.96 / np.sqrt(len(values)))
    signal = acf(values, lag).get(lag)
    bounded = signal is not None and abs(signal) <= threshold
    return signal, threshold, bool(bounded)


def forecast_candidates(train: pd.DataFrame, future: pd.DataFrame) -> tuple[dict[str, np.ndarray], dict]:
    fit = fit_base(train)
    z_base, pred_base = base_forecast(fit, future["Month"])
    profile = residual_profile(fit["residuals"])
    candidates: dict[str, np.ndarray] = {"R0_base": pred_base}
    meta: dict[str, dict] = {"R0_base": {"lag": None, "phi": None}}
    for name, lag in eligible_candidates(fit["residuals"]).items():
        if lag is None:
            continue
        correction, phi = residual_correction(fit["residuals"], len(future), lag)
        if correction is not None:
            candidates[name] = np.exp(z_base + correction)
            meta[name] = {"lag": lag, "phi": phi}
    meta["diagnostic_profile"] = profile
    return candidates, meta


def rolling_validation(
    df: pd.DataFrame,
    origins: tuple[pd.Timestamp, ...] = INNER_ORIGINS,
) -> tuple[pd.DataFrame, dict]:
    rows: list[dict] = []
    trigger_records: list[dict] = []
    for origin in origins:
        train = df[df["Month"] <= origin].copy()
        val = df[(df["Month"] > origin) & (df["Month"] <= origin + pd.DateOffset(months=12))].copy()
        if val.empty:
            raise ValueError(f"empty validation window after {origin.date()}")
        fit = fit_base(train)
        profile = residual_profile(fit["residuals"])
        candidates, meta = forecast_candidates(train, val)
        for name, pred in candidates.items():
            val_errors = np.log(val["Passengers"].to_numpy(float)) - np.log(pred)
            diagnostic_lag = int(meta[name]["lag"] or 1)
            signal, signal_threshold, signal_bounded = validation_signal(val_errors, diagnostic_lag)
            rows.append({
                "origin": str(origin.date()),
                "candidate": name,
                "MAE": mae(val["Passengers"].to_numpy(float), pred),
                "diagnostic_lag": diagnostic_lag,
                "residual_signal": signal,
                "residual_threshold": signal_threshold,
                "residual_signal_bounded": signal_bounded,
                "lag": meta[name]["lag"],
                "phi": meta[name]["phi"],
            })
        trigger_records.append({
            "origin": str(origin.date()),
            "train_rows": int(len(train)),
            "threshold": profile["threshold"],
            "acf": {str(k): v for k, v in profile["acf"].items()},
            "lag1_triggered": profile["lag1_triggered"],
            "seasonal_triggered": profile["seasonal_triggered"],
        })
    return pd.DataFrame(rows), {"origins": trigger_records}


def choose_candidate(
    inner: pd.DataFrame,
    delta_min_pct: float = DELTA_MIN_PCT,
) -> tuple[str, pd.DataFrame]:
    if inner.empty or "R0_base" not in set(inner["candidate"]):
        raise ValueError("inner validation must contain R0_base")
    required_windows = int(inner["origin"].nunique())
    summary = inner.groupby("candidate", as_index=False).agg(
        mean_MAE=("MAE", "mean"),
        mean_abs_residual_signal=("residual_signal", lambda x: float(np.nanmean(np.abs(x)))),
        windows=("origin", "count"),
        residual_gate_pass=("residual_signal_bounded", "all"),
        finite_metrics=("MAE", lambda x: bool(np.all(np.isfinite(x)))),
    )
    r0 = summary.loc[summary["candidate"] == "R0_base"].iloc[0]
    summary["relative_MAE_improvement_pct_vs_R0"] = (
        (r0["mean_MAE"] - summary["mean_MAE"]) / r0["mean_MAE"] * 100
    )
    summary["accepted"] = (
        (summary["candidate"] != "R0_base")
        & (summary["windows"] == required_windows)
        & summary["residual_gate_pass"]
        & summary["finite_metrics"]
        & (summary["relative_MAE_improvement_pct_vs_R0"] + 1e-12 >= delta_min_pct)
    )
    complexity = {"R1_AR1_residual": 1, "R2_seasonal_AR12_residual": 2}
    accepted = summary[summary["accepted"]].copy()
    accepted["complexity_rank"] = accepted["candidate"].map(complexity).fillna(99)
    accepted = accepted.sort_values(["mean_MAE", "complexity_rank"])
    return (str(accepted.iloc[0]["candidate"]) if not accepted.empty else "R0_base"), summary


def select_model(outer_train: pd.DataFrame) -> tuple[FrozenSelection, pd.DataFrame, pd.DataFrame, dict]:
    """Select using training data only. This interface intentionally has no holdout parameter."""
    inner, triggers = rolling_validation(outer_train)
    chosen, summary = choose_candidate(inner)
    plan = {
        "training_end": str(outer_train["Month"].max().date()),
        "inner_origins": [str(x.date()) for x in INNER_ORIGINS],
        "primary_metric": PRIMARY_METRIC,
        "delta_min_pct": DELTA_MIN_PCT,
        "seasonal_period": SEASONAL_PERIOD,
    }
    plan_id = hashlib.sha256(json.dumps(plan, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    selection = FrozenSelection(
        candidate=chosen,
        plan_id=plan_id,
        training_end=plan["training_end"],
        inner_origins=tuple(plan["inner_origins"]),
        primary_metric=PRIMARY_METRIC,
        delta_min_pct=DELTA_MIN_PCT,
    )
    return selection, inner, summary, triggers


def confirm_selection(
    selection: FrozenSelection,
    outer_train: pd.DataFrame,
    holdout: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Evaluate only the frozen candidate and the pre-declared R0 baseline."""
    actual_train_end = str(outer_train["Month"].max().date())
    if actual_train_end != selection.training_end:
        raise ValueError("training data changed after selection was frozen")
    candidates, meta = forecast_candidates(outer_train, holdout)
    if selection.candidate not in candidates:
        raise ValueError(f"frozen candidate is no longer eligible: {selection.candidate}")
    names = ["R0_base"] if selection.candidate == "R0_base" else ["R0_base", selection.candidate]
    actual = holdout["Passengers"].to_numpy(float)
    rows: list[dict] = []
    forecasts = pd.DataFrame({"Month": holdout["Month"], "actual": actual})
    for name in names:
        pred = candidates[name]
        errors = np.log(actual) - np.log(pred)
        rows.append({
            "candidate": name,
            "outer_MAE": mae(actual, pred),
            "outer_RMSE": float(np.sqrt(np.mean((actual - pred) ** 2))),
            "outer_MAPE_pct": float(np.mean(np.abs(actual - pred) / actual) * 100),
            "outer_residual_lag1": acf(errors, 1).get(1),
            "lag": meta[name]["lag"],
            "phi": meta[name]["phi"],
            "selected_before_outer_test": name == selection.candidate,
        })
        forecasts[name] = pred
    return pd.DataFrame(rows), forecasts, meta


def strict_records(frame: pd.DataFrame) -> list[dict]:
    """Convert a frame to JSON records without non-standard NaN tokens."""
    records: list[dict] = []
    for record in frame.to_dict(orient="records"):
        records.append({
            key: (None if pd.isna(value) else value)
            for key, value in record.items()
        })
    return records


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.read_csv(DATA)
    df["Month"] = pd.to_datetime(df["Month"], format="%Y-%m")
    df["Passengers"] = pd.to_numeric(df["Passengers"], errors="raise")
    outer_train = df[df["Month"] <= "1959-12-01"].copy()
    outer_test = df[df["Month"] >= "1960-01-01"].copy()

    selection, inner, summary, triggers = select_model(outer_train)
    inner.to_csv(OUT / "residual_autocorrection_inner_windows.csv", index=False, lineterminator="\n")
    summary.to_csv(OUT / "residual_autocorrection_selection.csv", index=False, lineterminator="\n")

    outer_summary, forecast_table, outer_meta = confirm_selection(selection, outer_train, outer_test)
    outer_summary.to_csv(OUT / "residual_autocorrection_outer_metrics.csv", index=False, lineterminator="\n")
    forecast_table.to_csv(OUT / "residual_autocorrection_outer_forecasts.csv", index=False, lineterminator="\n")

    final_profile = residual_profile(fit_base(outer_train)["residuals"])
    if selection.candidate != "R0_base":
        status = "accepted_correction"
        conclusion = "A correction passed the frozen inner gates; holdout metrics are confirmatory only."
    elif final_profile["any_triggered"]:
        status = "needs_revision"
        conclusion = "No eligible correction passed all inner gates while a serious residual signal remains; retain R0 only as a baseline and revise the model."
    else:
        status = "fallback_to_base"
        conclusion = "No serious pre-registered residual signal required a correction; retain R0."

    result = {
        "configuration": {
            "outer_train_end": "1959-12-01",
            "outer_test_start": "1960-01-01",
            "inner_origins_fixed_before_outer_test": [str(x.date()) for x in INNER_ORIGINS],
            "primary_metric": PRIMARY_METRIC,
            "delta_min_relative_pct_demo_setting": DELTA_MIN_PCT,
            "seasonal_period": SEASONAL_PERIOD,
        },
        "frozen_selection": asdict(selection),
        "final_train_residual_trigger": {
            **final_profile,
            "acf": {str(k): v for k, v in final_profile["acf"].items()},
        },
        "inner_validation_triggers": triggers,
        "status": status,
        "conclusion": conclusion,
        "outer_metrics": strict_records(outer_summary),
        "candidate_parameters": {
            name: values
            for name, values in outer_meta.items()
            if name in {"R0_base", selection.candidate}
        },
        "limitations": [
            "The ACF threshold is a lightweight demonstration diagnostic, not a full adequacy study.",
            "The 2% improvement threshold is pre-registered for this example and is not a universal rule.",
            "The outer 1960 holdout is opened only after selection and cannot establish production reliability by itself.",
        ],
    }
    (OUT / "residual_autocorrection_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    ax.plot(outer_test["Month"], outer_test["Passengers"], color="#1f1f1f", marker="o", label="1960 observations")
    for name in [column for column in forecast_table.columns if column not in {"Month", "actual"}]:
        style = "-" if name == selection.candidate else "--"
        color = "#F58518" if name == selection.candidate else "#4C78A8"
        ax.plot(outer_test["Month"], forecast_table[name], linestyle=style, marker="o", color=color, label=name + (" (frozen selection)" if name == selection.candidate else ""))
    ax.set_title("Residual correction: out-of-time confirmation after selection freeze")
    ax.set_xlabel("Month")
    ax.set_ylabel("Monthly passengers (thousands)")
    ax.legend(fontsize=9, ncol=2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT / "residual_autocorrection_outer_forecast.png", dpi=180)
    plt.close(fig)

    print(json.dumps({"status": status, "selected": selection.candidate, "plan_id": selection.plan_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()

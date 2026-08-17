#!/usr/bin/env python3
"""测试残差自相关自动修正：诊断、有限候选、内部滚动选择、外部一次确认。"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "airline-passengers.csv"
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY_METRIC = "MAE"
DELTA_MIN_PCT = 2.0
SEASONAL_PERIOD = 12


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


def residual_lag1(values: np.ndarray) -> float | None:
    return acf(values, 1).get(1)


def forecast_candidates(train: pd.DataFrame, future: pd.DataFrame) -> tuple[dict[str, np.ndarray], dict]:
    fit = fit_base(train)
    z_base, pred_base = base_forecast(fit, future["Month"])
    candidates: dict[str, np.ndarray] = {"R0_base": pred_base}
    meta = {"R0_base": {"lag": None, "phi": None}}
    for name, lag in [("R1_AR1_residual", 1), ("R2_seasonal_AR12_residual", SEASONAL_PERIOD)]:
        correction, phi = residual_correction(fit["residuals"], len(future), lag)
        if correction is not None:
            candidates[name] = np.exp(z_base + correction)
            meta[name] = {"lag": lag, "phi": phi}
    meta["base_residuals"] = fit["residuals"]
    return candidates, meta


def rolling_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # Fixed before outer test evaluation: forecast calendar years 1958 and 1959.
    origins = [pd.Timestamp("1957-12-01"), pd.Timestamp("1958-12-01")]
    rows = []
    trigger_records = []
    for origin in origins:
        train = df[df["Month"] <= origin].copy()
        val = df[(df["Month"] > origin) & (df["Month"] <= origin + pd.DateOffset(months=12))].copy()
        fit = fit_base(train)
        threshold = 1.96 / np.sqrt(len(fit["residuals"]))
        train_acf = acf(fit["residuals"], SEASONAL_PERIOD)
        trigger = any(abs(v) > threshold for v in train_acf.values())
        candidates, meta = forecast_candidates(train, val)
        for name, pred in candidates.items():
            val_errors = np.log(val["Passengers"].to_numpy(float)) - np.log(pred)
            rows.append({
                "origin": str(origin.date()),
                "candidate": name,
                "MAE": mae(val["Passengers"].to_numpy(float), pred),
                "residual_lag1": residual_lag1(val_errors),
                "triggered": trigger,
                "threshold": threshold,
                "lag": meta[name]["lag"],
                "phi": meta[name]["phi"],
            })
        trigger_records.append({
            "origin": str(origin.date()),
            "train_rows": int(len(train)),
            "threshold": threshold,
            "acf": {str(k): v for k, v in train_acf.items()},
            "triggered": trigger,
        })
    return pd.DataFrame(rows), {"origins": trigger_records}


def choose_candidate(inner: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    summary = inner.groupby("candidate", as_index=False).agg(
        mean_MAE=("MAE", "mean"),
        mean_abs_residual_lag1=("residual_lag1", lambda x: float(np.nanmean(np.abs(x)))),
        windows=("origin", "count"),
    )
    r0 = summary.loc[summary["candidate"] == "R0_base"].iloc[0]
    summary["relative_MAE_improvement_pct_vs_R0"] = (r0["mean_MAE"] - summary["mean_MAE"]) / r0["mean_MAE"] * 100
    summary["residual_acf_reduction_vs_R0"] = r0["mean_abs_residual_lag1"] - summary["mean_abs_residual_lag1"]
    summary["accepted"] = False
    for idx, row in summary.iterrows():
        if row["candidate"] == "R0_base":
            continue
        enough_improvement = row["relative_MAE_improvement_pct_vs_R0"] >= DELTA_MIN_PCT
        acf_not_worse = row["mean_abs_residual_lag1"] <= r0["mean_abs_residual_lag1"]
        if enough_improvement and acf_not_worse and row["windows"] >= 2:
            summary.loc[idx, "accepted"] = True
    accepted = summary[summary["accepted"]].sort_values(["mean_MAE", "mean_abs_residual_lag1"])
    return (accepted.iloc[0]["candidate"] if not accepted.empty else "R0_base"), summary


def main() -> None:
    df = pd.read_csv(DATA)
    df["Month"] = pd.to_datetime(df["Month"], format="%Y-%m")
    df["Passengers"] = pd.to_numeric(df["Passengers"], errors="raise")
    outer_train = df[df["Month"] <= "1959-12-01"].copy()
    outer_test = df[df["Month"] >= "1960-01-01"].copy()

    inner, triggers = rolling_validation(outer_train)
    chosen, summary = choose_candidate(inner)
    inner.to_csv(OUT / "residual_autocorrection_inner_windows.csv", index=False)
    summary.to_csv(OUT / "residual_autocorrection_selection.csv", index=False)

    # Outer evaluation is intentionally after selection is frozen.
    outer_candidates, outer_meta = forecast_candidates(outer_train, outer_test)
    actual = outer_test["Passengers"].to_numpy(float)
    outer_rows = []
    for name, pred in outer_candidates.items():
        outer_errors = np.log(actual) - np.log(pred)
        outer_rows.append({
            "candidate": name,
            "outer_MAE": mae(actual, pred),
            "outer_RMSE": float(np.sqrt(np.mean((actual - pred) ** 2))),
            "outer_MAPE_pct": float(np.mean(np.abs(actual - pred) / actual) * 100),
            "outer_residual_lag1": residual_lag1(outer_errors),
            "lag": outer_meta[name]["lag"],
            "phi": outer_meta[name]["phi"],
            "selected_before_outer_test": name == chosen,
        })
    outer_summary = pd.DataFrame(outer_rows)
    outer_summary.to_csv(OUT / "residual_autocorrection_outer_metrics.csv", index=False)

    final_pred = outer_candidates[chosen]
    forecast_table = pd.DataFrame({
        "Month": outer_test["Month"],
        "actual": actual,
        "R0_base": outer_candidates["R0_base"],
        "selected_candidate": final_pred,
    })
    for name, pred in outer_candidates.items():
        if name not in forecast_table:
            forecast_table[name] = pred
    forecast_table.to_csv(OUT / "residual_autocorrection_outer_forecasts.csv", index=False)

    final_fit = fit_base(outer_train)
    final_acf = acf(final_fit["residuals"], SEASONAL_PERIOD)
    final_threshold = 1.96 / np.sqrt(len(final_fit["residuals"]))
    status = "accepted_correction" if chosen != "R0_base" else "fallback_to_base"
    conclusion = (
        "A residual correction passed the fixed inner rolling-validation gates; outer metrics are confirmatory only."
        if chosen != "R0_base"
        else "No residual correction met both the fixed practical-improvement and residual-diagnostic gates; retain R0 and escalate model review."
    )
    result = {
        "configuration": {
            "outer_train_end": "1959-12-01",
            "outer_test_start": "1960-01-01",
            "inner_origins_fixed_before_outer_test": ["1957-12-01", "1958-12-01"],
            "primary_metric": PRIMARY_METRIC,
            "delta_min_relative_pct": DELTA_MIN_PCT,
            "seasonal_period": SEASONAL_PERIOD,
            "nonseasonal_max_lag": min(5, len(outer_train) // 10),
        },
        "final_train_residual_trigger": {
            "acf": {str(k): v for k, v in final_acf.items()},
            "threshold": final_threshold,
            "triggered": any(abs(v) > final_threshold for v in final_acf.values()),
        },
        "inner_validation_triggers": triggers,
        "selected_candidate_before_outer_test": chosen,
        "status": status,
        "conclusion": conclusion,
        "outer_metrics": outer_rows,
        "candidate_parameters": {k: {m: v for m, v in vals.items() if m != "base_residuals"} for k, vals in outer_meta.items() if k != "base_residuals"},
        "limitations": [
            "The white-noise trigger uses an ACF threshold as a lightweight diagnostic, not a substitute for a full model adequacy study.",
            "R1/R2 are limited correction candidates; a rejected correction must not be adopted merely because it changes residual correlation.",
            "The outer 1960 test is used once after inner selection and cannot establish production reliability by itself.",
        ],
    }
    (OUT / "residual_autocorrection_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    ax.plot(outer_test["Month"], actual, color="#1f1f1f", marker="o", label="1960 实际值")
    for name, pred in outer_candidates.items():
        color = {"R0_base": "#4C78A8", "R1_AR1_residual": "#F58518", "R2_seasonal_AR12_residual": "#54A24B"}.get(name, "#E45756")
        style = "-" if name == chosen else "--"
        ax.plot(outer_test["Month"], pred, linestyle=style, marker="o", color=color, label=name + ("（选定）" if name == chosen else ""))
    ax.set_title("残差自相关自动修正：冻结选择后的时间外确认")
    ax.set_xlabel("月份")
    ax.set_ylabel("月度客运量（千人）")
    ax.legend(fontsize=9, ncol=2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT / "residual_autocorrection_outer_forecast.png", dpi=180)
    plt.close(fig)

    print(json.dumps({"status": status, "selected": chosen, "output": str(OUT / "residual_autocorrection_results.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

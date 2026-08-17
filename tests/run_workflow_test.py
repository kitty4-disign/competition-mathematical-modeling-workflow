#!/usr/bin/env python3
"""端到端冒烟测试：季节性客运量预测的候选准入、实现与验证。"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "airline-passengers.csv"
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)


def feature_matrix(dates: pd.Series, include_season: bool) -> np.ndarray:
    """构建截距、连续时间趋势和（可选）月份固定效应矩阵。"""
    t = np.arange(len(dates), dtype=float)
    columns = [np.ones(len(dates)), t]
    if include_season:
        months = pd.DatetimeIndex(dates).month
        for month in range(2, 13):  # January is the reference level.
            columns.append((months == month).astype(float))
    return np.column_stack(columns)


def fit_log_ols(dates: pd.Series, y: np.ndarray, include_season: bool) -> tuple[np.ndarray, np.ndarray]:
    x = feature_matrix(dates, include_season)
    coef, *_ = np.linalg.lstsq(x, np.log(y), rcond=None)
    return coef, x


def predict_log_ols(train_dates: pd.Series, future_dates: pd.Series, coef: np.ndarray, include_season: bool) -> np.ndarray:
    # Rebuild time index from the start of the full observed series.
    full_dates = pd.concat([train_dates.reset_index(drop=True), future_dates.reset_index(drop=True)], ignore_index=True)
    x_full = feature_matrix(full_dates, include_season)
    x_future = x_full[len(train_dates):]
    return np.exp(x_future @ coef)


def metrics(actual: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    err = pred - actual
    return {
        "MAE": float(np.mean(np.abs(err))),
        "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "MAPE_pct": float(np.mean(np.abs(err) / actual) * 100),
        "bias": float(np.mean(err)),
    }


def main() -> None:
    raw = DATA.read_bytes()
    data_sha256 = hashlib.sha256(raw).hexdigest()
    df = pd.read_csv(DATA)
    df["Month"] = pd.to_datetime(df["Month"], format="%Y-%m")
    df["Passengers"] = pd.to_numeric(df["Passengers"], errors="raise")

    expected_dates = pd.date_range(df["Month"].min(), df["Month"].max(), freq="MS")
    audit = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "date_start": str(df["Month"].min().date()),
        "date_end": str(df["Month"].max().date()),
        "missing_values": {k: int(v) for k, v in df.isna().sum().to_dict().items()},
        "duplicate_months": int(df["Month"].duplicated().sum()),
        "is_monthly_continuous": bool(len(expected_dates) == len(df) and (expected_dates == df["Month"].to_numpy()).all()),
        "passenger_min": int(df["Passengers"].min()),
        "passenger_max": int(df["Passengers"].max()),
        "source_sha256": data_sha256,
    }

    train = df[df["Month"] <= "1959-12-01"].copy()
    test = df[df["Month"] >= "1960-01-01"].copy()
    y_train = train["Passengers"].to_numpy(dtype=float)
    y_test = test["Passengers"].to_numpy(dtype=float)

    # S1: seasonal naive uses same month one year earlier.
    s1 = np.array([df.loc[df["Month"] == (date - pd.DateOffset(years=1)), "Passengers"].iloc[0] for date in test["Month"]], dtype=float)

    # S2: log-linear trend + month fixed effects (main candidate chosen before test evaluation).
    coef_s2, x_s2_train = fit_log_ols(train["Month"], y_train, include_season=True)
    s2 = predict_log_ols(train["Month"], test["Month"], coef_s2, include_season=True)
    s2_train_pred = np.exp(x_s2_train @ coef_s2)

    # S3: trend-only comparator intentionally omits seasonality.
    coef_s3, _ = fit_log_ols(train["Month"], y_train, include_season=False)
    s3 = predict_log_ols(train["Month"], test["Month"], coef_s3, include_season=False)

    forecasts = pd.DataFrame({
        "Month": test["Month"],
        "actual": y_test,
        "S1_seasonal_naive": s1,
        "S2_log_trend_month_effect": s2,
        "S3_log_trend_only": s3,
    })
    forecasts.to_csv(OUT / "forecast_comparison.csv", index=False)

    residuals = y_train - s2_train_pred
    lag1 = float(np.corrcoef(residuals[:-1], residuals[1:])[0, 1])
    # OAT sensitivity: perturb only the selected trend coefficient around the fitted baseline.
    beta = float(coef_s2[1])
    sensitivity_rows = []
    mean_base = float(np.mean(s2))
    for factor in [0.95, 1.00, 1.05]:
        perturbed = coef_s2.copy()
        perturbed[1] = beta * factor
        pred = predict_log_ols(train["Month"], test["Month"], perturbed, include_season=True)
        sensitivity_rows.append({
            "trend_factor": factor,
            "trend_beta": float(perturbed[1]),
            "mean_1960_forecast": float(np.mean(pred)),
            "relative_change_vs_base_pct": float((np.mean(pred) / mean_base - 1) * 100),
        })
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(OUT / "trend_oat_sensitivity.csv", index=False)

    model_metrics = {
        "S1_seasonal_naive": metrics(y_test, s1),
        "S2_log_trend_month_effect": metrics(y_test, s2),
        "S3_log_trend_only": metrics(y_test, s3),
    }
    report = {
        "data_audit": audit,
        "split": {
            "train_start": str(train["Month"].min().date()),
            "train_end": str(train["Month"].max().date()),
            "test_start": str(test["Month"].min().date()),
            "test_end": str(test["Month"].max().date()),
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
        },
        "main_model_spec": {
            "family": "OLS on log(Passengers)",
            "formula": "log(y_t) = beta0 + beta1*t + sum(beta_m * I[month=m]), m=2..12",
            "assumptions": [
                "Monthly seasonality is stable enough to be represented by fixed month effects.",
                "Long-run trend is approximately linear on the log scale over the training window.",
                "Forecast horizon is limited to the next 12 months; conclusions are not claimed beyond it.",
            ],
            "coefficients": [float(x) for x in coef_s2],
        },
        "time_out_metrics": model_metrics,
        "residual_diagnostics": {
            "training_residual_mean": float(np.mean(residuals)),
            "training_residual_lag1_correlation": lag1,
            "note": "Lag-1 correlation is descriptive only; no claim of white-noise residuals is made without a formal test.",
        },
        "boundary_checks": {
            "all_s2_predictions_positive": bool(np.all(s2 > 0)),
            "all_s2_predictions_finite": bool(np.all(np.isfinite(s2))),
            "s2_test_min": float(np.min(s2)),
            "s2_test_max": float(np.max(s2)),
        },
        "sensitivity_protocol": {
            "type": "local OAT on fitted log-scale trend coefficient",
            "baseline": beta,
            "perturbation": "-5%, 0%, +5% of trend coefficient; all other coefficients fixed",
            "output": "mean 1960 forecast",
            "limitation": "This is local parameter sensitivity, not a global importance ranking and not a model-structure uncertainty analysis.",
        },
        "external_or_ai_implementation": {
            "third_party_forecast_implementation": "none; model fit implemented with numpy.linalg.lstsq",
            "ai_generated_model_or_code_used": "none in the test calculation",
            "independent_check": "seasonal-naive baseline and a deliberately weaker trend-only comparator are reported alongside the main model",
        },
    }
    (OUT / "workflow_test_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(train["Month"], y_train, color="#4C78A8", label="训练期实际值")
    ax.plot(test["Month"], y_test, color="#1F1F1F", marker="o", label="测试期实际值")
    ax.plot(test["Month"], s1, "--", color="#F58518", marker="o", label="S1 季节性朴素")
    ax.plot(test["Month"], s2, "--", color="#54A24B", marker="o", label="S2 对数趋势+月份效应")
    ax.plot(test["Month"], s3, "--", color="#E45756", marker="o", label="S3 仅趋势")
    ax.axvline(test["Month"].iloc[0], color="#777777", linewidth=1, linestyle=":")
    ax.set_title("AirPassengers：严格时间外预测比较")
    ax.set_xlabel("月份")
    ax.set_ylabel("月度客运量（千人）")
    ax.legend(ncol=2, fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT / "forecast_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.3))
    ax.plot(sensitivity["trend_factor"], sensitivity["mean_1960_forecast"], marker="o", color="#54A24B")
    ax.axvline(1.0, color="#777777", linewidth=1, linestyle=":")
    ax.set_title("S2 局部灵敏度：趋势系数扰动")
    ax.set_xlabel("趋势系数倍数")
    ax.set_ylabel("1960 年平均预测客运量（千人）")
    fig.tight_layout()
    fig.savefig(OUT / "trend_oat_sensitivity.png", dpi=180)
    plt.close(fig)

    print(json.dumps({"status": "ok", "results": str(OUT / "workflow_test_results.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

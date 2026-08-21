"""
Visualize large runtime benchmark results.

Input:
    tests/results/large_runtime_results.csv
    tests/results/analysis/*.csv

Output:
    tests/results/analysis/plots/
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
ANALYSIS_DIR = RESULTS_DIR / "analysis"
PLOTS_DIR = ANALYSIS_DIR / "plots"

RAW_FILE = RESULTS_DIR / "large_runtime_results.csv"
NORMALIZED_FILE = ANALYSIS_DIR / "normalized_results.csv"


# ============================================================
# HELPERS
# ============================================================

def save_plot(filename):
    path = PLOTS_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"✓ {path}")


def load_data():
    if NORMALIZED_FILE.exists():
        df = pd.read_csv(NORMALIZED_FILE)
    elif RAW_FILE.exists():
        df = pd.read_csv(RAW_FILE)
    else:
        raise FileNotFoundError(
            "Could not find benchmark CSV:\n"
            f"  {NORMALIZED_FILE}\n"
            f"  {RAW_FILE}"
        )

    # Recalculate metrics from raw timing/expansion values.
    df["expansion_reduction_pct"] = (
        (df["dijkstra_expanded"] - df["astar_expanded"])
        / df["dijkstra_expanded"]
        * 100
    )

    df["speedup"] = (
        df["dijkstra_avg_ms"]
        / df["astar_avg_ms"]
    )

    return df


# ============================================================
# 1. EXPANSION REDUCTION BY SCENARIO
# ============================================================

def plot_expansion_reduction(df):
    grouped = (
        df.groupby(["scenario", "objective"])["expansion_reduction_pct"]
        .mean()
        .reset_index()
    )

    pivot = grouped.pivot(
        index="scenario",
        columns="objective",
        values="expansion_reduction_pct",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(10, 6),
    )

    ax.set_title("A* Expansion Reduction by Scenario")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Expansion Reduction (%)")
    ax.axhline(0, linewidth=0.8)
    ax.legend(title="Objective")
    ax.grid(axis="y", alpha=0.25)

    save_plot("expansion_reduction_by_scenario.png")


# ============================================================
# 2. RUNTIME SPEEDUP BY SCENARIO
# ============================================================

def plot_runtime_speedup(df):
    grouped = (
        df.groupby(["scenario", "objective"])["speedup"]
        .mean()
        .reset_index()
    )

    pivot = grouped.pivot(
        index="scenario",
        columns="objective",
        values="speedup",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(10, 6),
    )

    ax.set_title("A* Runtime Speedup by Scenario")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Speedup (Dijkstra / A*)")
    ax.axhline(1.0, linewidth=1.2)
    ax.grid(axis="y", alpha=0.25)

    save_plot("runtime_speedup_by_scenario.png")


# ============================================================
# 3. EXPANSION REDUCTION VS RUNTIME SPEEDUP
# ============================================================

def plot_expansion_vs_runtime(df):
    fig, ax = plt.subplots(figsize=(10, 7))

    for objective in sorted(df["objective"].unique()):

        rows = df[df["objective"] == objective]

        ax.scatter(
            rows["expansion_reduction_pct"],
            rows["speedup"],
            alpha=0.45,
            label=objective,
        )

    ax.axhline(
        1.0,
        linewidth=1.2,
        linestyle="--",
    )

    ax.axvline(
        0.0,
        linewidth=0.8,
    )

    ax.set_title(
        "Expansion Reduction vs Runtime Speedup"
    )

    ax.set_xlabel(
        "Expansion Reduction (%)"
    )

    ax.set_ylabel(
        "Runtime Speedup (Dijkstra / A*)"
    )

    ax.grid(alpha=0.25)
    ax.legend()

    save_plot("expansion_vs_runtime.png")


# ============================================================
# 4. OBJECTIVE COMPARISON
# ============================================================

def plot_objective_comparison(df):
    grouped = (
        df.groupby("objective")
        .agg(
            expansion_reduction=(
                "expansion_reduction_pct",
                "mean",
            ),
            speedup=(
                "speedup",
                "mean",
            ),
        )
        .reset_index()
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5),
    )

    axes[0].bar(
        grouped["objective"],
        grouped["expansion_reduction"],
    )

    axes[0].set_title(
        "Average Expansion Reduction"
    )

    axes[0].set_ylabel(
        "Reduction (%)"
    )

    axes[0].grid(
        axis="y",
        alpha=0.25,
    )

    axes[1].bar(
        grouped["objective"],
        grouped["speedup"],
    )

    axes[1].axhline(
        1.0,
        linewidth=1.2,
        linestyle="--",
    )

    axes[1].set_title(
        "Average Runtime Speedup"
    )

    axes[1].set_ylabel(
        "Speedup (Dijkstra / A*)"
    )

    axes[1].grid(
        axis="y",
        alpha=0.25,
    )

    fig.suptitle(
        "A* vs Dijkstra by Objective"
    )

    plt.tight_layout()

    path = PLOTS_DIR / "objective_comparison.png"
    plt.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close()

    print(f"✓ {path}")


# ============================================================
# 5. SIZE SCALING
# ============================================================

def plot_size_scaling(df):
    grouped = (
        df.groupby(
            ["scenario", "size", "objective"]
        )["speedup"]
        .mean()
        .reset_index()
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14, 6),
    )

    scenarios = sorted(
        grouped["scenario"].unique()
    )

    objectives = sorted(
        grouped["objective"].unique()
    )

    for scenario in scenarios:

        for objective in objectives:

            rows = grouped[
                (grouped["scenario"] == scenario)
                & (grouped["objective"] == objective)
            ]

            if rows.empty:
                continue

            axes[0].plot(
                rows["size"],
                rows["speedup"],
                marker="o",
                label=f"{scenario} - {objective}",
            )

    axes[0].axhline(
        1.0,
        linewidth=1.2,
        linestyle="--",
    )

    axes[0].set_title(
        "Runtime Speedup vs Maze Size"
    )

    axes[0].set_xlabel(
        "Maze Size"
    )

    axes[0].set_ylabel(
        "Speedup (Dijkstra / A*)"
    )

    axes[0].grid(alpha=0.25)
    axes[0].legend(
        fontsize=8,
        ncol=2,
    )

    # Expansion reduction
    grouped_exp = (
        df.groupby(
            ["scenario", "size", "objective"]
        )["expansion_reduction_pct"]
        .mean()
        .reset_index()
    )

    for scenario in scenarios:

        for objective in objectives:

            rows = grouped_exp[
                (grouped_exp["scenario"] == scenario)
                & (grouped_exp["objective"] == objective)
            ]

            if rows.empty:
                continue

            axes[1].plot(
                rows["size"],
                rows["expansion_reduction_pct"],
                marker="o",
                label=f"{scenario} - {objective}",
            )

    axes[1].axhline(
        0.0,
        linewidth=0.8,
        linestyle="--",
    )

    axes[1].set_title(
        "Expansion Reduction vs Maze Size"
    )

    axes[1].set_xlabel(
        "Maze Size"
    )

    axes[1].set_ylabel(
        "Expansion Reduction (%)"
    )

    axes[1].grid(alpha=0.25)
    axes[1].legend(
        fontsize=8,
        ncol=2,
    )

    fig.suptitle(
        "A* Scaling with Maze Size"
    )

    plt.tight_layout()

    path = PLOTS_DIR / "size_scaling.png"
    plt.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close()

    print(f"✓ {path}")


# ============================================================
# 6. BEST / WORST CASES
# ============================================================

def plot_best_worst(df):
    best = df.nlargest(
        10,
        "speedup",
    ).copy()

    worst = df.nsmallest(
        10,
        "speedup",
    ).copy()

    best["label"] = (
        best["scenario"]
        + " "
        + best["size"].astype(str)
        + " "
        + best["objective"]
    )

    worst["label"] = (
        worst["scenario"]
        + " "
        + worst["size"].astype(str)
        + " "
        + worst["objective"]
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(15, 7),
    )

    axes[0].barh(
        best["label"],
        best["speedup"],
    )

    axes[0].axvline(
        1.0,
        linewidth=1.2,
        linestyle="--",
    )

    axes[0].set_title(
        "Top 10 A* Cases"
    )

    axes[0].set_xlabel(
        "Runtime Speedup"
    )

    axes[0].invert_yaxis()
    axes[0].grid(
        axis="x",
        alpha=0.25,
    )

    axes[1].barh(
        worst["label"],
        worst["speedup"],
    )

    axes[1].axvline(
        1.0,
        linewidth=1.2,
        linestyle="--",
    )

    axes[1].set_title(
        "Bottom 10 A* Cases"
    )

    axes[1].set_xlabel(
        "Runtime Speedup"
    )

    axes[1].invert_yaxis()
    axes[1].grid(
        axis="x",
        alpha=0.25,
    )

    fig.suptitle(
        "Best vs Worst A* Runtime Cases"
    )

    plt.tight_layout()

    path = PLOTS_DIR / "best_vs_worst_cases.png"
    plt.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close()

    print(f"✓ {path}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("#" * 70)
    print("A* vs DIJKSTRA - LARGE RUNTIME VISUALIZATION")
    print("#" * 70)

    PLOTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("Analysis directory:")
    print(ANALYSIS_DIR)

    df = load_data()

    print(
        f"Loaded {len(df)} benchmark rows."
    )

    print()
    print("Creating plots...")
    print("-" * 70)

    plot_expansion_reduction(df)
    plot_runtime_speedup(df)
    plot_expansion_vs_runtime(df)
    plot_objective_comparison(df)
    plot_size_scaling(df)
    plot_best_worst(df)

    print()
    print("#" * 70)
    print("VISUALIZATION FINISHED")
    print("#" * 70)

    print()
    print("Plots saved to:")
    print(PLOTS_DIR)


if __name__ == "__main__":
    main()

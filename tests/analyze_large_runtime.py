import csv
import statistics
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "results"

RAW_RESULTS_FILE = (
    RESULTS_DIR / "large_runtime_results.csv"
)

RAW_SUMMARY_FILE = (
    RESULTS_DIR / "large_runtime_summary.csv"
)

ANALYSIS_DIR = (
    RESULTS_DIR / "analysis"
)


# ============================================================
# OUTPUT FILES
# ============================================================

NORMALIZED_FILE = (
    ANALYSIS_DIR / "normalized_results.csv"
)

OVERALL_SUMMARY_FILE = (
    ANALYSIS_DIR / "overall_summary.csv"
)

SCENARIO_SUMMARY_FILE = (
    ANALYSIS_DIR / "scenario_summary.csv"
)

OBJECTIVE_SUMMARY_FILE = (
    ANALYSIS_DIR / "objective_summary.csv"
)

SIZE_SUMMARY_FILE = (
    ANALYSIS_DIR / "size_summary.csv"
)

BEST_CASES_FILE = (
    ANALYSIS_DIR / "best_astar_cases.csv"
)

WORST_CASES_FILE = (
    ANALYSIS_DIR / "worst_astar_cases.csv"
)


# ============================================================
# CSV HELPERS
# ============================================================

def read_csv(path):

    with open(
        path,
        "r",
        newline="",
        encoding="utf-8",
    ) as f:

        return list(
            csv.DictReader(f)
        )


def write_csv(
    path,
    rows,
    fieldnames,
):

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# LOAD RAW RESULTS
# ============================================================

def load_results():

    if not RAW_RESULTS_FILE.exists():

        raise FileNotFoundError(
            f"File not found:\n"
            f"{RAW_RESULTS_FILE}"
        )

    rows = read_csv(
        RAW_RESULTS_FILE
    )

    if not rows:

        raise ValueError(
            "large_runtime_results.csv is empty."
        )

    print(
        f"Loaded {len(rows)} benchmark rows."
    )

    return rows


# ============================================================
# NORMALIZE
# ============================================================

def normalize_results(rows):

    normalized = []

    for row in rows:

        d_time = float(
            row["dijkstra_avg_ms"]
        )

        a_time = float(
            row["astar_avg_ms"]
        )

        d_exp = int(
            row["dijkstra_expanded"]
        )

        a_exp = int(
            row["astar_expanded"]
        )

        # ----------------------------------------------------
        # Recalculate instead of blindly trusting CSV
        # ----------------------------------------------------

        if d_exp > 0:

            expansion_reduction = (
                (d_exp - a_exp)
                / d_exp
                * 100
            )

        else:

            expansion_reduction = 0.0

        if a_time > 0:

            speedup = (
                d_time
                / a_time
            )

        else:

            speedup = 0.0

        runtime_change = (
            (a_time - d_time)
            / d_time
            * 100
            if d_time > 0
            else 0.0
        )

        # ----------------------------------------------------
        # Classify result
        # ----------------------------------------------------

        if speedup > 1:

            result = "A* FASTER"

        elif speedup < 1:

            result = "A* SLOWER"

        else:

            result = "SAME"

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        normalized.append(
            {
                "scenario":
                    row["scenario"],

                "size":
                    int(row["size"]),

                "case":
                    int(row["case"]),

                # IMPORTANT:
                # Random/Dense/Weighted -> numeric seed
                # Open -> "OPEN"
                "seed":
                    str(row["seed"]),

                "start":
                    row["start"],

                "goal":
                    row["goal"],

                "objective":
                    row["objective"],

                "dijkstra_cost":
                    float(row["dijkstra_cost"]),

                "astar_cost":
                    float(row["astar_cost"]),

                "dijkstra_expanded":
                    d_exp,

                "astar_expanded":
                    a_exp,

                "dijkstra_avg_ms":
                    d_time,

                "dijkstra_min_ms":
                    float(
                        row["dijkstra_min_ms"]
                    ),

                "dijkstra_max_ms":
                    float(
                        row["dijkstra_max_ms"]
                    ),

                "astar_avg_ms":
                    a_time,

                "astar_min_ms":
                    float(
                        row["astar_min_ms"]
                    ),

                "astar_max_ms":
                    float(
                        row["astar_max_ms"]
                    ),

                "expansion_reduction_pct":
                    expansion_reduction,

                "speedup":
                    speedup,

                "runtime_change_pct":
                    runtime_change,

                "astar_faster":
                    result == "A* FASTER",

                "result":
                    result,
            }
        )

    return normalized


# ============================================================
# GROUPING
# ============================================================

def group_by(rows, key):

    groups = {}

    for row in rows:

        value = row[key]

        if value not in groups:
            groups[value] = []

        groups[value].append(row)

    return groups


# ============================================================
# AGGREGATE
# ============================================================

def aggregate(rows):

    if not rows:
        return None

    d_exp = statistics.mean(
        r["dijkstra_expanded"]
        for r in rows
    )

    a_exp = statistics.mean(
        r["astar_expanded"]
        for r in rows
    )

    reduction = statistics.mean(
        r["expansion_reduction_pct"]
        for r in rows
    )

    d_time = statistics.mean(
        r["dijkstra_avg_ms"]
        for r in rows
    )

    a_time = statistics.mean(
        r["astar_avg_ms"]
        for r in rows
    )

    speedup = (
        d_time / a_time
        if a_time > 0
        else 0
    )

    faster = sum(
        r["speedup"] > 1
        for r in rows
    )

    same = sum(
        r["speedup"] == 1
        for r in rows
    )

    slower = sum(
        r["speedup"] < 1
        for r in rows
    )

    return {
        "cases":
            len(rows),

        "avg_dijkstra_expanded":
            d_exp,

        "avg_astar_expanded":
            a_exp,

        "avg_expansion_reduction_pct":
            reduction,

        "avg_dijkstra_ms":
            d_time,

        "avg_astar_ms":
            a_time,

        "avg_speedup":
            speedup,

        "astar_faster_cases":
            faster,

        "astar_same_cases":
            same,

        "astar_slower_cases":
            slower,

        "best_speedup":
            max(
                r["speedup"]
                for r in rows
            ),

        "median_speedup":
            statistics.median(
                r["speedup"]
                for r in rows
            ),

        "worst_speedup":
            min(
                r["speedup"]
                for r in rows
            ),
    }


# ============================================================
# SCENARIO SUMMARY
# ============================================================

def build_scenario_summary(rows):

    groups = {}

    for row in rows:

        key = (
            row["scenario"],
            row["size"],
            row["objective"],
        )

        groups.setdefault(
            key,
            [],
        ).append(row)

    output = []

    for (
        scenario,
        size,
        objective,
    ), data in groups.items():

        stats = aggregate(data)

        output.append(
            {
                "scenario":
                    scenario,

                "size":
                    size,

                "objective":
                    objective,

                **{
                    key: round(value, 6)
                    if isinstance(
                        value,
                        float,
                    )
                    else value

                    for key, value
                    in stats.items()
                },
            }
        )

    return output


# ============================================================
# OBJECTIVE SUMMARY
# ============================================================

def build_objective_summary(rows):

    groups = group_by(
        rows,
        "objective",
    )

    output = []

    for objective, data in groups.items():

        stats = aggregate(data)

        output.append(
            {
                "objective":
                    objective,

                **{
                    key: round(value, 6)
                    if isinstance(
                        value,
                        float,
                    )
                    else value

                    for key, value
                    in stats.items()
                },
            }
        )

    return output


# ============================================================
# SIZE SUMMARY
# ============================================================

def build_size_summary(rows):

    groups = group_by(
        rows,
        "size",
    )

    output = []

    for size, data in sorted(
        groups.items()
    ):

        stats = aggregate(data)

        output.append(
            {
                "size":
                    size,

                **{
                    key: round(value, 6)
                    if isinstance(
                        value,
                        float,
                    )
                    else value

                    for key, value
                    in stats.items()
                },
            }
        )

    return output


# ============================================================
# OVERALL SUMMARY
# ============================================================

def build_overall_summary(rows):

    stats = aggregate(rows)

    total = len(rows)

    return [
        {
            "metric":
                "total_cases",

            "value":
                total,
        },

        {
            "metric":
                "astar_faster_cases",

            "value":
                stats["astar_faster_cases"],
        },

        {
            "metric":
                "astar_same_cases",

            "value":
                stats["astar_same_cases"],
        },

        {
            "metric":
                "astar_slower_cases",

            "value":
                stats["astar_slower_cases"],
        },

        {
            "metric":
                "astar_faster_pct",

            "value":
                round(
                    stats["astar_faster_cases"]
                    / total
                    * 100,
                    4,
                ),
        },

        {
            "metric":
                "astar_slower_pct",

            "value":
                round(
                    stats["astar_slower_cases"]
                    / total
                    * 100,
                    4,
                ),
        },

        {
            "metric":
                "avg_expansion_reduction_pct",

            "value":
                round(
                    stats[
                        "avg_expansion_reduction_pct"
                    ],
                    6,
                ),
        },

        {
            "metric":
                "avg_runtime_speedup",

            "value":
                round(
                    stats["avg_speedup"],
                    6,
                ),
        },

        {
            "metric":
                "best_speedup",

            "value":
                round(
                    stats["best_speedup"],
                    6,
                ),
        },

        {
            "metric":
                "median_speedup",

            "value":
                round(
                    stats["median_speedup"],
                    6,
                ),
        },

        {
            "metric":
                "worst_speedup",

            "value":
                round(
                    stats["worst_speedup"],
                    6,
                ),
        },
    ]


# ============================================================
# BEST / WORST CASES
# ============================================================

def build_extreme_cases(
    rows,
    count=20,
):

    ranked = sorted(
        rows,
        key=lambda r: r["speedup"],
        reverse=True,
    )

    best = ranked[:count]

    worst = list(
        reversed(
            ranked[-count:]
        )
    )

    return best, worst


# ============================================================
# PRINT
# ============================================================

def print_report(
    overall,
    objective_summary,
    scenario_summary,
):

    print("\n")
    print("#" * 70)
    print("LARGE RUNTIME ANALYSIS")
    print("#" * 70)

    print("\nOVERALL")

    for row in overall:

        print(
            f"{row['metric']:<40}"
            f"{row['value']}"
        )

    print("\nOBJECTIVE SUMMARY")
    print("-" * 70)

    for row in objective_summary:

        print(
            f"{row['objective']:<10} | "
            f"exp reduction="
            f"{row['avg_expansion_reduction_pct']:>7.2f}% | "
            f"speedup="
            f"{row['avg_speedup']:>6.2f}x | "
            f"faster="
            f"{row['astar_faster_cases']:>3} | "
            f"slower="
            f"{row['astar_slower_cases']:>3}"
        )

    print("\nSCENARIO SUMMARY")
    print("-" * 70)

    for row in scenario_summary:

        print(
            f"{row['scenario']:<10} "
            f"{row['size']:>4} | "
            f"{row['objective']:<8} | "
            f"reduction="
            f"{row['avg_expansion_reduction_pct']:>7.2f}% | "
            f"speedup="
            f"{row['avg_speedup']:>6.2f}x"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("#" * 70)
    print("A* vs DIJKSTRA - LARGE RUNTIME ANALYSIS")
    print("#" * 70)

    # --------------------------------------------------------
    # Create analysis directory
    # --------------------------------------------------------

    ANALYSIS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"\nAnalysis directory:"
        f"\n{ANALYSIS_DIR}"
    )

    # --------------------------------------------------------
    # Load raw results
    # --------------------------------------------------------

    rows = load_results()

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    rows = normalize_results(rows)

    print(
        f"Normalized rows: {len(rows)}"
    )

    # --------------------------------------------------------
    # Save normalized data
    # --------------------------------------------------------

    normalized_fields = [
        "scenario",
        "size",
        "case",
        "seed",
        "start",
        "goal",
        "objective",
        "dijkstra_cost",
        "astar_cost",
        "dijkstra_expanded",
        "astar_expanded",
        "dijkstra_avg_ms",
        "dijkstra_min_ms",
        "dijkstra_max_ms",
        "astar_avg_ms",
        "astar_min_ms",
        "astar_max_ms",
        "expansion_reduction_pct",
        "speedup",
        "runtime_change_pct",
        "astar_faster",
        "result",
    ]

    write_csv(
        NORMALIZED_FILE,
        rows,
        normalized_fields,
    )

    # --------------------------------------------------------
    # Build summaries
    # --------------------------------------------------------

    overall = (
        build_overall_summary(rows)
    )

    objective_summary = (
        build_objective_summary(rows)
    )

    scenario_summary = (
        build_scenario_summary(rows)
    )

    size_summary = (
        build_size_summary(rows)
    )

    # --------------------------------------------------------
    # Best / worst
    # --------------------------------------------------------

    best, worst = (
        build_extreme_cases(rows)
    )

    # --------------------------------------------------------
    # Write overall
    # --------------------------------------------------------

    write_csv(
        OVERALL_SUMMARY_FILE,
        overall,
        [
            "metric",
            "value",
        ],
    )

    # --------------------------------------------------------
    # Write objective
    # --------------------------------------------------------

    write_csv(
        OBJECTIVE_SUMMARY_FILE,
        objective_summary,
        list(
            objective_summary[0].keys()
        ),
    )

    # --------------------------------------------------------
    # Write scenario
    # --------------------------------------------------------

    write_csv(
        SCENARIO_SUMMARY_FILE,
        scenario_summary,
        list(
            scenario_summary[0].keys()
        ),
    )

    # --------------------------------------------------------
    # Write size
    # --------------------------------------------------------

    write_csv(
        SIZE_SUMMARY_FILE,
        size_summary,
        list(
            size_summary[0].keys()
        ),
    )

    # --------------------------------------------------------
    # Write best / worst
    # --------------------------------------------------------

    write_csv(
        BEST_CASES_FILE,
        best,
        normalized_fields,
    )

    write_csv(
        WORST_CASES_FILE,
        worst,
        normalized_fields,
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print_report(
        overall,
        objective_summary,
        scenario_summary,
    )

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    print("\n")
    print("#" * 70)
    print("FILES CREATED")
    print("#" * 70)

    files = [
        NORMALIZED_FILE,
        OVERALL_SUMMARY_FILE,
        SCENARIO_SUMMARY_FILE,
        OBJECTIVE_SUMMARY_FILE,
        SIZE_SUMMARY_FILE,
        BEST_CASES_FILE,
        WORST_CASES_FILE,
    ]

    for path in files:

        print(
            f"✓ {path.relative_to(BASE_DIR)}"
        )

    print("\nDONE.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
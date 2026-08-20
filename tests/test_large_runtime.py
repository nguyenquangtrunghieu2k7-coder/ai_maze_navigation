import csv
import math
import random
import statistics
import time
from pathlib import Path

from core.maze import Maze
from core.terrain import Terrain

from core.cost import (
    distance_cost,
    time_cost,
    energy_cost,
)

from algorithms.astar import Astar
from algorithms.dijkstra import Dijkstra

from algorithms.heuristic import (
    euclidean_3d,
    time_heuristic,
    energy_heuristic,
)


# ============================================================
# CONFIG
# ============================================================

BASE_SEED = 20260820

SIZES = [
    101,
    201,
    301,
]

CASES_PER_SIZE = 10

# Number of benchmark runs per algorithm / case
BENCH_RUNS = 5

WALL_PROBABILITY = 0.20

# Start / goal must be sufficiently far apart
MIN_MANHATTAN_RATIO = 0.50


# ============================================================
# OUTPUT
# ============================================================

RESULT_DIR = Path(__file__).parent / "results"
RESULT_DIR.mkdir(exist_ok=True)

CASE_CSV = RESULT_DIR / "large_runtime_results.csv"
SUMMARY_CSV = RESULT_DIR / "large_runtime_summary.csv"


# ============================================================
# OBJECTIVES
# ============================================================

OBJECTIVES = [
    (
        "DISTANCE",
        distance_cost,
        euclidean_3d,
    ),
    (
        "TIME",
        time_cost,
        time_heuristic,
    ),
    (
        "ENERGY",
        energy_cost,
        energy_heuristic,
    ),
]


# ============================================================
# CSV HELPERS
# ============================================================

CASE_FIELDS = [
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

    "astar_faster",
]


SUMMARY_FIELDS = [
    "scenario",
    "size",
    "objective",
    "cases",

    "avg_dijkstra_expanded",
    "avg_astar_expanded",
    "avg_expansion_reduction_pct",

    "avg_dijkstra_ms",
    "avg_astar_ms",
    "avg_speedup",

    "astar_faster_cases",
    "astar_same_cases",
    "astar_slower_cases",

    "best_speedup",
    "median_speedup",
    "worst_speedup",
]


def save_case_results(rows):
    """Save every benchmark case to CSV."""

    with open(
        CASE_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=CASE_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)


def save_summary(rows):
    """Save aggregated benchmark results to CSV."""

    with open(
        SUMMARY_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=SUMMARY_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# RANDOM MAZE
# ============================================================

def build_random_maze(
    size: int,
    seed: int,
    wall_probability: float = WALL_PROBABILITY,
):
    """
    Random maze.

    Border = wall
    Interior = random walkable / wall

    Start / goal are selected from walkable cells
    and must be sufficiently far apart.
    """

    rng = random.Random(seed)

    maze = Maze(size, size)

    for y in range(1, size - 1):
        for x in range(1, size - 1):

            if rng.random() > wall_probability:
                maze.set_walkable(x, y)

    walkable = []

    for y in range(1, size - 1):
        for x in range(1, size - 1):

            cell = maze.get_cell(x, y)

            if cell.walkable:
                walkable.append((x, y))

    if len(walkable) < 2:
        return None

    for _ in range(1000):

        start = rng.choice(walkable)
        goal = rng.choice(walkable)

        if start == goal:
            continue

        distance = (
            abs(start[0] - goal[0])
            + abs(start[1] - goal[1])
        )

        max_distance = 2 * (size - 1)

        if distance >= max_distance * MIN_MANHATTAN_RATIO:

            maze.set_start(*start)
            maze.set_goal(*goal)

            return maze

    return None


# ============================================================
# OPEN MAZE
# ============================================================

def build_open_maze(size: int):
    """
    Almost completely open maze.

    Useful for testing how strongly the heuristic
    guides A* compared with Dijkstra.
    """

    maze = Maze(size, size)

    for y in range(1, size - 1):
        for x in range(1, size - 1):
            maze.set_walkable(x, y)

    start = (1, 1)
    goal = (size - 2, size - 2)

    maze.set_start(*start)
    maze.set_goal(*goal)

    return maze


# ============================================================
# DENSE MAZE
# ============================================================

def build_dense_maze(
    size: int,
    seed: int,
):
    """
    Dense / mostly open random maze.

    Low wall probability means many alternative paths.
    """

    return build_random_maze(
        size,
        seed,
        wall_probability=0.05,
    )


# ============================================================
# WEIGHTED MAZE
# ============================================================

def build_weighted_maze(
    size: int,
    seed: int,
):
    """
    Random maze + terrain + elevation.

    Designed to stress TIME / ENERGY objectives.
    """

    maze = build_random_maze(
        size,
        seed,
        wall_probability=0.15,
    )

    if maze is None:
        return None

    rng = random.Random(seed + 999999)

    terrains = [
        Terrain.ROAD,
        Terrain.GRASS,
        Terrain.SAND,
        Terrain.MUD,
    ]

    for y in range(1, size - 1):
        for x in range(1, size - 1):

            cell = maze.get_cell(x, y)

            if not cell.walkable:
                continue

            cell.terrain = rng.choice(terrains)

            cell.elevation = rng.randint(0, 10)

    return maze


# ============================================================
# VALIDATION
# ============================================================

def validate_result(
    maze,
    result,
    start,
    goal,
    cost_fn,
):
    """
    Verify that the returned path is valid and that
    path_cost matches the actual path cost.
    """

    assert result.found, "Path not found"

    assert result.path[0] == start
    assert result.path[-1] == goal

    calculated = 0.0

    for i in range(len(result.path) - 1):

        x, y = result.path[i]
        nx, ny = result.path[i + 1]

        neighbors = list(
            maze.neighbors(x, y)
        )

        assert (nx, ny) in neighbors

        calculated += cost_fn(
            maze,
            x,
            y,
            nx,
            ny,
        )

    assert math.isclose(
        calculated,
        result.path_cost,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


# ============================================================
# BENCHMARK
# ============================================================

def benchmark_algorithm(
    algorithm,
    maze,
    start,
    goal,
    cost_fn,
    heuristic_fn=None,
):
    """
    Benchmark one algorithm.

    Returns:
        avg
        min
        max
        result
    """

    times = []
    last_result = None

    # --------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------

    if heuristic_fn is None:

        algorithm.search(
            maze,
            start,
            goal,
            cost_fn,
        )

    else:

        algorithm.search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn,
        )

    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    for _ in range(BENCH_RUNS):

        t0 = time.perf_counter()

        if heuristic_fn is None:

            result = algorithm.search(
                maze,
                start,
                goal,
                cost_fn,
            )

        else:

            result = algorithm.search(
                maze,
                start,
                goal,
                cost_fn,
                heuristic_fn,
            )

        t1 = time.perf_counter()

        times.append(
            (t1 - t0) * 1000
        )

        last_result = result

    return {
        "avg": statistics.mean(times),
        "min": min(times),
        "max": max(times),
        "result": last_result,
    }


# ============================================================
# COMPARISON
# ============================================================

def compare(
    maze,
    start,
    goal,
    objective_name,
    cost_fn,
    heuristic_fn,
):
    """
    Compare Dijkstra vs A* for one objective.
    """

    dijkstra = Dijkstra()
    astar = Astar()

    # --------------------------------------------------------
    # Dijkstra
    # --------------------------------------------------------

    d = benchmark_algorithm(
        dijkstra,
        maze,
        start,
        goal,
        cost_fn,
    )

    # --------------------------------------------------------
    # A*
    # --------------------------------------------------------

    a = benchmark_algorithm(
        astar,
        maze,
        start,
        goal,
        cost_fn,
        heuristic_fn,
    )

    d_result = d["result"]
    a_result = a["result"]

    # --------------------------------------------------------
    # Correctness
    # --------------------------------------------------------

    validate_result(
        maze,
        d_result,
        start,
        goal,
        cost_fn,
    )

    validate_result(
        maze,
        a_result,
        start,
        goal,
        cost_fn,
    )

    # Dijkstra and A* must return the same optimal cost
    assert math.isclose(
        d_result.path_cost,
        a_result.path_cost,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    d_exp = d_result.expanded_nodes
    a_exp = a_result.expanded_nodes

    if d_exp > 0:

        expansion_reduction = (
            (d_exp - a_exp)
            / d_exp
            * 100
        )

    else:

        expansion_reduction = 0.0

    speedup = (
        d["avg"] / a["avg"]
        if a["avg"] > 0
        else 0.0
    )

    return {
        "objective": objective_name,

        "d_cost": d_result.path_cost,
        "a_cost": a_result.path_cost,

        "d_exp": d_exp,
        "a_exp": a_exp,

        "d_avg": d["avg"],
        "d_min": d["min"],
        "d_max": d["max"],

        "a_avg": a["avg"],
        "a_min": a["min"],
        "a_max": a["max"],

        "reduction": expansion_reduction,
        "speedup": speedup,
    }


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(result):

    print(
        f"{result['objective']:<8} "
        f"D={result['d_cost']:10.3f} "
        f"A*={result['a_cost']:10.3f} "
        f"D_exp={result['d_exp']:6d} "
        f"A*_exp={result['a_exp']:6d} "
        f"reduction={result['reduction']:6.2f}% "
        f"D_time={result['d_avg']:8.3f} ms "
        f"A*_time={result['a_avg']:8.3f} ms "
        f"speedup={result['speedup']:5.2f}x"
    )


# ============================================================
# AGGREGATE
# ============================================================

def summarize(
    results,
    title,
    scenario,
    size,
    summary_rows,
):
    """
    Print and store summary statistics.
    """

    print()
    print("#" * 70)
    print(title)
    print("#" * 70)

    for objective_name, _, _ in OBJECTIVES:

        rows = [
            r
            for r in results
            if r["objective"] == objective_name
        ]

        if not rows:
            continue

        d_exp = statistics.mean(
            r["d_exp"]
            for r in rows
        )

        a_exp = statistics.mean(
            r["a_exp"]
            for r in rows
        )

        reduction = statistics.mean(
            r["reduction"]
            for r in rows
        )

        d_time = statistics.mean(
            r["d_avg"]
            for r in rows
        )

        a_time = statistics.mean(
            r["a_avg"]
            for r in rows
        )

        speedup = d_time / a_time

        faster = sum(
            r["speedup"] > 1.0
            for r in rows
        )

        slower = sum(
            r["speedup"] < 1.0
            for r in rows
        )

        same = (
            len(rows)
            - faster
            - slower
        )

        best = max(
            r["speedup"]
            for r in rows
        )

        worst = min(
            r["speedup"]
            for r in rows
        )

        median = statistics.median(
            r["speedup"]
            for r in rows
        )

        print()
        print(objective_name)
        print("-" * 70)

        print(
            f"Cases:                 {len(rows)}"
        )

        print(
            f"Average Dijkstra exp:  {d_exp:.2f}"
        )

        print(
            f"Average A* exp:        {a_exp:.2f}"
        )

        print(
            f"Average reduction:     {reduction:.2f}%"
        )

        print(
            f"Average Dijkstra time: {d_time:.4f} ms"
        )

        print(
            f"Average A* time:       {a_time:.4f} ms"
        )

        print(
            f"Average speedup:       {speedup:.2f}x"
        )

        print(
            f"A* faster:             {faster}"
        )

        print(
            f"A* same:               {same}"
        )

        print(
            f"A* slower:             {slower}"
        )

        print(
            f"Best speedup:          {best:.2f}x"
        )

        print(
            f"Median speedup:        {median:.2f}x"
        )

        print(
            f"Worst speedup:         {worst:.2f}x"
        )

        summary_rows.append({
            "scenario": scenario,
            "size": size,
            "objective": objective_name,
            "cases": len(rows),

            "avg_dijkstra_expanded": d_exp,
            "avg_astar_expanded": a_exp,
            "avg_expansion_reduction_pct": reduction,

            "avg_dijkstra_ms": d_time,
            "avg_astar_ms": a_time,
            "avg_speedup": speedup,

            "astar_faster_cases": faster,
            "astar_same_cases": same,
            "astar_slower_cases": slower,

            "best_speedup": best,
            "median_speedup": median,
            "worst_speedup": worst,
        })


# ============================================================
# SAVE CASE
# ============================================================

def append_case_rows(
    case_rows,
    scenario,
    size,
    case_id,
    seed,
    start,
    goal,
    results,
):
    """
    Convert benchmark results into CSV rows.
    """

    for result in results:

        case_rows.append({
            "scenario": scenario,
            "size": size,
            "case": case_id,
            "seed": seed,
            "start": start,
            "goal": goal,
            "objective": result["objective"],

            "dijkstra_cost": result["d_cost"],
            "astar_cost": result["a_cost"],

            "dijkstra_expanded": result["d_exp"],
            "astar_expanded": result["a_exp"],

            "dijkstra_avg_ms": result["d_avg"],
            "dijkstra_min_ms": result["d_min"],
            "dijkstra_max_ms": result["d_max"],

            "astar_avg_ms": result["a_avg"],
            "astar_min_ms": result["a_min"],
            "astar_max_ms": result["a_max"],

            "expansion_reduction_pct": result["reduction"],
            "speedup": result["speedup"],

            "astar_faster": (
                result["speedup"] > 1.0
            ),
        })


# ============================================================
# RANDOM LARGE MAZES
# ============================================================

def run_random_benchmark(
    size,
    case_rows,
    summary_rows,
):

    print()
    print("=" * 70)
    print(
        f"RANDOM MAZE: {size} x {size}"
    )
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED

    while generated < CASES_PER_SIZE:

        current_seed = seed

        maze = build_random_maze(
            size,
            current_seed,
        )

        seed += 1

        if maze is None:
            continue

        start = maze.start
        goal = maze.goal

        case_results = []

        try:

            for (
                objective_name,
                cost_fn,
                heuristic_fn,
            ) in OBJECTIVES:

                result = compare(
                    maze,
                    start,
                    goal,
                    objective_name,
                    cost_fn,
                    heuristic_fn,
                )

                case_results.append(result)

        except AssertionError:

            continue

        generated += 1

        print(
            f"\nCASE {generated:02d} "
            f"| seed={current_seed} "
            f"| start={start} "
            f"| goal={goal}"
        )

        for result in case_results:

            print_result(result)

            results.append(result)

        append_case_rows(
            case_rows,
            "RANDOM",
            size,
            generated,
            current_seed,
            start,
            goal,
            case_results,
        )

    summarize(
        results,
        f"RANDOM MAZE SUMMARY - {size} x {size}",
        "RANDOM",
        size,
        summary_rows,
    )

    return results


# ============================================================
# OPEN MAZE
# ============================================================

def run_open_benchmark(
    size,
    case_rows,
    summary_rows,
):

    print()
    print("=" * 70)
    print(
        f"OPEN MAZE: {size} x {size}"
    )
    print("=" * 70)

    maze = build_open_maze(size)

    start = maze.start
    goal = maze.goal

    results = []

    for (
        objective_name,
        cost_fn,
        heuristic_fn,
    ) in OBJECTIVES:

        result = compare(
            maze,
            start,
            goal,
            objective_name,
            cost_fn,
            heuristic_fn,
        )

        print_result(result)

        results.append(result)

    append_case_rows(
        case_rows,
        "OPEN",
        size,
        1,
        "OPEN",
        start,
        goal,
        results,
    )

    summarize(
        results,
        f"OPEN MAZE SUMMARY - {size} x {size}",
        "OPEN",
        size,
        summary_rows,
    )

    return results


# ============================================================
# DENSE MAZE
# ============================================================

def run_dense_benchmark(
    size,
    case_rows,
    summary_rows,
):

    print()
    print("=" * 70)
    print(
        f"DENSE RANDOM MAZE: {size} x {size}"
    )
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED + 50000

    while generated < CASES_PER_SIZE:

        current_seed = seed

        maze = build_dense_maze(
            size,
            current_seed,
        )

        seed += 1

        if maze is None:
            continue

        start = maze.start
        goal = maze.goal

        case_results = []

        try:

            for (
                objective_name,
                cost_fn,
                heuristic_fn,
            ) in OBJECTIVES:

                result = compare(
                    maze,
                    start,
                    goal,
                    objective_name,
                    cost_fn,
                    heuristic_fn,
                )

                case_results.append(result)

        except AssertionError:

            continue

        generated += 1

        print(
            f"\nCASE {generated:02d} "
            f"| seed={current_seed} "
            f"| start={start} "
            f"| goal={goal}"
        )

        for result in case_results:

            print_result(result)

            results.append(result)

        append_case_rows(
            case_rows,
            "DENSE",
            size,
            generated,
            current_seed,
            start,
            goal,
            case_results,
        )

    summarize(
        results,
        f"DENSE MAZE SUMMARY - {size} x {size}",
        "DENSE",
        size,
        summary_rows,
    )

    return results


# ============================================================
# WEIGHTED MAZE
# ============================================================

def run_weighted_benchmark(
    size,
    case_rows,
    summary_rows,
):

    print()
    print("=" * 70)
    print(
        f"WEIGHTED MAZE: {size} x {size}"
    )
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED + 100000

    while generated < CASES_PER_SIZE:

        current_seed = seed

        maze = build_weighted_maze(
            size,
            current_seed,
        )

        seed += 1

        if maze is None:
            continue

        start = maze.start
        goal = maze.goal

        case_results = []

        try:

            for (
                objective_name,
                cost_fn,
                heuristic_fn,
            ) in OBJECTIVES:

                result = compare(
                    maze,
                    start,
                    goal,
                    objective_name,
                    cost_fn,
                    heuristic_fn,
                )

                case_results.append(result)

        except AssertionError:

            continue

        generated += 1

        print(
            f"\nCASE {generated:02d} "
            f"| seed={current_seed} "
            f"| start={start} "
            f"| goal={goal}"
        )

        for result in case_results:

            print_result(result)

            results.append(result)

        append_case_rows(
            case_rows,
            "WEIGHTED",
            size,
            generated,
            current_seed,
            start,
            goal,
            case_results,
        )

    summarize(
        results,
        f"WEIGHTED MAZE SUMMARY - {size} x {size}",
        "WEIGHTED",
        size,
        summary_rows,
    )

    return results


# ============================================================
# FINAL SUMMARY
# ============================================================

def final_summary(
    all_results,
    summary_rows,
):

    print()
    print("#" * 70)
    print("FINAL LARGE RUNTIME SUMMARY")
    print("#" * 70)

    for objective_name, _, _ in OBJECTIVES:

        rows = [
            r
            for r in all_results
            if r["objective"] == objective_name
        ]

        if not rows:
            continue

        d_time = statistics.mean(
            r["d_avg"]
            for r in rows
        )

        a_time = statistics.mean(
            r["a_avg"]
            for r in rows
        )

        d_exp = statistics.mean(
            r["d_exp"]
            for r in rows
        )

        a_exp = statistics.mean(
            r["a_exp"]
            for r in rows
        )

        speedup = d_time / a_time

        reduction = (
            (d_exp - a_exp)
            / d_exp
            * 100
        )

        faster = sum(
            r["speedup"] > 1
            for r in rows
        )

        slower = sum(
            r["speedup"] < 1
            for r in rows
        )

        same = (
            len(rows)
            - faster
            - slower
        )

        best = max(
            r["speedup"]
            for r in rows
        )

        median = statistics.median(
            r["speedup"]
            for r in rows
        )

        worst = min(
            r["speedup"]
            for r in rows
        )

        print()
        print(objective_name)

        print(
            f"  Dijkstra avg time : "
            f"{d_time:.4f} ms"
        )

        print(
            f"  A* avg time       : "
            f"{a_time:.4f} ms"
        )

        print(
            f"  Runtime speedup   : "
            f"{speedup:.2f}x"
        )

        print(
            f"  Dijkstra avg exp  : "
            f"{d_exp:.2f}"
        )

        print(
            f"  A* avg exp        : "
            f"{a_exp:.2f}"
        )

        print(
            f"  Expansion reduce  : "
            f"{reduction:.2f}%"
        )

        print(
            f"  A* faster cases   : "
            f"{faster}/{len(rows)}"
        )

        print(
            f"  A* same cases     : "
            f"{same}/{len(rows)}"
        )

        print(
            f"  A* slower cases   : "
            f"{slower}/{len(rows)}"
        )

        print(
            f"  Best speedup      : "
            f"{best:.2f}x"
        )

        print(
            f"  Median speedup    : "
            f"{median:.2f}x"
        )

        print(
            f"  Worst speedup     : "
            f"{worst:.2f}x"
        )

    print()
    print("#" * 70)
    print("CSV RESULTS")
    print("#" * 70)

    print(
        f"Case results : {CASE_CSV}"
    )

    print(
        f"Summary      : {SUMMARY_CSV}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("#" * 70)
    print("A* vs DIJKSTRA - LARGE RUNTIME STRESS TEST")
    print("#" * 70)

    print()
    print("Configuration")
    print("-" * 70)
    print("Sizes:", SIZES)
    print("Cases / size:", CASES_PER_SIZE)
    print("Benchmark runs:", BENCH_RUNS)
    print("Wall probability:", WALL_PROBABILITY)
    print("Base seed:", BASE_SEED)

    case_rows = []
    summary_rows = []
    all_results = []

    # ========================================================
    # RANDOM
    # ========================================================

    for size in SIZES:

        results = run_random_benchmark(
            size,
            case_rows,
            summary_rows,
        )

        all_results.extend(results)

        # Save progressively
        save_case_results(case_rows)
        save_summary(summary_rows)

    # ========================================================
    # OPEN
    # ========================================================

    for size in SIZES:

        results = run_open_benchmark(
            size,
            case_rows,
            summary_rows,
        )

        all_results.extend(results)

        save_case_results(case_rows)
        save_summary(summary_rows)

    # ========================================================
    # DENSE
    # ========================================================

    for size in SIZES:

        results = run_dense_benchmark(
            size,
            case_rows,
            summary_rows,
        )

        all_results.extend(results)

        save_case_results(case_rows)
        save_summary(summary_rows)

    # ========================================================
    # WEIGHTED
    # ========================================================

    for size in SIZES:

        results = run_weighted_benchmark(
            size,
            case_rows,
            summary_rows,
        )

        all_results.extend(results)

        save_case_results(case_rows)
        save_summary(summary_rows)

    # ========================================================
    # FINAL
    # ========================================================

    final_summary(
        all_results,
        summary_rows,
    )

    # Final save
    save_case_results(case_rows)
    save_summary(summary_rows)

    print()
    print("#" * 70)
    print("LARGE RUNTIME BENCHMARK FINISHED")
    print("#" * 70)
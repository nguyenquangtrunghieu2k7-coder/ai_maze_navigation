import random
import time
import statistics
import math
import csv
import sys
from pathlib import Path
from datetime import datetime

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
BENCH_RUNS = 5

WALL_PROBABILITY = 0.20
MIN_MANHATTAN_RATIO = 0.50

# ============================================================
# RESULT DIRECTORY
# ============================================================

RESULT_ROOT = (
    Path(__file__).parent
    / "results"
    / "large_runtime"
)

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

RESULT_DIR = RESULT_ROOT / RUN_ID

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


RAW_CSV = RESULT_DIR / "raw_results.csv"
SUMMARY_CSV = RESULT_DIR / "summary.csv"
CASE_SUMMARY_CSV = RESULT_DIR / "case_summary.csv"
BEST_CSV = RESULT_DIR / "best_cases.csv"
WORST_CSV = RESULT_DIR / "worst_cases.csv"
CONFIG_FILE = RESULT_DIR / "config.txt"
TERMINAL_FILE = RESULT_DIR / "terminal_output.txt"


# ============================================================
# TERMINAL LOGGER
# ============================================================

class Tee:
    """
    In ra terminal đồng thời ghi vào file.
    """

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


terminal_file = open(
    TERMINAL_FILE,
    "w",
    encoding="utf-8",
)

original_stdout = sys.stdout

sys.stdout = Tee(
    original_stdout,
    terminal_file,
)


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

RAW_FIELDS = [
    "size",
    "maze_type",
    "case",
    "seed",
    "start_x",
    "start_y",
    "goal_x",
    "goal_y",
    "objective",
    "d_cost",
    "a_cost",
    "d_exp",
    "a_exp",
    "expansion_reduction",
    "d_avg_ms",
    "d_min_ms",
    "d_max_ms",
    "a_avg_ms",
    "a_min_ms",
    "a_max_ms",
    "speedup",
]


CASE_FIELDS = [
    "size",
    "maze_type",
    "case",
    "seed",
    "start_x",
    "start_y",
    "goal_x",
    "goal_y",
    "distance_d_speedup",
    "time_d_speedup",
    "energy_d_speedup",
    "distance_reduction",
    "time_reduction",
    "energy_reduction",
]


SUMMARY_FIELDS = [
    "maze_type",
    "size",
    "objective",
    "cases",
    "avg_dijkstra_exp",
    "avg_astar_exp",
    "avg_reduction",
    "avg_dijkstra_ms",
    "avg_astar_ms",
    "avg_speedup",
    "median_speedup",
    "best_speedup",
    "worst_speedup",
    "astar_faster",
    "astar_same",
    "astar_slower",
]


def write_csv_header(path, fields):
    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )
        writer.writeheader()


write_csv_header(RAW_CSV, RAW_FIELDS)
write_csv_header(CASE_SUMMARY_CSV, CASE_FIELDS)
write_csv_header(SUMMARY_CSV, SUMMARY_FIELDS)


def append_csv(path, fields, row):
    with open(
        path,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )
        writer.writerow(row)


# ============================================================
# CONFIG FILE
# ============================================================

with open(
    CONFIG_FILE,
    "w",
    encoding="utf-8",
) as f:

    f.write("A* vs DIJKSTRA LARGE RUNTIME EXPERIMENT\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"Run ID: {RUN_ID}\n")
    f.write(f"Base seed: {BASE_SEED}\n")
    f.write(f"Sizes: {SIZES}\n")
    f.write(f"Cases per size: {CASES_PER_SIZE}\n")
    f.write(f"Benchmark runs: {BENCH_RUNS}\n")
    f.write(
        f"Wall probability: "
        f"{WALL_PROBABILITY}\n"
    )
    f.write(
        f"Min Manhattan ratio: "
        f"{MIN_MANHATTAN_RATIO}\n"
    )

    f.write("\nMaze types:\n")
    f.write("- random\n")
    f.write("- open\n")
    f.write("- dense\n")
    f.write("- weighted\n")


# ============================================================
# RANDOM MAZE
# ============================================================

def build_random_maze(
    size: int,
    seed: int,
    wall_probability: float = WALL_PROBABILITY,
):

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

        if (
            distance
            >= max_distance * MIN_MANHATTAN_RATIO
        ):

            maze.set_start(*start)
            maze.set_goal(*goal)

            return maze

    return None


# ============================================================
# OPEN MAZE
# ============================================================

def build_open_maze(size: int):

    maze = Maze(size, size)

    for y in range(1, size - 1):

        for x in range(1, size - 1):

            maze.set_walkable(x, y)

    maze.set_start(1, 1)
    maze.set_goal(
        size - 2,
        size - 2,
    )

    return maze


# ============================================================
# DENSE MAZE
# ============================================================

def build_dense_maze(
    size: int,
    seed: int,
):

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

    maze = build_random_maze(
        size,
        seed,
        wall_probability=0.15,
    )

    if maze is None:
        return None

    rng = random.Random(
        seed + 999999
    )

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

            cell.terrain = rng.choice(
                terrains
            )

            cell.elevation = rng.randint(
                0,
                10,
            )

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

    assert result.found, (
        "Path not found"
    )

    assert result.path[0] == start
    assert result.path[-1] == goal

    calculated = 0.0

    for i in range(
        len(result.path) - 1
    ):

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

    dijkstra = Dijkstra()
    astar = Astar()

    d = benchmark_algorithm(
        dijkstra,
        maze,
        start,
        goal,
        cost_fn,
    )

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

    reduction = 0.0

    if d_exp > 0:

        reduction = (
            (d_exp - a_exp)
            / d_exp
            * 100
        )

    speedup = (
        d["avg"] / a["avg"]
        if a["avg"] > 0
        else 0
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

        "reduction": reduction,
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
        f"reduction="
        f"{result['reduction']:6.2f}% "
        f"D_time="
        f"{result['d_avg']:8.3f} ms "
        f"A*_time="
        f"{result['a_avg']:8.3f} ms "
        f"speedup="
        f"{result['speedup']:5.2f}x"
    )


# ============================================================
# SAVE RAW RESULT
# ============================================================

def save_raw(
    result,
    size,
    maze_type,
    case,
    seed,
    start,
    goal,
):

    row = {
        "size": size,
        "maze_type": maze_type,
        "case": case,
        "seed": seed,

        "start_x": start[0],
        "start_y": start[1],

        "goal_x": goal[0],
        "goal_y": goal[1],

        "objective": result["objective"],

        "d_cost": result["d_cost"],
        "a_cost": result["a_cost"],

        "d_exp": result["d_exp"],
        "a_exp": result["a_exp"],

        "expansion_reduction":
            result["reduction"],

        "d_avg_ms": result["d_avg"],
        "d_min_ms": result["d_min"],
        "d_max_ms": result["d_max"],

        "a_avg_ms": result["a_avg"],
        "a_min_ms": result["a_min"],
        "a_max_ms": result["a_max"],

        "speedup": result["speedup"],
    }

    append_csv(
        RAW_CSV,
        RAW_FIELDS,
        row,
    )


# ============================================================
# RUN RANDOM / DENSE / WEIGHTED
# ============================================================

def run_random_like(
    size,
    maze_type,
    builder,
    seed_offset,
):

    print()
    print("=" * 70)
    print(
        f"{maze_type.upper()} MAZE: "
        f"{size} x {size}"
    )
    print("=" * 70)

    results = []

    generated = 0
    seed = (
        BASE_SEED
        + seed_offset
    )

    while generated < CASES_PER_SIZE:

        current_seed = seed
        seed += 1

        maze = builder(
            size,
            current_seed,
        )

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

                case_results.append(
                    result
                )

        except AssertionError:

            print(
                f"SKIP seed={current_seed}"
                " - invalid/no path"
            )

            continue

        generated += 1

        print()
        print(
            f"CASE {generated:02d} "
            f"| seed={current_seed} "
            f"| start={start} "
            f"| goal={goal}"
        )

        for result in case_results:

            print_result(result)

            save_raw(
                result,
                size,
                maze_type,
                generated,
                current_seed,
                start,
                goal,
            )

            results.append(result)

    return results


# ============================================================
# OPEN MAZE
# ============================================================

def run_open(size):

    print()
    print("=" * 70)
    print(
        f"OPEN MAZE: "
        f"{size} x {size}"
    )
    print("=" * 70)

    maze = build_open_maze(size)

    start = maze.start
    goal = maze.goal

    results = []

    case = 1
    seed = 0

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

        save_raw(
            result,
            size,
            "open",
            case,
            seed,
            start,
            goal,
        )

        results.append(result)

    return results


# ============================================================
# SUMMARY
# ============================================================

def make_summary_rows(
    all_results,
):

    rows = []

    groups = {}

    for item in all_results:

        key = (
            item["maze_type"],
            item["size"],
            item["objective"],
        )

        groups.setdefault(
            key,
            [],
        ).append(item)

    for (
        maze_type,
        size,
        objective,
    ), items in groups.items():

        d_exp = statistics.mean(
            x["d_exp"]
            for x in items
        )

        a_exp = statistics.mean(
            x["a_exp"]
            for x in items
        )

        reduction = statistics.mean(
            x["reduction"]
            for x in items
        )

        d_time = statistics.mean(
            x["d_avg"]
            for x in items
        )

        a_time = statistics.mean(
            x["a_avg"]
            for x in items
        )

        speedup = (
            d_time / a_time
            if a_time > 0
            else 0
        )

        speedups = [
            x["speedup"]
            for x in items
        ]

        faster = sum(
            x > 1
            for x in speedups
        )

        slower = sum(
            x < 1
            for x in speedups
        )

        same = (
            len(items)
            - faster
            - slower
        )

        row = {
            "maze_type": maze_type,
            "size": size,
            "objective": objective,
            "cases": len(items),

            "avg_dijkstra_exp": d_exp,
            "avg_astar_exp": a_exp,
            "avg_reduction": reduction,

            "avg_dijkstra_ms": d_time,
            "avg_astar_ms": a_time,

            "avg_speedup": speedup,

            "median_speedup":
                statistics.median(
                    speedups
                ),

            "best_speedup":
                max(speedups),

            "worst_speedup":
                min(speedups),

            "astar_faster": faster,
            "astar_same": same,
            "astar_slower": slower,
        }

        rows.append(row)

    return rows


def save_summary(rows):

    for row in rows:

        append_csv(
            SUMMARY_CSV,
            SUMMARY_FIELDS,
            row,
        )


def print_summary(
    rows,
    title,
):

    print()
    print("#" * 70)
    print(title)
    print("#" * 70)

    for row in rows:

        print()
        print(
            f"{row['maze_type'].upper()} "
            f"{row['size']}x{row['size']} "
            f"- {row['objective']}"
        )

        print(
            f"Cases:                 "
            f"{row['cases']}"
        )

        print(
            f"Average Dijkstra exp:  "
            f"{row['avg_dijkstra_exp']:.2f}"
        )

        print(
            f"Average A* exp:        "
            f"{row['avg_astar_exp']:.2f}"
        )

        print(
            f"Average reduction:     "
            f"{row['avg_reduction']:.2f}%"
        )

        print(
            f"Average Dijkstra time: "
            f"{row['avg_dijkstra_ms']:.4f} ms"
        )

        print(
            f"Average A* time:       "
            f"{row['avg_astar_ms']:.4f} ms"
        )

        print(
            f"Average speedup:       "
            f"{row['avg_speedup']:.2f}x"
        )

        print(
            f"A* faster:             "
            f"{row['astar_faster']}"
        )

        print(
            f"A* same:               "
            f"{row['astar_same']}"
        )

        print(
            f"A* slower:             "
            f"{row['astar_slower']}"
        )

        print(
            f"Best speedup:          "
            f"{row['best_speedup']:.2f}x"
        )

        print(
            f"Median speedup:        "
            f"{row['median_speedup']:.2f}x"
        )

        print(
            f"Worst speedup:         "
            f"{row['worst_speedup']:.2f}x"
        )


# ============================================================
# CASE SUMMARY
# ============================================================

def save_case_summaries(
    all_results,
):

    groups = {}

    for result in all_results:

        key = (
            result["maze_type"],
            result["size"],
            result["case"],
            result["seed"],
            result["start"],
            result["goal"],
        )

        groups.setdefault(
            key,
            [],
        ).append(result)

    for (
        maze_type,
        size,
        case,
        seed,
        start,
        goal,
    ), items in groups.items():

        values = {
            x["objective"]: x
            for x in items
        }

        row = {
            "size": size,
            "maze_type": maze_type,
            "case": case,
            "seed": seed,

            "start_x": start[0],
            "start_y": start[1],

            "goal_x": goal[0],
            "goal_y": goal[1],

            "distance_d_speedup":
                values.get(
                    "DISTANCE",
                    {},
                ).get(
                    "speedup",
                    "",
                ),

            "time_d_speedup":
                values.get(
                    "TIME",
                    {},
                ).get(
                    "speedup",
                    "",
                ),

            "energy_d_speedup":
                values.get(
                    "ENERGY",
                    {},
                ).get(
                    "speedup",
                    "",
                ),

            "distance_reduction":
                values.get(
                    "DISTANCE",
                    {},
                ).get(
                    "reduction",
                    "",
                ),

            "time_reduction":
                values.get(
                    "TIME",
                    {},
                ).get(
                    "reduction",
                    "",
                ),

            "energy_reduction":
                values.get(
                    "ENERGY",
                    {},
                ).get(
                    "reduction",
                    "",
                ),
        }

        append_csv(
            CASE_SUMMARY_CSV,
            CASE_FIELDS,
            row,
        )


# ============================================================
# BEST / WORST CASES
# ============================================================

def save_extreme_cases(
    all_results,
):

    sorted_results = sorted(
        all_results,
        key=lambda x: x["speedup"],
        reverse=True,
    )

    best = sorted_results[:20]
    worst = sorted_results[-20:]

    fields = [
        "size",
        "maze_type",
        "case",
        "seed",
        "objective",
        "speedup",
        "reduction",
        "d_avg_ms",
        "a_avg_ms",
        "d_exp",
        "a_exp",
    ]

    write_csv_header(
        BEST_CSV,
        fields,
    )

    write_csv_header(
        WORST_CSV,
        fields,
    )

    for path, items in [
        (BEST_CSV, best),
        (WORST_CSV, worst),
    ]:

        for x in items:

            row = {
                "size": x["size"],
                "maze_type": x["maze_type"],
                "case": x["case"],
                "seed": x["seed"],
                "objective": x["objective"],
                "speedup": x["speedup"],
                "reduction": x["reduction"],
                "d_avg_ms": x["d_avg"],
                "a_avg_ms": x["a_avg"],
                "d_exp": x["d_exp"],
                "a_exp": x["a_exp"],
            }

            append_csv(
                path,
                fields,
                row,
            )


# ============================================================
# FINAL SUMMARY
# ============================================================

def print_final_summary(
    all_results,
):

    print()
    print("#" * 70)
    print("FINAL LARGE RUNTIME SUMMARY")
    print("#" * 70)

    for objective_name, _, _ in OBJECTIVES:

        rows = [
            x
            for x in all_results
            if x["objective"]
            == objective_name
        ]

        if not rows:
            continue

        d_time = statistics.mean(
            x["d_avg"]
            for x in rows
        )

        a_time = statistics.mean(
            x["a_avg"]
            for x in rows
        )

        d_exp = statistics.mean(
            x["d_exp"]
            for x in rows
        )

        a_exp = statistics.mean(
            x["a_exp"]
            for x in rows
        )

        speedup = (
            d_time / a_time
        )

        reduction = (
            (d_exp - a_exp)
            / d_exp
            * 100
        )

        faster = sum(
            x["speedup"] > 1
            for x in rows
        )

        slower = sum(
            x["speedup"] < 1
            for x in rows
        )

        same = (
            len(rows)
            - faster
            - slower
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


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("#" * 70)
    print(
        "A* vs DIJKSTRA "
        "LARGE RUNTIME STRESS TEST"
    )
    print("#" * 70)

    print()
    print("Configuration")
    print("-" * 70)
    print("Sizes:", SIZES)
    print(
        "Cases / size:",
        CASES_PER_SIZE,
    )
    print(
        "Benchmark runs:",
        BENCH_RUNS,
    )
    print(
        "Wall probability:",
        WALL_PROBABILITY,
    )
    print(
        "Base seed:",
        BASE_SEED,
    )

    print()
    print("Results directory:")
    print(RESULT_DIR)

    all_results = []

    # ========================================================
    # RANDOM
    # ========================================================

    for size in SIZES:

        results = run_random_like(
            size,
            "random",
            build_random_maze,
            0,
        )

        for result in results:
            result["maze_type"] = "random"
            result["size"] = size

            # Metadata được thêm ở đây
            # để summary xử lý.

        all_results.extend(results)

    # ========================================================
    # OPEN
    # ========================================================

    for size in SIZES:

        results = run_open(size)

        for result in results:

            result["maze_type"] = "open"
            result["size"] = size
            result["case"] = 1
            result["seed"] = 0
            result["start"] = (1, 1)
            result["goal"] = (
                size - 2,
                size - 2,
            )

        all_results.extend(results)

    # ========================================================
    # DENSE
    # ========================================================

    for size in SIZES:

        results = run_random_like(
            size,
            "dense",
            build_dense_maze,
            50000,
        )

        for result in results:
            result["maze_type"] = "dense"
            result["size"] = size

        all_results.extend(results)

    # ========================================================
    # WEIGHTED
    # ========================================================

    for size in SIZES:

        results = run_random_like(
            size,
            "weighted",
            build_weighted_maze,
            100000,
        )

        for result in results:
            result["maze_type"] = "weighted"
            result["size"] = size

        all_results.extend(results)

    # ========================================================
    # SUMMARIES
    # ========================================================

    summary_rows = make_summary_rows(
        all_results
    )

    save_summary(summary_rows)

    print_summary(
        summary_rows,
        "GROUPED SUMMARY",
    )

    save_case_summaries(
        all_results
    )

    save_extreme_cases(
        all_results
    )

    print_final_summary(
        all_results
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("#" * 70)
    print("LARGE RUNTIME BENCHMARK FINISHED")
    print("#" * 70)

    print()
    print(
        f"Total result rows: "
        f"{len(all_results)}"
    )

    print()
    print("Files saved:")
    print(
        f"  raw_results.csv     -> "
        f"{RAW_CSV}"
    )
    print(
        f"  summary.csv         -> "
        f"{SUMMARY_CSV}"
    )
    print(
        f"  case_summary.csv    -> "
        f"{CASE_SUMMARY_CSV}"
    )
    print(
        f"  best_cases.csv      -> "
        f"{BEST_CSV}"
    )
    print(
        f"  worst_cases.csv     -> "
        f"{WORST_CSV}"
    )
    print(
        f"  config.txt          -> "
        f"{CONFIG_FILE}"
    )
    print(
        f"  terminal_output.txt -> "
        f"{TERMINAL_FILE}"
    )


# ============================================================
# RUN
# ============================================================

try:

    if __name__ == "__main__":
        main()

finally:

    sys.stdout = original_stdout

    terminal_file.close()
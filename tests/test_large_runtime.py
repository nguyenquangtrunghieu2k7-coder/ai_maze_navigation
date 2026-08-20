import random
import time
import statistics
import math

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

# Nếu máy chạy khỏe có thể tăng lên:
SIZES = [
    101,
    201,
    301,
]

CASES_PER_SIZE = 10

# Số lần benchmark mỗi algorithm / case
BENCH_RUNS = 5

WALL_PROBABILITY = 0.20

# Chỉ lấy start/goal đủ xa nhau
MIN_MANHATTAN_RATIO = 0.50


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

    Sau đó đảm bảo start và goal là walkable.
    """

    rng = random.Random(seed)

    maze = Maze(size, size)

    for y in range(1, size - 1):
        for x in range(1, size - 1):

            if rng.random() > wall_probability:
                maze.set_walkable(x, y)

    # Random start / goal
    walkable = []

    for y in range(1, size - 1):
        for x in range(1, size - 1):

            cell = maze.get_cell(x, y)

            if cell.walkable:
                walkable.append((x, y))

    if len(walkable) < 2:
        return None

    # Tìm start / goal đủ xa nhau
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
    Gần như toàn bộ maze là walkable.

    Đây là case rất tốt để xem heuristic có thực sự
    giúp A* định hướng hay không.
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

def build_dense_maze(size: int, seed: int):
    """
    Nhiều đường đi nhưng vẫn giữ tỷ lệ wall thấp.
    """

    return build_random_maze(
        size,
        seed,
        wall_probability=0.05,
    )


# ============================================================
# WEIGHTED MAZE
# ============================================================

def build_weighted_maze(size: int, seed: int):
    """
    Maze random + terrain + elevation.

    Dùng để stress TIME / ENERGY heuristic.
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

            # elevation 0 -> 10
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
    Correctness check.

    Benchmark chỉ có ý nghĩa nếu cả 2 algorithm
    thực sự trả về optimal path.
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
    Benchmark một algorithm.

    Trả về:
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
    Compare Dijkstra vs A*.
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

    # Optimal cost must match
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

    expansion_reduction = 0.0

    if d_exp > 0:
        expansion_reduction = (
            (d_exp - a_exp)
            / d_exp
            * 100
        )

    speedup = (
        d["avg"]
        / a["avg"]
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

def summarize(results, title):

    print("\n")
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
            r["d_exp"] for r in rows
        )

        a_exp = statistics.mean(
            r["a_exp"] for r in rows
        )

        reduction = statistics.mean(
            r["reduction"] for r in rows
        )

        d_time = statistics.mean(
            r["d_avg"] for r in rows
        )

        a_time = statistics.mean(
            r["a_avg"] for r in rows
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

        same = len(rows) - faster - slower

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


# ============================================================
# RANDOM LARGE MAZES
# ============================================================

def run_random_benchmark(size):

    print("\n")
    print("=" * 70)
    print(f"RANDOM MAZE: {size} x {size}")
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED

    while generated < CASES_PER_SIZE:

        maze = build_random_maze(
            size,
            seed,
        )

        seed += 1

        if maze is None:
            continue

        start = maze.start
        goal = maze.goal

        # ----------------------------------------------------
        # Run all objectives
        # ----------------------------------------------------

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

            # No path / invalid case
            continue

        generated += 1

        print(
            f"\nCASE {generated:02d} "
            f"| seed={seed - 1} "
            f"| start={start} "
            f"| goal={goal}"
        )

        for result in case_results:
            print_result(result)
            results.append(result)

    summarize(
        results,
        f"RANDOM MAZE SUMMARY - {size} x {size}",
    )

    return results


# ============================================================
# OPEN MAZE
# ============================================================

def run_open_benchmark(size):

    print("\n")
    print("=" * 70)
    print(f"OPEN MAZE: {size} x {size}")
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

    summarize(
        results,
        f"OPEN MAZE SUMMARY - {size} x {size}",
    )

    return results


# ============================================================
# DENSE MAZE
# ============================================================

def run_dense_benchmark(size):

    print("\n")
    print("=" * 70)
    print(f"DENSE / OPEN RANDOM MAZE: {size} x {size}")
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED + 50000

    while generated < CASES_PER_SIZE:

        maze = build_dense_maze(
            size,
            seed,
        )

        seed += 1

        if maze is None:
            continue

        try:

            case_results = []

            for (
                objective_name,
                cost_fn,
                heuristic_fn,
            ) in OBJECTIVES:

                result = compare(
                    maze,
                    maze.start,
                    maze.goal,
                    objective_name,
                    cost_fn,
                    heuristic_fn,
                )

                case_results.append(result)

        except AssertionError:

            continue

        generated += 1

        print(
            f"\nCASE {generated:02d}"
            f" | seed={seed - 1}"
            f" | start={maze.start}"
            f" | goal={maze.goal}"
        )

        for result in case_results:

            print_result(result)

            results.append(result)

    summarize(
        results,
        f"DENSE MAZE SUMMARY - {size} x {size}",
    )

    return results


# ============================================================
# WEIGHTED MAZE
# ============================================================

def run_weighted_benchmark(size):

    print("\n")
    print("=" * 70)
    print(f"WEIGHTED MAZE: {size} x {size}")
    print("=" * 70)

    results = []

    generated = 0
    seed = BASE_SEED + 100000

    while generated < CASES_PER_SIZE:

        maze = build_weighted_maze(
            size,
            seed,
        )

        seed += 1

        if maze is None:
            continue

        try:

            case_results = []

            for (
                objective_name,
                cost_fn,
                heuristic_fn,
            ) in OBJECTIVES:

                result = compare(
                    maze,
                    maze.start,
                    maze.goal,
                    objective_name,
                    cost_fn,
                    heuristic_fn,
                )

                case_results.append(result)

        except AssertionError:

            continue

        generated += 1

        print(
            f"\nCASE {generated:02d}"
            f" | seed={seed - 1}"
            f" | start={maze.start}"
            f" | goal={maze.goal}"
        )

        for result in case_results:

            print_result(result)

            results.append(result)

    summarize(
        results,
        f"WEIGHTED MAZE SUMMARY - {size} x {size}",
    )

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")
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

    all_results = []

    # ========================================================
    # RANDOM
    # ========================================================

    for size in SIZES:

        results = run_random_benchmark(size)

        all_results.extend(results)

    # ========================================================
    # OPEN
    # ========================================================

    for size in SIZES:

        results = run_open_benchmark(size)

        all_results.extend(results)

    # ========================================================
    # DENSE
    # ========================================================

    for size in SIZES:

        results = run_dense_benchmark(size)

        all_results.extend(results)

    # ========================================================
    # WEIGHTED
    # ========================================================

    for size in SIZES:

        results = run_weighted_benchmark(size)

        all_results.extend(results)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
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

        print()
        print(
            f"{objective_name}"
        )

        print(
            f"  Dijkstra avg time : {d_time:.4f} ms"
        )

        print(
            f"  A* avg time       : {a_time:.4f} ms"
        )

        print(
            f"  Runtime speedup   : {speedup:.2f}x"
        )

        print(
            f"  Dijkstra avg exp  : {d_exp:.2f}"
        )

        print(
            f"  A* avg exp        : {a_exp:.2f}"
        )

        print(
            f"  Expansion reduce  : {reduction:.2f}%"
        )

        print(
            f"  A* faster cases   : {faster}/{len(rows)}"
        )

        print(
            f"  A* slower cases   : {slower}/{len(rows)}"
        )

    print("\n")
    print("#" * 70)
    print("LARGE RUNTIME BENCHMARK FINISHED")
    print("#" * 70)
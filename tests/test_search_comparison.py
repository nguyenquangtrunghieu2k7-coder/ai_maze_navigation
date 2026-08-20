import math
import time
import argparse

import matplotlib.pyplot as plt

from core.maze import Maze

from core.cost import (
    distance_cost,
    time_cost,
    energy_cost,
)

from algorithms.dijkstra import Dijkstra
from algorithms.astar import Astar

from algorithms.heuristic import (
    euclidean_3d,
    time_heuristic,
    energy_heuristic,
)


# ============================================================
# CONFIG
# ============================================================

BENCHMARK_RUNS = 100


# ============================================================
# MAZE
# ============================================================

def build_comparison_maze():
    """
    Maze dùng chung cho Dijkstra và A*.

    Có nhiều nhánh để A* có cơ hội
    prune search bằng heuristic.

    S = Start
    G = Goal

    ###########
    #S        #
    # ### ### #
    #   #     #
    ### # ### #
    #     #   #
    # ### # #G#
    #         #
    ###########
    """

    width = 11
    height = 9

    maze = Maze(width, height)

    walkable = [
        # Row 1
        (1, 1), (2, 1), (3, 1), (4, 1),
        (5, 1), (6, 1), (7, 1), (8, 1),
        (9, 1),

        # Row 2
        (1, 2), (5, 2), (7, 2), (9, 2),

        # Row 3
        (1, 3), (2, 3), (3, 3), (5, 3),
        (6, 3), (7, 3), (8, 3), (9, 3),

        # Row 4
        (3, 4), (5, 4), (9, 4),

        # Row 5
        (1, 5), (2, 5), (3, 5), (4, 5),
        (5, 5), (7, 5), (8, 5), (9, 5),

        # Row 6
        (1, 6), (5, 6), (7, 6), (9, 6),

        # Row 7
        (1, 7), (2, 7), (3, 7), (4, 7),
        (5, 7), (6, 7), (7, 7), (8, 7),
        (9, 7),
    ]

    for x, y in walkable:
        maze.set_walkable(x, y)

    maze.set_start(1, 1)
    maze.set_goal(9, 7)

    return maze


# ============================================================
# HELPERS
# ============================================================

def check_path_valid(maze, path, start, goal):
    """
    Kiểm tra path có thực sự đi được trong maze.
    """

    assert path, "Path is empty"

    assert path[0] == start
    assert path[-1] == goal

    for current, nxt in zip(path, path[1:]):
        neighbors = list(
            maze.neighbors(
                current[0],
                current[1]
            )
        )

        assert nxt in neighbors, (
            f"Invalid step: {current} -> {nxt}"
        )


def calculate_path_cost(maze, path, cost_fn):
    """
    Tự tính lại g(path).
    """

    total = 0.0

    for current, nxt in zip(path, path[1:]):
        x, y = current
        nx, ny = nxt

        total += cost_fn(
            maze,
            x,
            y,
            nx,
            ny
        )

    return total


def run_search(
    maze,
    start,
    goal,
    cost_fn,
    heuristic_fn
):
    """
    Chạy Dijkstra + A* trên cùng một maze.
    """

    dijkstra = Dijkstra()
    astar = Astar()

    d_result = dijkstra.search(
        maze,
        start,
        goal,
        cost_fn
    )

    a_result = astar.search(
        maze,
        start,
        goal,
        cost_fn,
        heuristic_fn
    )

    return d_result, a_result


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
# TEST 1
# COST COMPARISON
# ============================================================

def test_cost_comparison():

    print("\n" + "=" * 60)
    print("TEST 1: PATH COST COMPARISON")
    print("=" * 60)

    start = (1, 1)
    goal = (9, 7)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        maze = build_comparison_maze()

        d_result, a_result = run_search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        print(f"\n{name}")

        print(
            "Dijkstra cost:",
            d_result.path_cost
        )

        print(
            "A* cost:",
            a_result.path_cost
        )

        assert d_result.found
        assert a_result.found

        assert math.isclose(
            d_result.path_cost,
            a_result.path_cost,
            rel_tol=1e-9,
            abs_tol=1e-9
        )

    print("\nPASS")


# ============================================================
# TEST 2
# EXPANDED NODES
# ============================================================

def test_expanded_nodes():

    print("\n" + "=" * 60)
    print("TEST 2: EXPANDED NODES")
    print("=" * 60)

    start = (1, 1)
    goal = (9, 7)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        maze = build_comparison_maze()

        d_result, a_result = run_search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        d_nodes = d_result.expanded_nodes
        a_nodes = a_result.expanded_nodes

        if d_nodes > 0:
            reduction = (
                (d_nodes - a_nodes)
                / d_nodes
                * 100
            )
        else:
            reduction = 0.0

        print(f"\n{name}")

        print(
            f"Dijkstra expanded: {d_nodes}"
        )

        print(
            f"A* expanded:       {a_nodes}"
        )

        print(
            f"Reduction:         {reduction:.2f}%"
        )

        assert d_result.found
        assert a_result.found

        assert d_nodes > 0
        assert a_nodes > 0

        # A* phải giữ optimality
        assert math.isclose(
            d_result.path_cost,
            a_result.path_cost,
            rel_tol=1e-9,
            abs_tol=1e-9
        )

    print("\nPASS")


# ============================================================
# TEST 3
# RUNTIME
# ============================================================

def benchmark_algorithm(
    algorithm,
    maze_builder,
    start,
    goal,
    cost_fn,
    heuristic_fn=None,
    runs=BENCHMARK_RUNS
):
    """
    Chạy algorithm nhiều lần và lấy
    average / min / max runtime.
    """

    times = []

    for _ in range(runs):

        maze = maze_builder()

        start_time = time.perf_counter()

        if heuristic_fn is None:

            algorithm.search(
                maze,
                start,
                goal,
                cost_fn
            )

        else:

            algorithm.search(
                maze,
                start,
                goal,
                cost_fn,
                heuristic_fn
            )

        elapsed = (
            time.perf_counter()
            - start_time
        ) * 1000

        times.append(elapsed)

    return {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
    }


def test_runtime():

    print("\n" + "=" * 60)
    print("TEST 3: RUNTIME BENCHMARK")
    print("=" * 60)

    start = (1, 1)
    goal = (9, 7)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        d_stats = benchmark_algorithm(
            Dijkstra(),
            build_comparison_maze,
            start,
            goal,
            cost_fn,
            runs=BENCHMARK_RUNS
        )

        a_stats = benchmark_algorithm(
            Astar(),
            build_comparison_maze,
            start,
            goal,
            cost_fn,
            heuristic_fn,
            runs=BENCHMARK_RUNS
        )

        print(f"\n{name}")

        print(
            f"Dijkstra:"
            f" avg={d_stats['avg']:.6f} ms"
            f" min={d_stats['min']:.6f} ms"
            f" max={d_stats['max']:.6f} ms"
        )

        print(
            f"A*:"
            f"       avg={a_stats['avg']:.6f} ms"
            f" min={a_stats['min']:.6f} ms"
            f" max={a_stats['max']:.6f} ms"
        )

        if d_stats["avg"] > 0:

            speedup = (
                d_stats["avg"]
                / a_stats["avg"]
            )

            print(
                f"Speedup:"
                f" {speedup:.2f}x"
            )

    print("\nPASS")


# ============================================================
# TEST 4
# PATH VALIDITY
# ============================================================

def test_path_validity():

    print("\n" + "=" * 60)
    print("TEST 4: PATH VALIDITY")
    print("=" * 60)

    start = (1, 1)
    goal = (9, 7)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        maze = build_comparison_maze()

        d_result, a_result = run_search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        check_path_valid(
            maze,
            d_result.path,
            start,
            goal
        )

        check_path_valid(
            maze,
            a_result.path,
            start,
            goal
        )

        d_cost = calculate_path_cost(
            maze,
            d_result.path,
            cost_fn
        )

        a_cost = calculate_path_cost(
            maze,
            a_result.path,
            cost_fn
        )

        assert math.isclose(
            d_result.path_cost,
            d_cost,
            rel_tol=1e-9,
            abs_tol=1e-9
        )

        assert math.isclose(
            a_result.path_cost,
            a_cost,
            rel_tol=1e-9,
            abs_tol=1e-9
        )

        print(
            f"{name:<10} PASS"
        )

    print("\nPASS")


# ============================================================
# VISUALIZATION
# ============================================================

def visualize_result(
    maze,
    d_result,
    a_result,
    start,
    goal,
    title
):
    """
    Visualization đơn giản:

    - Dijkstra visited = .
    - A* visited = +
    - Final path = *
    - Start = S
    - Goal = G
    """

    height = maze.height
    width = maze.width

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 6)
    )

    results = [
        ("Dijkstra", d_result),
        ("A*", a_result),
    ]

    for ax, (name, result) in zip(
        axes,
        results
    ):

        grid = []

        for y in range(height):

            row = []

            for x in range(width):

                cell = maze.get_cell(x, y)

                # Không walkable
                if not cell.walkable:
                    value = 0
                else:
                    value = 1

                row.append(value)

            grid.append(row)

        ax.imshow(
            grid,
            origin="upper"
        )

        # ----------------------------------------------------
        # Visited
        # ----------------------------------------------------

        visited_x = []
        visited_y = []

        for x, y in result.visited_order:

            if (x, y) != start and (x, y) != goal:
                visited_x.append(x)
                visited_y.append(y)

        ax.scatter(
            visited_x,
            visited_y,
            s=20,
            marker="."
        )

        # ----------------------------------------------------
        # Final path
        # ----------------------------------------------------

        path_x = [
            x for x, y in result.path
        ]

        path_y = [
            y for x, y in result.path
        ]

        ax.plot(
            path_x,
            path_y,
            linewidth=2
        )

        # ----------------------------------------------------
        # Start / Goal
        # ----------------------------------------------------

        ax.scatter(
            [start[0]],
            [start[1]],
            s=100,
            marker="o"
        )

        ax.scatter(
            [goal[0]],
            [goal[1]],
            s=100,
            marker="X"
        )

        ax.set_title(
            f"{name}\n"
            f"Expanded: {result.expanded_nodes}"
        )

        ax.set_xlim(-0.5, width - 0.5)
        ax.set_ylim(height - 0.5, -0.5)

        ax.set_xticks(range(width))
        ax.set_yticks(range(height))

        ax.grid(True)

    fig.suptitle(title)

    plt.tight_layout()
    plt.show()


def visualize_comparison():

    print("\n" + "=" * 60)
    print("VISUALIZATION")
    print("=" * 60)

    start = (1, 1)
    goal = (9, 7)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        maze = build_comparison_maze()

        d_result, a_result = run_search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        visualize_result(
            maze,
            d_result,
            a_result,
            start,
            goal,
            f"{name}: Dijkstra vs A*"
        )


# ============================================================
# SUMMARY
# ============================================================

def print_summary():

    print("\n")
    print("#" * 70)
    print("DIJKSTRA vs A* SUMMARY")
    print("#" * 70)

    start = (1, 1)
    goal = (9, 7)

    print()

    print(
        f"{'OBJECTIVE':<12}"
        f"{'D_COST':>12}"
        f"{'A*_COST':>12}"
        f"{'D_EXPAND':>12}"
        f"{'A*_EXPAND':>12}"
        f"{'REDUCTION':>12}"
    )

    print("-" * 72)

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        maze = build_comparison_maze()

        d_result, a_result = run_search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        d_nodes = d_result.expanded_nodes
        a_nodes = a_result.expanded_nodes

        if d_nodes:
            reduction = (
                (d_nodes - a_nodes)
                / d_nodes
                * 100
            )
        else:
            reduction = 0.0

        print(
            f"{name:<12}"
            f"{d_result.path_cost:>12.3f}"
            f"{a_result.path_cost:>12.3f}"
            f"{d_nodes:>12}"
            f"{a_nodes:>12}"
            f"{reduction:>11.2f}%"
        )

    print("#" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Show Dijkstra vs A* visualization"
    )

    args = parser.parse_args()

    print("\n")
    print("#" * 70)
    print("DIJKSTRA vs A* COMPARISON SUITE")
    print("#" * 70)

    test_cost_comparison()
    test_expanded_nodes()
    test_runtime()
    test_path_validity()

    print_summary()

    if args.visualize:
        visualize_comparison()

    print("\n")
    print("#" * 70)
    print("ALL COMPARISON TESTS PASSED")
    print("#" * 70)
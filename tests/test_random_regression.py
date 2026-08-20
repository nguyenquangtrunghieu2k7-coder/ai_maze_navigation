import math
import random
import time

from core.maze import Maze
from core.terrain import Terrain

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

WIDTH = 51
HEIGHT = 51

NUM_MAZES = 30

BASE_SEED = 20260820

# Probability of turning an initially free cell into a wall.
# Keep moderate so maze has many alternative routes.
WALL_PROBABILITY = 0.25

ELEVATION_MIN = 0
ELEVATION_MAX = 10

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
# RANDOM MAZE GENERATION
# ============================================================

def build_random_maze(seed):
    """
    Generate a random connected maze.

    Strategy:
        1. Start with all cells walkable.
        2. Randomly remove walls.
        3. Check connectivity.
        4. If disconnected, retry.

    Fixed seed => reproducible test.
    """

    rng = random.Random(seed)

    while True:

        maze = Maze(WIDTH, HEIGHT)

        # ----------------------------------------------------
        # Initially everything inside border is walkable
        # ----------------------------------------------------

        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):

                if rng.random() > WALL_PROBABILITY:
                    maze.set_walkable(x, y)

        # ----------------------------------------------------
        # Random elevation
        # ----------------------------------------------------

        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):

                cell = maze.get_cell(x, y)

                if cell.walkable:

                    cell.elevation = rng.randint(
                        ELEVATION_MIN,
                        ELEVATION_MAX
                    )

        # ----------------------------------------------------
        # Random terrain
        # ----------------------------------------------------

        terrains = [
            Terrain.ROAD,
            Terrain.GRASS,
            Terrain.SAND,
            Terrain.MUD,
        ]

        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):

                cell = maze.get_cell(x, y)

                if cell.walkable:

                    maze.set_terrain(
                        x,
                        y,
                        rng.choice(terrains)
                    )

        # ----------------------------------------------------
        # Pick start / goal
        # ----------------------------------------------------

        walkable = []

        for y in range(1, HEIGHT - 1):
            for x in range(1, WIDTH - 1):

                if maze.get_cell(x, y).walkable:
                    walkable.append((x, y))

        if len(walkable) < 2:
            continue

        start = rng.choice(walkable)
        goal = rng.choice(walkable)

        if start == goal:
            continue

        maze.set_start(*start)
        maze.set_goal(*goal)

        # ----------------------------------------------------
        # Make sure a path exists
        # ----------------------------------------------------

        if has_path(maze, start, goal):

            return maze, start, goal


# ============================================================
# CONNECTIVITY CHECK
# ============================================================

def has_path(maze, start, goal):
    """
    Simple BFS used ONLY by the generator.

    Không dùng Dijkstra/A* ở đây vì chúng ta không muốn
    generator phụ thuộc vào algorithm đang được test.
    """

    queue = [start]
    visited = {start}

    while queue:

        current = queue.pop(0)

        if current == goal:
            return True

        x, y = current

        for neighbor in maze.neighbors(x, y):

            if neighbor not in visited:

                visited.add(neighbor)
                queue.append(neighbor)

    return False


# ============================================================
# RUN ONE CASE
# ============================================================

def run_case(
    maze,
    start,
    goal,
    cost_fn,
    heuristic_fn,
):
    """
    Run Dijkstra and A* on exactly the same maze.
    """

    dijkstra = Dijkstra()
    astar = Astar()

    # --------------------------------------------------------
    # Dijkstra
    # --------------------------------------------------------

    start_time = time.perf_counter()

    d_result = dijkstra.search(
        maze,
        start,
        goal,
        cost_fn
    )

    d_runtime = (
        time.perf_counter()
        - start_time
    ) * 1000

    # --------------------------------------------------------
    # A*
    # --------------------------------------------------------

    start_time = time.perf_counter()

    a_result = astar.search(
        maze,
        start,
        goal,
        cost_fn,
        heuristic_fn
    )

    a_runtime = (
        time.perf_counter()
        - start_time
    ) * 1000

    return (
        d_result,
        a_result,
        d_runtime,
        a_runtime,
    )


# ============================================================
# PATH VALIDATION
# ============================================================

def check_path_valid(
    maze,
    path,
    start,
    goal
):
    assert path
    assert path[0] == start
    assert path[-1] == goal

    for current, nxt in zip(
        path,
        path[1:]
    ):

        x, y = current

        neighbors = list(
            maze.neighbors(x, y)
        )

        assert nxt in neighbors, (
            f"Invalid path step: "
            f"{current} -> {nxt}"
        )


# ============================================================
# COST VALIDATION
# ============================================================

def calculate_path_cost(
    maze,
    path,
    cost_fn
):

    total = 0.0

    for current, nxt in zip(
        path,
        path[1:]
    ):

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


# ============================================================
# STATISTICS
# ============================================================

def print_objective_summary(
    name,
    stats
):

    print("\n" + "-" * 70)

    print(name)

    print("-" * 70)

    print(
        f"Cases:              {len(stats)}"
    )

    print(
        f"A* better expanded: "
        f"{sum(s['a_expanded'] < s['d_expanded'] for s in stats)}"
    )

    print(
        f"Same expanded:       "
        f"{sum(s['a_expanded'] == s['d_expanded'] for s in stats)}"
    )

    print(
        f"A* worse expanded:   "
        f"{sum(s['a_expanded'] > s['d_expanded'] for s in stats)}"
    )

    avg_d_expanded = (
        sum(s["d_expanded"] for s in stats)
        / len(stats)
    )

    avg_a_expanded = (
        sum(s["a_expanded"] for s in stats)
        / len(stats)
    )

    print(
        f"\nAverage Dijkstra expanded:"
        f" {avg_d_expanded:.2f}"
    )

    print(
        f"Average A* expanded:"
        f"       {avg_a_expanded:.2f}"
    )

    if avg_d_expanded > 0:

        reduction = (
            (avg_d_expanded - avg_a_expanded)
            / avg_d_expanded
            * 100
        )

        print(
            f"Average reduction:"
            f" {reduction:.2f}%"
        )

    avg_d_runtime = (
        sum(s["d_runtime"] for s in stats)
        / len(stats)
    )

    avg_a_runtime = (
        sum(s["a_runtime"] for s in stats)
        / len(stats)
    )

    print(
        f"\nAverage Dijkstra runtime:"
        f" {avg_d_runtime:.4f} ms"
    )

    print(
        f"Average A* runtime:"
        f"       {avg_a_runtime:.4f} ms"
    )

    if avg_a_runtime > 0:

        speedup = (
            avg_d_runtime
            / avg_a_runtime
        )

        print(
            f"Average speedup:"
            f" {speedup:.2f}x"
        )


# ============================================================
# MAIN REGRESSION TEST
# ============================================================

def test_random_regression():

    print("\n")
    print("#" * 70)
    print("RANDOM MAZE REGRESSION")
    print("#" * 70)

    print(
        f"Size: {WIDTH} x {HEIGHT}"
    )

    print(
        f"Mazes: {NUM_MAZES}"
    )

    print(
        f"Base seed: {BASE_SEED}"
    )

    print(
        f"Wall probability:"
        f" {WALL_PROBABILITY}"
    )

    all_stats = {
        "DISTANCE": [],
        "TIME": [],
        "ENERGY": [],
    }

    # ========================================================
    # Generate random mazes
    # ========================================================

    for maze_id in range(NUM_MAZES):

        seed = BASE_SEED + maze_id

        maze, start, goal = build_random_maze(
            seed
        )

        print(
            f"\nMaze {maze_id + 1:02d}"
            f" | seed={seed}"
            f" | start={start}"
            f" | goal={goal}"
        )

        # ====================================================
        # Every objective
        # ====================================================

        for (
            name,
            cost_fn,
            heuristic_fn
        ) in OBJECTIVES:

            (
                d_result,
                a_result,
                d_runtime,
                a_runtime,
            ) = run_case(
                maze,
                start,
                goal,
                cost_fn,
                heuristic_fn
            )

            # ------------------------------------------------
            # Both algorithms must find a path
            # ------------------------------------------------

            assert d_result.found, (
                f"Dijkstra failed\n"
                f"maze={maze_id}\n"
                f"seed={seed}\n"
                f"objective={name}"
            )

            assert a_result.found, (
                f"A* failed while Dijkstra succeeded\n"
                f"maze={maze_id}\n"
                f"seed={seed}\n"
                f"objective={name}\n"
                f"start={start}\n"
                f"goal={goal}"
            )

            # ------------------------------------------------
            # Optimal cost must match
            # ------------------------------------------------

            assert math.isclose(
                d_result.path_cost,
                a_result.path_cost,
                rel_tol=1e-8,
                abs_tol=1e-8
            ), (
                f"OPTIMAL COST MISMATCH\n"
                f"maze={maze_id}\n"
                f"seed={seed}\n"
                f"objective={name}\n"
                f"Dijkstra={d_result.path_cost}\n"
                f"A*={a_result.path_cost}"
            )

            # ------------------------------------------------
            # Path validity
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Recalculate path cost
            # ------------------------------------------------

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
                rel_tol=1e-8,
                abs_tol=1e-8
            )

            assert math.isclose(
                a_result.path_cost,
                a_cost,
                rel_tol=1e-8,
                abs_tol=1e-8
            )

            # ------------------------------------------------
            # Save statistics
            # ------------------------------------------------

            all_stats[name].append({
                "d_expanded":
                    d_result.expanded_nodes,

                "a_expanded":
                    a_result.expanded_nodes,

                "d_runtime":
                    d_runtime,

                "a_runtime":
                    a_runtime,

                "cost":
                    a_result.path_cost,
            })

            # ------------------------------------------------
            # Print case
            # ------------------------------------------------

            if (
                a_result.expanded_nodes
                < d_result.expanded_nodes
            ):
                symbol = "A* BETTER"

            elif (
                a_result.expanded_nodes
                == d_result.expanded_nodes
            ):
                symbol = "SAME"

            else:
                symbol = "A* WORSE"

            print(
                f"  {name:<8}"
                f"D={d_result.expanded_nodes:<4}"
                f"A*={a_result.expanded_nodes:<4}"
                f"{symbol}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("#" * 70)
    print("RANDOM REGRESSION SUMMARY")
    print("#" * 70)

    for name in (
        "DISTANCE",
        "TIME",
        "ENERGY"
    ):

        print_objective_summary(
            name,
            all_stats[name]
        )

    print("\n")
    print("#" * 70)
    print("ALL RANDOM REGRESSION TESTS PASSED")
    print("#" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    test_random_regression()
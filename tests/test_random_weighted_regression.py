import math
import random
from statistics import mean

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

WIDTH = 31
HEIGHT = 31

NUM_CASES = 25

BASE_SEED = 20260820

WALL_PROBABILITY = 0.20

MIN_DISTANCE = 10

ELEVATION_MIN = 0
ELEVATION_MAX = 10

# Số node random dùng để kiểm tra admissibility
ADMISSIBILITY_SAMPLES = 8


# ============================================================
# HELPERS
# ============================================================

def get_walkable_cells(maze):
    cells = []

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if maze.get_cell(x, y).walkable:
                cells.append((x, y))

    return cells


def build_random_maze(seed):
    """
    Tạo random weighted maze.

    Có:
    - random walls
    - random terrain
    - random elevation

    Sau đó chọn start/goal trong cùng connected component.
    """

    rng = random.Random(seed)

    maze = Maze(WIDTH, HEIGHT)

    # --------------------------------------------------------
    # 1. Random walls
    # --------------------------------------------------------

    for y in range(HEIGHT):
        for x in range(WIDTH):

            # Viền ngoài để tránh edge case quá sát boundary
            if (
                x == 0
                or y == 0
                or x == WIDTH - 1
                or y == HEIGHT - 1
            ):
                continue

            if rng.random() > WALL_PROBABILITY:
                maze.set_walkable(x, y)

    # --------------------------------------------------------
    # 2. Terrain + elevation
    # --------------------------------------------------------

    terrains = [
        Terrain.ROAD,
        Terrain.GRASS,
        Terrain.SAND,
        Terrain.MUD,
    ]

    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):

            cell = maze.get_cell(x, y)

            if not cell.walkable:
                continue

            cell.terrain = rng.choice(terrains)

            cell.elevation = rng.randint(
                ELEVATION_MIN,
                ELEVATION_MAX
            )

    # --------------------------------------------------------
    # 3. Find connected components
    # --------------------------------------------------------

    walkable = set(get_walkable_cells(maze))

    if not walkable:
        return None

    start = rng.choice(list(walkable))

    component = set()
    stack = [start]

    while stack:

        current = stack.pop()

        if current in component:
            continue

        component.add(current)

        x, y = current

        for neighbor in maze.neighbors(x, y):

            if neighbor not in component:
                stack.append(neighbor)

    # Cần đủ xa để test meaningful
    candidates = [
        cell
        for cell in component
        if abs(cell[0] - start[0])
        + abs(cell[1] - start[1])
        >= MIN_DISTANCE
    ]

    if not candidates:
        return None

    goal = rng.choice(candidates)

    maze.set_start(*start)
    maze.set_goal(*goal)

    return maze, start, goal


def calculate_path_cost(maze, path, cost_fn):

    total = 0.0

    for i in range(len(path) - 1):

        x, y = path[i]
        nx, ny = path[i + 1]

        total += cost_fn(
            maze,
            x,
            y,
            nx,
            ny
        )

    return total


def check_path_valid(maze, path, start, goal):

    assert path, "Path is empty"

    assert path[0] == start, (
        f"Path does not start at start: "
        f"{path[0]} != {start}"
    )

    assert path[-1] == goal, (
        f"Path does not end at goal: "
        f"{path[-1]} != {goal}"
    )

    for i in range(len(path) - 1):

        current = path[i]
        neighbor = path[i + 1]

        assert neighbor in maze.neighbors(*current), (
            f"Invalid move: "
            f"{current} -> {neighbor}"
        )


def zero_heuristic(maze, current, goal):
    return 0.0


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
# SINGLE CASE
# ============================================================

def run_case(case_id, seed):

    built = build_random_maze(seed)

    if built is None:
        return None

    maze, start, goal = built

    print(
        f"\nCASE {case_id:02d} | "
        f"seed={seed} | "
        f"start={start} | "
        f"goal={goal}"
    )

    dijkstra = Dijkstra()
    astar = Astar()

    results = {}

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        # ----------------------------------------------------
        # Dijkstra
        # ----------------------------------------------------

        d_result = dijkstra.search(
            maze,
            start,
            goal,
            cost_fn
        )

        # ----------------------------------------------------
        # A*
        # ----------------------------------------------------

        a_result = astar.search(
            maze,
            start,
            goal,
            cost_fn,
            heuristic_fn
        )

        # ----------------------------------------------------
        # Both must find path
        # ----------------------------------------------------

        assert d_result.found, (
            f"{name}: Dijkstra failed\n"
            f"seed={seed}"
        )

        assert a_result.found, (
            f"{name}: A* failed\n"
            f"seed={seed}"
        )

        # ----------------------------------------------------
        # Path validity
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Cost consistency
        # ----------------------------------------------------

        d_calculated = calculate_path_cost(
            maze,
            d_result.path,
            cost_fn
        )

        a_calculated = calculate_path_cost(
            maze,
            a_result.path,
            cost_fn
        )

        assert math.isclose(
            d_result.path_cost,
            d_calculated,
            rel_tol=1e-9,
            abs_tol=1e-9
        ), (
            f"{name}: Dijkstra path_cost mismatch\n"
            f"reported={d_result.path_cost}\n"
            f"calculated={d_calculated}"
        )

        assert math.isclose(
            a_result.path_cost,
            a_calculated,
            rel_tol=1e-9,
            abs_tol=1e-9
        ), (
            f"{name}: A* path_cost mismatch\n"
            f"reported={a_result.path_cost}\n"
            f"calculated={a_calculated}"
        )

        # ----------------------------------------------------
        # MOST IMPORTANT:
        # A* must return same optimal cost as Dijkstra
        # ----------------------------------------------------

        assert math.isclose(
            d_result.path_cost,
            a_result.path_cost,
            rel_tol=1e-9,
            abs_tol=1e-9
        ), (
            f"\n"
            f"{name}: A* FOUND NON-OPTIMAL PATH!\n"
            f"seed={seed}\n"
            f"start={start}\n"
            f"goal={goal}\n"
            f"Dijkstra={d_result.path_cost}\n"
            f"A*={a_result.path_cost}\n"
            f"Dijkstra path={d_result.path}\n"
            f"A* path={a_result.path}"
        )

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        results[name] = (
            d_result,
            a_result,
        )

        reduction = (
            1.0
            - a_result.expanded_nodes
            / d_result.expanded_nodes
        ) * 100.0

        print(
            f"{name:<8} "
            f"D={d_result.path_cost:.3f} "
            f"A*={a_result.path_cost:.3f} "
            f"D_exp={d_result.expanded_nodes:<5} "
            f"A*_exp={a_result.expanded_nodes:<5} "
            f"reduction={reduction:6.2f}%"
        )

    return maze, start, goal, results


# ============================================================
# HEURISTIC ADMISSIBILITY
# ============================================================

def test_admissibility(
    maze,
    start,
    goal,
    seed,
):
    """
    Kiểm tra:

        h(n) <= true_cost(n -> goal)

    True cost được lấy bằng Dijkstra.

    Đây là test cực quan trọng cho A*.
    """

    rng = random.Random(seed)

    walkable = get_walkable_cells(maze)

    if len(walkable) > ADMISSIBILITY_SAMPLES:

        sampled = rng.sample(
            walkable,
            ADMISSIBILITY_SAMPLES
        )

    else:
        sampled = walkable

    dijkstra = Dijkstra()

    for name, cost_fn, heuristic_fn in OBJECTIVES:

        for node in sampled:

            # node == goal thì h phải = 0
            h = heuristic_fn(
                maze,
                node,
                goal
            )

            assert h >= -1e-9, (
                f"\n"
                f"{name}: negative heuristic!\n"
                f"seed={seed}\n"
                f"node={node}\n"
                f"h={h}"
            )

            # Từ node -> goal
            result = dijkstra.search(
                maze,
                node,
                goal,
                cost_fn
            )

            if not result.found:
                continue

            optimal = result.path_cost

            assert h <= optimal + 1e-9, (
                f"\n"
                f"================================================\n"
                f"HEURISTIC IS NOT ADMISSIBLE\n"
                f"================================================\n"
                f"Objective : {name}\n"
                f"Seed      : {seed}\n"
                f"Node      : {node}\n"
                f"Goal      : {goal}\n"
                f"Heuristic : {h}\n"
                f"Optimal   : {optimal}\n"
                f"Difference: {h - optimal}\n"
                f"================================================"
            )


# ============================================================
# MAIN REGRESSION
# ============================================================

def test_random_weighted_regression():

    print("\n")
    print("#" * 70)
    print("RANDOM WEIGHTED MAZE REGRESSION")
    print("#" * 70)

    print(f"Size: {WIDTH} x {HEIGHT}")
    print(f"Mazes: {NUM_CASES}")
    print(f"Base seed: {BASE_SEED}")
    print(f"Wall probability: {WALL_PROBABILITY}")
    print(
        f"Elevation: "
        f"{ELEVATION_MIN} -> {ELEVATION_MAX}"
    )

    all_results = {
        "DISTANCE": [],
        "TIME": [],
        "ENERGY": [],
    }

    valid_cases = 0
    skipped_cases = 0

    for i in range(NUM_CASES):

        seed = BASE_SEED + i

        result = run_case(
            i + 1,
            seed
        )

        if result is None:

            print(
                f"\nCASE {i + 1:02d} "
                f"SKIPPED - no suitable connected pair"
            )

            skipped_cases += 1
            continue

        maze, start, goal, results = result

        valid_cases += 1

        # ----------------------------------------------------
        # Check heuristic admissibility
        # ----------------------------------------------------

        test_admissibility(
            maze,
            start,
            goal,
            seed
        )

        # ----------------------------------------------------
        # Save statistics
        # ----------------------------------------------------

        for name in OBJECTIVES:

            objective_name = name[0]

            d_result, a_result = results[
                objective_name
            ]

            reduction = (
                1.0
                - a_result.expanded_nodes
                / d_result.expanded_nodes
            ) * 100.0

            all_results[
                objective_name
            ].append(
                {
                    "d_expanded":
                        d_result.expanded_nodes,

                    "a_expanded":
                        a_result.expanded_nodes,

                    "d_runtime":
                        d_result.runtime_ms,

                    "a_runtime":
                        a_result.runtime_ms,

                    "reduction":
                        reduction,
                }
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("#" * 70)
    print("RANDOM WEIGHTED REGRESSION SUMMARY")
    print("#" * 70)

    print(
        f"Valid cases:   {valid_cases}"
    )

    print(
        f"Skipped cases: {skipped_cases}"
    )

    assert valid_cases > 0

    for name, _, _ in OBJECTIVES:

        data = all_results[name]

        if not data:
            continue

        better = sum(
            r["a_expanded"] < r["d_expanded"]
            for r in data
        )

        same = sum(
            r["a_expanded"] == r["d_expanded"]
            for r in data
        )

        worse = sum(
            r["a_expanded"] > r["d_expanded"]
            for r in data
        )

        avg_d_expanded = mean(
            r["d_expanded"]
            for r in data
        )

        avg_a_expanded = mean(
            r["a_expanded"]
            for r in data
        )

        avg_reduction = mean(
            r["reduction"]
            for r in data
        )

        avg_d_runtime = mean(
            r["d_runtime"]
            for r in data
        )

        avg_a_runtime = mean(
            r["a_runtime"]
            for r in data
        )

        speedup = (
            avg_d_runtime
            / avg_a_runtime
        )

        print("\n")
        print("-" * 70)
        print(name)
        print("-" * 70)

        print(
            f"Cases:                 {len(data)}"
        )

        print(
            f"A* fewer expansions:   {better}"
        )

        print(
            f"Same expansions:       {same}"
        )

        print(
            f"A* more expansions:    {worse}"
        )

        print(
            f"Average Dijkstra exp:  "
            f"{avg_d_expanded:.2f}"
        )

        print(
            f"Average A* exp:        "
            f"{avg_a_expanded:.2f}"
        )

        print(
            f"Average reduction:     "
            f"{avg_reduction:.2f}%"
        )

        print(
            f"Average Dijkstra time: "
            f"{avg_d_runtime:.4f} ms"
        )

        print(
            f"Average A* time:       "
            f"{avg_a_runtime:.4f} ms"
        )

        print(
            f"Average speedup:       "
            f"{speedup:.2f}x"
        )

    print("\n")
    print("#" * 70)
    print("ALL RANDOM WEIGHTED REGRESSION TESTS PASSED")
    print("#" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    test_random_weighted_regression()
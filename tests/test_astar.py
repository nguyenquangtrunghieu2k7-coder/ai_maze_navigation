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
# HELPERS
# ============================================================

def check_path_valid(
    maze: Maze,
    path: list[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
):
    assert path, "Path is empty"
    assert path[0] == start
    assert path[-1] == goal

    for i in range(len(path) - 1):
        current = path[i]
        neighbor = path[i + 1]

        assert neighbor in list(
            maze.neighbors(*current)
        ), f"Invalid step: {current} -> {neighbor}"


def calculate_path_cost(
    maze: Maze,
    path: list[tuple[int, int]],
    cost_fn,
) -> float:

    total = 0.0

    for i in range(len(path) - 1):

        x, y = path[i]
        nx, ny = path[i + 1]

        total += cost_fn(
            maze,
            x,
            y,
            nx,
            ny,
        )

    return total


def zero_heuristic(
    maze: Maze,
    current: tuple[int, int],
    goal: tuple[int, int],
) -> float:
    return 0.0


# ============================================================
# MAZE 1
# Basic maze with multiple routes
# ============================================================

def build_basic_maze():

    width = 9
    height = 7

    maze = Maze(width, height)

    walkable = [

        # Top route
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),

        # Left vertical
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),

        # Middle route
        (2, 3),
        (3, 3),
        (4, 3),
        (5, 3),
        (6, 3),
        (7, 3),

        # Right vertical
        (7, 2),
        (7, 4),
        (7, 5),

        # Bottom route
        (1, 5),
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
        (6, 5),
        (7, 5),
    ]

    for cell in walkable:
        maze.set_walkable(*cell)

    maze.set_start(1, 1)
    maze.set_goal(7, 5)

    return maze


# ============================================================
# MAZE 2
# Terrain-aware maze
#
# Upper route  -> SAND
# Lower route  -> ROAD
#
# Distance should prefer shorter route.
# Time should prefer ROAD if the detour is worthwhile.
# ============================================================

def build_terrain_maze():

    width = 11
    height = 7

    maze = Maze(width, height)

    # Upper route
    for x in range(1, 10):
        maze.set_walkable(x, 1)

    maze.set_walkable(1, 2)
    maze.set_walkable(9, 2)

    # Lower route
    for x in range(1, 10):
        maze.set_walkable(x, 5)

    maze.set_walkable(1, 4)
    maze.set_walkable(9, 4)

    maze.set_start(1, 1)
    maze.set_goal(9, 1)

    # Upper route = sand
    for x in range(1, 10):
        maze.set_terrain(
            x,
            1,
            Terrain.SAND,
        )

    # Lower route = road
    for x in range(1, 10):
        maze.set_terrain(
            x,
            5,
            Terrain.ROAD,
        )

    return maze


# ============================================================
# MAZE 3
# Elevation maze
#
# Direct route crosses a hill.
# Alternative route stays flat.
# ============================================================

def build_elevation_maze():

    width = 9
    height = 7

    maze = Maze(width, height)

    # Direct upper route
    for x in range(1, 8):
        maze.set_walkable(x, 1)

    # Lower detour
    for x in range(1, 8):
        maze.set_walkable(x, 5)

    maze.set_walkable(1, 2)
    maze.set_walkable(1, 3)
    maze.set_walkable(1, 4)

    maze.set_walkable(7, 2)
    maze.set_walkable(7, 3)
    maze.set_walkable(7, 4)

    maze.set_start(1, 1)
    maze.set_goal(7, 1)

    # Hill on direct route
    for x in range(2, 7):
        maze.get_cell(x, 1).elevation = 5

    # Flat lower route
    for x in range(1, 8):
        maze.get_cell(x, 5).elevation = 0

    return maze


# ============================================================
# MAZE 4
# Small elevation maze for uphill/downhill
# ============================================================

def build_slope_maze():

    width = 7
    height = 3

    maze = Maze(width, height)

    for x in range(1, 6):
        maze.set_walkable(x, 1)

    maze.set_start(1, 1)
    maze.set_goal(5, 1)

    return maze


# ============================================================
# MAZE 5
# No path
# ============================================================

def build_no_path_maze():

    width = 5
    height = 5

    maze = Maze(width, height)

    maze.set_walkable(1, 1)
    maze.set_walkable(3, 3)

    maze.set_start(1, 1)
    maze.set_goal(3, 3)

    return maze


# ============================================================
# TEST 1
# A* - DISTANCE
# ============================================================

def test_distance():

    print("\n" + "=" * 60)
    print("TEST 1: A* - DISTANCE")
    print("=" * 60)

    maze = build_basic_maze()

    start = (1, 1)
    goal = (7, 5)

    result = Astar().search(
        maze,
        start,
        goal,
        distance_cost,
        euclidean_3d,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Cost:", result.path_cost)
    print("Expanded:", result.expanded_nodes)

    assert result.found

    check_path_valid(
        maze,
        result.path,
        start,
        goal,
    )

    expected = calculate_path_cost(
        maze,
        result.path,
        distance_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 2
# A* - TIME
# ============================================================

def test_time():

    print("\n" + "=" * 60)
    print("TEST 2: A* - TIME")
    print("=" * 60)

    maze = build_terrain_maze()

    start = (1, 1)
    goal = (9, 1)

    result = Astar().search(
        maze,
        start,
        goal,
        time_cost,
        time_heuristic,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Cost:", result.path_cost)
    print("Expanded:", result.expanded_nodes)

    assert result.found

    check_path_valid(
        maze,
        result.path,
        start,
        goal,
    )

    expected = calculate_path_cost(
        maze,
        result.path,
        time_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 3
# A* - ENERGY
# ============================================================

def test_energy():

    print("\n" + "=" * 60)
    print("TEST 3: A* - ENERGY")
    print("=" * 60)

    maze = build_elevation_maze()

    start = (1, 1)
    goal = (7, 1)

    result = Astar().search(
        maze,
        start,
        goal,
        energy_cost,
        energy_heuristic,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Cost:", result.path_cost)
    print("Expanded:", result.expanded_nodes)

    assert result.found

    check_path_valid(
        maze,
        result.path,
        start,
        goal,
    )

    expected = calculate_path_cost(
        maze,
        result.path,
        energy_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 4
# A* vs Dijkstra
#
# Most important correctness test.
# ============================================================

def test_astar_vs_dijkstra():

    print("\n" + "=" * 60)
    print("TEST 4: A* vs DIJKSTRA")
    print("=" * 60)

    cases = [

        (
            "DISTANCE",
            build_basic_maze,
            distance_cost,
            euclidean_3d,
        ),

        (
            "TIME",
            build_terrain_maze,
            time_cost,
            time_heuristic,
        ),

        (
            "ENERGY",
            build_elevation_maze,
            energy_cost,
            energy_heuristic,
        ),
    ]

    for (
        name,
        maze_builder,
        cost_fn,
        heu_fn,
    ) in cases:

        maze = maze_builder()

        start = maze.start
        goal = maze.goal

        dijkstra_result = Dijkstra().search(
            maze,
            start,
            goal,
            cost_fn,
        )

        astar_result = Astar().search(
            maze,
            start,
            goal,
            cost_fn,
            heu_fn,
        )

        print("\n", name)

        print(
            "Dijkstra:",
            dijkstra_result.path_cost,
        )

        print(
            "A*:",
            astar_result.path_cost,
        )

        assert dijkstra_result.found
        assert astar_result.found

        assert math.isclose(
            dijkstra_result.path_cost,
            astar_result.path_cost,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )

    print("\nPASS")


# ============================================================
# TEST 5
# ZERO HEURISTIC
#
# A*(h=0) should behave like Dijkstra.
# ============================================================

def test_zero_heuristic():

    print("\n" + "=" * 60)
    print("TEST 5: A* WITH ZERO HEURISTIC")
    print("=" * 60)

    cases = [
        (
            build_basic_maze,
            distance_cost,
        ),
        (
            build_terrain_maze,
            time_cost,
        ),
        (
            build_elevation_maze,
            energy_cost,
        ),
    ]

    for maze_builder, cost_fn in cases:

        maze = maze_builder()

        start = maze.start
        goal = maze.goal

        d_result = Dijkstra().search(
            maze,
            start,
            goal,
            cost_fn,
        )

        a_result = Astar().search(
            maze,
            start,
            goal,
            cost_fn,
            zero_heuristic,
        )

        print(
            "\nDijkstra:",
            d_result.path_cost,
        )

        print(
            "A*(h=0):",
            a_result.path_cost,
        )

        assert math.isclose(
            d_result.path_cost,
            a_result.path_cost,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )

    print("PASS")


# ============================================================
# TEST 6
# START == GOAL
# ============================================================

def test_start_equals_goal():

    print("\n" + "=" * 60)
    print("TEST 6: START == GOAL")
    print("=" * 60)

    maze = build_basic_maze()

    start = (1, 1)

    result = Astar().search(
        maze,
        start,
        start,
        distance_cost,
        euclidean_3d,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Cost:", result.path_cost)

    assert result.found
    assert result.path == [start]

    assert math.isclose(
        result.path_cost,
        0.0,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 7
# NO PATH
# ============================================================

def test_no_path():

    print("\n" + "=" * 60)
    print("TEST 7: NO PATH")
    print("=" * 60)

    maze = build_no_path_maze()

    start = (1, 1)
    goal = (3, 3)

    result = Astar().search(
        maze,
        start,
        goal,
        distance_cost,
        euclidean_3d,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Cost:", result.path_cost)

    assert not result.found
    assert result.path == []

    print("PASS")


# ============================================================
# TEST 8
# HEURISTIC AT GOAL
# ============================================================

def test_heuristic_at_goal():

    print("\n" + "=" * 60)
    print("TEST 8: HEURISTIC AT GOAL")
    print("=" * 60)

    maze = build_elevation_maze()

    goal = maze.goal

    heuristics = [
        euclidean_3d,
        time_heuristic,
        energy_heuristic,
    ]

    for heu_fn in heuristics:

        value = heu_fn(
            maze,
            goal,
            goal,
        )

        print(
            heu_fn.__name__,
            "=",
            value,
        )

        assert math.isclose(
            value,
            0.0,
            abs_tol=1e-9,
        )

    print("PASS")


# ============================================================
# TEST 9
# HEURISTIC NON-NEGATIVE
# ============================================================

def test_heuristic_non_negative():

    print("\n" + "=" * 60)
    print("TEST 9: HEURISTIC NON-NEGATIVE")
    print("=" * 60)

    maze = build_elevation_maze()

    goal = maze.goal

    heuristics = [
        euclidean_3d,
        time_heuristic,
        energy_heuristic,
    ]

    for x in range(1, 8):

        for y in range(1, 6):

            try:
                maze.get_cell(x, y)
            except Exception:
                continue

            current = (x, y)

            for heu_fn in heuristics:

                value = heu_fn(
                    maze,
                    current,
                    goal,
                )

                assert value >= 0.0, (
                    f"{heu_fn.__name__} "
                    f"negative at {current}: {value}"
                )

    print("PASS")


# ============================================================
# TEST 10
# HEURISTIC ADMISSIBILITY
#
# h(n) <= optimal cost(n -> goal)
#
# This is one of the strongest tests.
# ============================================================

def test_heuristic_admissibility():

    print("\n" + "=" * 60)
    print("TEST 10: HEURISTIC ADMISSIBILITY")
    print("=" * 60)

    cases = [

        (
            "DISTANCE",
            build_basic_maze,
            distance_cost,
            euclidean_3d,
        ),

        (
            "TIME",
            build_terrain_maze,
            time_cost,
            time_heuristic,
        ),

        (
            "ENERGY",
            build_elevation_maze,
            energy_cost,
            energy_heuristic,
        ),
    ]

    for (
        name,
        maze_builder,
        cost_fn,
        heu_fn,
    ) in cases:

        maze = maze_builder()

        goal = maze.goal

        print("\n" + name)

        # Test every walkable cell
        for y in range(maze.height):
            for x in range(maze.width):

                try:
                    cell = maze.get_cell(x, y)
                except Exception:
                    continue

                if not cell.walkable:
                    continue

                current = (x, y)

                if current == goal:
                    continue

                # Optimal remaining cost
                result = Dijkstra().search(
                    maze,
                    current,
                    goal,
                    cost_fn,
                )

                if not result.found:
                    continue

                h = heu_fn(
                    maze,
                    current,
                    goal,
                )

                optimal = result.path_cost

                print(
                    current,
                    "h =",
                    h,
                    "optimal =",
                    optimal,
                )

                assert h <= optimal + 1e-9, (
                    f"{heu_fn.__name__} is NOT admissible "
                    f"at {current}: "
                    f"h={h}, optimal={optimal}"
                )

    print("PASS")


# ============================================================
# TEST 11
# PATH VALIDITY
# ============================================================

def test_path_validity():

    print("\n" + "=" * 60)
    print("TEST 11: PATH VALIDITY")
    print("=" * 60)

    cases = [
        (
            build_basic_maze,
            distance_cost,
            euclidean_3d,
        ),
        (
            build_terrain_maze,
            time_cost,
            time_heuristic,
        ),
        (
            build_elevation_maze,
            energy_cost,
            energy_heuristic,
        ),
    ]

    for maze_builder, cost_fn, heu_fn in cases:

        maze = maze_builder()

        result = Astar().search(
            maze,
            maze.start,
            maze.goal,
            cost_fn,
            heu_fn,
        )

        assert result.found

        check_path_valid(
            maze,
            result.path,
            maze.start,
            maze.goal,
        )

    print("PASS")


# ============================================================
# TEST 12
# PATH COST CONSISTENCY
#
# result.path_cost must equal
# sum(cost_fn(edge)).
# ============================================================

def test_path_cost_consistency():

    print("\n" + "=" * 60)
    print("TEST 12: PATH COST CONSISTENCY")
    print("=" * 60)

    cases = [
        (
            "DISTANCE",
            build_basic_maze,
            distance_cost,
            euclidean_3d,
        ),
        (
            "TIME",
            build_terrain_maze,
            time_cost,
            time_heuristic,
        ),
        (
            "ENERGY",
            build_elevation_maze,
            energy_cost,
            energy_heuristic,
        ),
    ]

    for name, maze_builder, cost_fn, heu_fn in cases:

        maze = maze_builder()

        result = Astar().search(
            maze,
            maze.start,
            maze.goal,
            cost_fn,
            heu_fn,
        )

        calculated = calculate_path_cost(
            maze,
            result.path,
            cost_fn,
        )

        print(
            name,
            "\nreported:",
            result.path_cost,
            "\ncalculated:",
            calculated,
        )

        assert math.isclose(
            result.path_cost,
            calculated,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )

    print("PASS")


# ============================================================
# TEST 13
# A* PATH COST MUST NOT CONTAIN HEURISTIC
#
# This catches the classic bug:
#
# path_cost = f = g + h
#
# instead of:
#
# path_cost = g
# ============================================================

def test_path_cost_is_g_not_f():

    print("\n" + "=" * 60)
    print("TEST 13: PATH COST IS g, NOT f")
    print("=" * 60)

    maze = build_basic_maze()

    start = maze.start
    goal = maze.goal

    result = Astar().search(
        maze,
        start,
        goal,
        distance_cost,
        euclidean_3d,
    )

    real_cost = calculate_path_cost(
        maze,
        result.path,
        distance_cost,
    )

    h_goal = euclidean_3d(
        maze,
        goal,
        goal,
    )

    assert math.isclose(
        h_goal,
        0.0,
        abs_tol=1e-9,
    )

    assert math.isclose(
        result.path_cost,
        real_cost,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("Real g:", real_cost)
    print("Reported:", result.path_cost)

    print("PASS")


# ============================================================
# TEST 14
# ENERGY - UPHILL
# ============================================================

def test_energy_uphill():

    print("\n" + "=" * 60)
    print("TEST 14: ENERGY - UPHILL")
    print("=" * 60)

    maze = build_slope_maze()

    for x in range(1, 6):
        maze.get_cell(x, 1).elevation = x - 1

    start = (1, 1)
    goal = (5, 1)

    result = Astar().search(
        maze,
        start,
        goal,
        energy_cost,
        energy_heuristic,
    )

    print("Path:", result.path)
    print("Energy:", result.path_cost)

    assert result.found

    check_path_valid(
        maze,
        result.path,
        start,
        goal,
    )

    expected = calculate_path_cost(
        maze,
        result.path,
        energy_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 15
# ENERGY - DOWNHILL
# ============================================================

def test_energy_downhill():

    print("\n" + "=" * 60)
    print("TEST 15: ENERGY - DOWNHILL")
    print("=" * 60)

    maze = build_slope_maze()

    for x in range(1, 6):
        maze.get_cell(x, 1).elevation = 5 - x

    start = (1, 1)
    goal = (5, 1)

    result = Astar().search(
        maze,
        start,
        goal,
        energy_cost,
        energy_heuristic,
    )

    print("Path:", result.path)
    print("Energy:", result.path_cost)

    assert result.found

    expected = calculate_path_cost(
        maze,
        result.path,
        energy_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 16
# ENERGY - BREAKING ANGLE
#
# The heuristic/search must not crash or
# produce negative energy on sufficiently steep downhill.
# ============================================================

def test_breaking_angle():

    print("\n" + "=" * 60)
    print("TEST 16: ENERGY - BREAKING ANGLE")
    print("=" * 60)

    maze = build_slope_maze()

    maze.get_cell(1, 1).elevation = 10
    maze.get_cell(2, 1).elevation = 0
    maze.get_cell(3, 1).elevation = 0
    maze.get_cell(4, 1).elevation = 0
    maze.get_cell(5, 1).elevation = 0

    start = (1, 1)
    goal = (5, 1)

    result = Astar().search(
        maze,
        start,
        goal,
        energy_cost,
        energy_heuristic,
    )

    print("Found:", result.found)
    print("Path:", result.path)
    print("Energy:", result.path_cost)

    assert result.found

    assert result.path_cost >= 0.0

    expected = calculate_path_cost(
        maze,
        result.path,
        energy_cost,
    )

    assert math.isclose(
        result.path_cost,
        expected,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print("PASS")


# ============================================================
# TEST 17
# OBJECTIVE RESULTS
#
# Make sure all three objectives are actually
# evaluated independently.
# ============================================================

def test_three_objectives():

    print("\n" + "=" * 60)
    print("TEST 17: THREE OBJECTIVES")
    print("=" * 60)

    cases = [
        (
            "DISTANCE",
            build_basic_maze,
            distance_cost,
            euclidean_3d,
        ),
        (
            "TIME",
            build_terrain_maze,
            time_cost,
            time_heuristic,
        ),
        (
            "ENERGY",
            build_elevation_maze,
            energy_cost,
            energy_heuristic,
        ),
    ]

    for name, maze_builder, cost_fn, heu_fn in cases:

        maze = maze_builder()

        result = Astar().search(
            maze,
            maze.start,
            maze.goal,
            cost_fn,
            heu_fn,
        )

        print(
            name,
            "\nPath:",
            result.path,
            "\nCost:",
            result.path_cost,
        )

        assert result.found
        assert result.path

    print("PASS")


# ============================================================
# RUN ALL
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("#" * 60)
    print("A* FULL TEST SUITE")
    print("#" * 60)

    test_distance()
    test_time()
    test_energy()

    test_astar_vs_dijkstra()

    test_zero_heuristic()

    test_start_equals_goal()
    test_no_path()

    test_heuristic_at_goal()
    test_heuristic_non_negative()
    test_heuristic_admissibility()

    test_path_validity()
    test_path_cost_consistency()
    test_path_cost_is_g_not_f()

    test_energy_uphill()
    test_energy_downhill()
    test_breaking_angle()

    test_three_objectives()

    print("\n")
    print("#" * 60)
    print("ALL A* TESTS PASSED")
    print("#" * 60)
import math

from core.maze import Maze
from core.terrain import Terrain
from core.cost import (
    distance_cost,
    time_cost,
    energy_cost
)

from algorithms.dijkstra import Dijkstra


WIDTH = 15
HEIGHT = 15

START = (1, 7)
GOAL = (13, 7)


# ======================================================
# CREATE CONTROLLED MAZE
# ======================================================

def create_test_maze():
    maze = Maze(WIDTH, HEIGHT)
    maze.reset()

    # --------------------------------------------------
    # Route A
    #
    # SHORTEST
    # MUD
    #
    # S ───────────────┐
    #                   │
    #                   G
    # --------------------------------------------------

    route_a = [
        (1, 7),
        (2, 7),
        (3, 7),
        (4, 7),
        (5, 7),
        (6, 7),
        (7, 7),
        (8, 7),
        (9, 7),
        (10, 7),
        (11, 7),
        (12, 7),
        (13, 7),
    ]

    # --------------------------------------------------
    # Route B
    #
    # MEDIUM
    # SAND
    # --------------------------------------------------

    route_b = [
        (1, 7),
        (1, 6),
        (1, 5),
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
        (6, 5),
        (7, 5),
        (8, 5),
        (9, 5),
        (10, 5),
        (11, 5),
        (12, 5),
        (13, 5),
        (13, 6),
        (13, 7),
    ]

    # --------------------------------------------------
    # Route C
    #
    # LONGEST
    # ROAD
    # --------------------------------------------------

    route_c = [
        (1, 7),
        (1, 8),
        (1, 9),
        (1, 10),
        (1, 11),
        (2, 11),
        (3, 11),
        (4, 11),
        (5, 11),
        (6, 11),
        (7, 11),
        (8, 11),
        (9, 11),
        (10, 11),
        (11, 11),
        (12, 11),
        (13, 11),
        (13, 10),
        (13, 9),
        (13, 8),
        (13, 7),
    ]

    # --------------------------------------------------
    # Make all route cells walkable
    # --------------------------------------------------

    for route in [route_a, route_b, route_c]:
        for x, y in route:
            maze.set_walkable(x, y, True)

    # --------------------------------------------------
    # Default terrain
    # --------------------------------------------------

    for route in [route_a, route_b, route_c]:
        for x, y in route:
            maze.get_cell(x, y).terrain = Terrain.GRASS

    # Route A → MUD
    for x, y in route_a[1:-1]:
        maze.get_cell(x, y).terrain = Terrain.MUD

    # Route B → SAND
    for x, y in route_b[1:-1]:
        maze.get_cell(x, y).terrain = Terrain.SAND

    # Route C → ROAD
    for x, y in route_c[1:-1]:
        maze.get_cell(x, y).terrain = Terrain.ROAD

    maze.set_start(*START)
    maze.set_goal(*GOAL)

    return maze


# ======================================================
# HELPER
# ======================================================

def print_result(name, result):

    print()
    print("=" * 50)
    print(name)
    print("=" * 50)

    print("Found:", result.found)
    print("Path:", result.path)
    print("Path length:", result.path_length)
    print("Path cost:", result.path_cost)
    print("Expanded nodes:", result.expanded_nodes)
    print("Runtime:", result.runtime_ms, "ms")


# ======================================================
# TEST 1
# DISTANCE
# ======================================================

def test_distance():

    maze = create_test_maze()

    result = Dijkstra().search(
        maze,
        START,
        GOAL,
        distance_cost
    )

    print_result(
        "TEST 1: DIJKSTRA - DISTANCE",
        result
    )

    assert result.found
    assert result.path[0] == START
    assert result.path[-1] == GOAL

    # Route A is the shortest route.
    assert result.path_length == 12

    # Every edge is 1 unit on flat terrain.
    assert math.isclose(
        result.path_cost,
        12.0
    )


# ======================================================
# TEST 2
# TIME
# ======================================================

def test_time():

    maze = create_test_maze()

    result = Dijkstra().search(
        maze,
        START,
        GOAL,
        time_cost
    )

    print_result(
        "TEST 2: DIJKSTRA - TIME",
        result
    )

    assert result.found
    assert result.path[0] == START
    assert result.path[-1] == GOAL

    # Road should be faster despite being longer.
    assert result.path[1:3] == [
        (1, 8),
        (1, 9)
    ]

    assert result.path_cost > 0


# ======================================================
# TEST 3
# ENERGY
# ======================================================

def test_energy():

    maze = create_test_maze()

    result = Dijkstra().search(
        maze,
        START,
        GOAL,
        energy_cost
    )

    print_result(
        "TEST 3: DIJKSTRA - ENERGY",
        result
    )

    assert result.found
    assert result.path[0] == START
    assert result.path[-1] == GOAL

    # Energy-efficient route should avoid Mud.
    assert Terrain.MUD not in [
        maze.get_cell(x, y).terrain
        for x, y in result.path
    ]

    assert result.path_cost > 0


# ======================================================
# TEST 4
# OBJECTIVE COMPARISON
# ======================================================

def test_compare_objectives():

    maze = create_test_maze()

    dijkstra = Dijkstra()

    distance_result = dijkstra.search(
        maze,
        START,
        GOAL,
        distance_cost
    )

    time_result = dijkstra.search(
        maze,
        START,
        GOAL,
        time_cost
    )

    energy_result = dijkstra.search(
        maze,
        START,
        GOAL,
        energy_cost
    )

    print()
    print("=" * 50)
    print("TEST 4: OBJECTIVE COMPARISON")
    print("=" * 50)

    print()
    print("DISTANCE")
    print("Path:", distance_result.path)
    print("Cost:", distance_result.path_cost)

    print()
    print("TIME")
    print("Path:", time_result.path)
    print("Cost:", time_result.path_cost)

    print()
    print("ENERGY")
    print("Path:", energy_result.path)
    print("Cost:", energy_result.path_cost)

    # All objectives must find a path.
    assert distance_result.found
    assert time_result.found
    assert energy_result.found

    # Shortest route must be Route A.
    assert distance_result.path_length == 12

    # Time and energy should avoid the Mud route.
    assert Terrain.MUD not in [
        maze.get_cell(x, y).terrain
        for x, y in time_result.path
    ]

    assert Terrain.MUD not in [
        maze.get_cell(x, y).terrain
        for x, y in energy_result.path
    ]

    # The objectives should produce different costs.
    assert distance_result.path_cost != time_result.path_cost
    assert distance_result.path_cost != energy_result.path_cost


# ======================================================
# TEST 5
# NO PATH
# ======================================================

def test_no_path():

    maze = Maze(5, 5)
    maze.reset()

    maze.set_walkable(1, 1, True)
    maze.set_walkable(2, 1, True)

    start = (1, 1)
    goal = (3, 3)

    result = Dijkstra().search(
        maze,
        start,
        goal,
        distance_cost
    )

    print()
    print("=" * 50)
    print("TEST 5: NO PATH")
    print("=" * 50)

    print("Found:", result.found)
    print("Path:", result.path)
    print("Path length:", result.path_length)
    print("Path cost:", result.path_cost)
    print("Expanded nodes:", result.expanded_nodes)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0
    assert result.path_cost == 0.0


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":

    test_distance()
    test_time()
    test_energy()
    test_compare_objectives()
    test_no_path()

    print()
    print("=" * 50)
    print("ALL DIJKSTRA TESTS PASSED")
    print("=" * 50)
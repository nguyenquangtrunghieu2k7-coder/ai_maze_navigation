import math

from core.maze import Maze
from core.terrain import Terrain
from core.cost import (
    distance_cost,
    time_cost,
    energy_cost,
)


def setup_maze():
    maze = Maze(7, 7)

    # Cho toàn bộ grid walkable
    for y in range(7):
        for x in range(7):
            maze.set_walkable(x, y, True)

    return maze


def print_result(name, value):
    print(f"{name}: {value:.6f}")


# ============================================================
# TEST 1: DISTANCE COST
# ============================================================

def test_distance_cost():
    print("\n" + "=" * 50)
    print("TEST 1: DISTANCE COST")
    print("=" * 50)

    maze = setup_maze()

    maze.get_cell(1, 1).elevation = 0.0
    maze.get_cell(2, 1).elevation = 0.0

    cost = distance_cost(
        maze,
        1, 1,
        2, 1
    )

    print_result("Distance cost", cost)

    assert math.isclose(cost, 1.0)


# ============================================================
# TEST 2: TIME COST
# ============================================================

def test_time_cost():
    print("\n" + "=" * 50)
    print("TEST 2: TIME COST")
    print("=" * 50)

    maze = setup_maze()

    # Cùng khoảng cách, cùng elevation
    maze.get_cell(1, 1).elevation = 0.0
    maze.get_cell(2, 1).elevation = 0.0

    terrains = [
        Terrain.ROAD,
        Terrain.GRASS,
        Terrain.SAND,
        Terrain.MUD,
    ]

    results = {}

    for terrain in terrains:
        maze.get_cell(2, 1).terrain = terrain

        cost = time_cost(
            maze,
            1, 1,
            2, 1
        )

        results[terrain] = cost

        print_result(
            f"{terrain.name} time",
            cost
        )

    # Terrain khó hơn phải mất nhiều thời gian hơn
    assert results[Terrain.ROAD] < results[Terrain.GRASS]
    assert results[Terrain.GRASS] < results[Terrain.SAND]
    assert results[Terrain.SAND] < results[Terrain.MUD]


# ============================================================
# TEST 3: ENERGY - FLAT TERRAIN
# ============================================================

def test_energy_flat():
    print("\n" + "=" * 50)
    print("TEST 3: ENERGY - FLAT TERRAIN")
    print("=" * 50)

    maze = setup_maze()

    maze.get_cell(1, 1).elevation = 0.0
    maze.get_cell(2, 1).elevation = 0.0

    terrains = [
        Terrain.ROAD,
        Terrain.GRASS,
        Terrain.SAND,
        Terrain.MUD,
    ]

    results = {}

    for terrain in terrains:
        maze.get_cell(2, 1).terrain = terrain

        cost = energy_cost(
            maze,
            1, 1,
            2, 1
        )

        results[terrain] = cost

        print_result(
            f"{terrain.name} energy",
            cost
        )

    # Ma sát càng lớn → energy càng lớn
    assert results[Terrain.ROAD] < results[Terrain.GRASS]
    assert results[Terrain.GRASS] < results[Terrain.SAND]
    assert results[Terrain.SAND] < results[Terrain.MUD]


# ============================================================
# TEST 4: ENERGY - SLOPE
# ============================================================

def test_energy_slope():
    print("\n" + "=" * 50)
    print("TEST 4: ENERGY - SLOPE")
    print("=" * 50)

    maze = setup_maze()

    maze.get_cell(1, 1).terrain = Terrain.ROAD
    maze.get_cell(2, 1).terrain = Terrain.ROAD

    # --------------------------------------------------------
    # Flat
    # --------------------------------------------------------

    maze.get_cell(1, 1).elevation = 0.0
    maze.get_cell(2, 1).elevation = 0.0

    flat_energy = energy_cost(
        maze,
        1, 1,
        2, 1
    )

    # --------------------------------------------------------
    # Uphill
    # --------------------------------------------------------

    maze.get_cell(1, 1).elevation = 0.0
    maze.get_cell(2, 1).elevation = 1.0

    uphill_energy = energy_cost(
        maze,
        1, 1,
        2, 1
    )

    # --------------------------------------------------------
    # Downhill
    # --------------------------------------------------------

    maze.get_cell(1, 1).elevation = 1.0
    maze.get_cell(2, 1).elevation = 0.0

    downhill_energy = energy_cost(
        maze,
        1, 1,
        2, 1
    )

    print_result("Flat energy", flat_energy)
    print_result("Uphill energy", uphill_energy)
    print_result("Downhill energy", downhill_energy)

    # Uphill phải tốn nhiều hơn flat
    assert uphill_energy > flat_energy

    # Downhill không được tốn nhiều hơn uphill
    assert downhill_energy < uphill_energy


# ============================================================
# TEST 5: BREAKING ANGLE
# ============================================================

def test_breaking_angle():
    print("\n" + "=" * 50)
    print("TEST 5: BREAKING ANGLE")
    print("=" * 50)

    maze = setup_maze()

    maze.get_cell(1, 1).terrain = Terrain.ROAD
    maze.get_cell(2, 1).terrain = Terrain.ROAD

    maze.get_cell(1, 1).elevation = 10.0
    maze.get_cell(2, 1).elevation = 0.0

    energy = energy_cost(
        maze,
        1, 1,
        2, 1
    )

    distance = math.sqrt(1 ** 2 + 10 ** 2)
    speed = 1.0
    expected_static_energy = 50 * (distance / speed)

    print_result("Total energy", energy)
    print_result("Expected static energy", expected_static_energy)

    # Khi vượt breaking angle:
    # motion_energy = 0
    # tổng energy chỉ còn static energy

    assert math.isclose(
        energy,
        expected_static_energy,
        rel_tol=1e-6
    )


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":
    test_distance_cost()
    test_time_cost()
    test_energy_flat()
    test_energy_slope()
    test_breaking_angle()

    print("\n" + "=" * 50)
    print("ALL COST TESTS PASSED")
    print("=" * 50)
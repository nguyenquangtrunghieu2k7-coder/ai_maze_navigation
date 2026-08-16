from core.maze import Maze
from algorithms.bfs import BFS


def print_result(name, result):
    print(f"\n{'=' * 50}")
    print(name)
    print(f"{'=' * 50}")

    print("Found:", result.found)
    print("Path:", result.path)
    print("Path length:", result.path_length)
    print("Expanded nodes:", result.expanded_nodes)
    print("Runtime:", result.runtime_ms, "ms")
    print("Visited order:", result.visited_order)


def test_simple_path():
    maze = Maze(7, 7)

    # Tạo một đường đi duy nhất
    for x in range(1, 6):
        maze.set_walkable(x, 1)

    for y in range(1, 6):
        maze.set_walkable(5, y)

    maze.set_start(1, 1)
    maze.set_goal(5, 5)

    bfs = BFS()

    result = bfs.search(
        maze,
        maze.start,
        maze.goal
    )

    print_result("TEST 1: SIMPLE PATH", result)


def test_branching_maze():
    maze = Maze(7, 7)

    walkable = [
        (1, 1), (2, 1), (3, 1),
        (1, 2), (3, 2),
        (1, 3), (2, 3), (3, 3),
        (3, 4),
        (3, 5), (4, 5), (5, 5),
    ]

    for x, y in walkable:
        maze.set_walkable(x, y)

    maze.set_start(1, 1)
    maze.set_goal(5, 5)

    bfs = BFS()

    result = bfs.search(
        maze,
        maze.start,
        maze.goal
    )

    print_result("TEST 2: BRANCHING MAZE", result)


def test_no_path():
    maze = Maze(7, 7)

    # Start region
    maze.set_walkable(1, 1)
    maze.set_walkable(2, 1)

    # Goal region bị tách biệt
    maze.set_walkable(5, 5)

    maze.set_start(1, 1)
    maze.set_goal(5, 5)

    bfs = BFS()

    result = bfs.search(
        maze,
        maze.start,
        maze.goal
    )

    print_result("TEST 3: NO PATH", result)


def main():
    test_simple_path()
    test_branching_maze()
    test_no_path()


if __name__ == "__main__":
    main()
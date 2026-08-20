from core.maze import Maze
from core.terrain import Terrain
from core.cost import distance_cost

from algorithms.dijkstra import Dijkstra


def test_dijkstra():

    maze = Maze(7, 7)

    for y in range(7):
        for x in range(7):
            maze.set_walkable(x, y, True)
            maze.get_cell(x, y).terrain = Terrain.ROAD

    start = (1, 1)
    goal = (5, 5)

    result = Dijkstra().search(
        maze,
        start,
        goal,
        distance_cost
    )

    print("=" * 50)
    print("DIJKSTRA - DISTANCE")
    print("=" * 50)

    print("Found:", result.found)
    print("Path:", result.path)
    print("Path length:", result.path_length)
    print("Path cost:", result.path_cost)
    print("Expanded nodes:", result.expanded_nodes)
    print("Runtime:", result.runtime_ms, "ms")
    print("Visited order:", result.visited_order)


if __name__ == "__main__":
    test_dijkstra()
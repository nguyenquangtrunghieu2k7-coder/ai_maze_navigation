import heapq
from time import perf_counter

from core.path import PathResult
from core.maze import Maze
from .base import SearchAlgorithms


class Astar(SearchAlgorithms):

    def search(
        self,
        maze: Maze,
        start: tuple[int, int],
        goal: tuple[int, int],
        cost_fn,
        heuristic_fn
    ) -> PathResult:

        start_time = perf_counter()

        queue = [
            (heuristic_fn(maze, start, goal), start)
        ]

        distance = {start: 0.0}
        parent = {start: None}

        result = PathResult()

        while queue:

            f_score, current = heapq.heappop(queue)

            g_score = distance[current]

            # Bỏ entry cũ trong priority queue
            if f_score > g_score + heuristic_fn(
                maze,
                current,
                goal
            ):
                continue

            # Node này thực sự được expand
            result.visited_order.append(current)
            result.expanded_nodes += 1

            # Đã tới goal
            if current == goal:
                result.path = self._reconstruct_path(
                    parent,
                    goal
                )

                result.path_cost = g_score
                break

            x, y = current

            for neighbor in maze.neighbors(x, y):

                nx, ny = neighbor

                edge_cost = cost_fn(
                    maze,
                    x, y,
                    nx, ny
                )

                new_cost = g_score + edge_cost

                if (
                    neighbor not in distance
                    or new_cost < distance[neighbor]
                ):

                    distance[neighbor] = new_cost
                    parent[neighbor] = current

                    h = heuristic_fn(
                        maze,
                        neighbor,
                        goal
                    )

                    f = new_cost + h

                    heapq.heappush(
                        queue,
                        (f, neighbor)
                    )

        result.runtime_ms = (
            perf_counter() - start_time
        ) * 1000

        return result

    def _reconstruct_path(
        self,
        parent: dict[
            tuple[int, int],
            tuple[int, int] | None
        ],
        goal: tuple[int, int]
    ) -> list[tuple[int, int]]:

        path = [goal]
        current = goal

        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]

        path.reverse()

        return path
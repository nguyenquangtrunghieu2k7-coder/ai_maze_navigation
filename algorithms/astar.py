import heapq
from time import perf_counter

from core.path import PathResult
from core.maze import Maze
from .base import SearchAlgorithms
from .heuristic import manhattan

class Astar(SearchAlgorithms):
    def search(self, maze: Maze, start: tuple[int,int], goal: tuple[int,int], cost_fn) -> PathResult:
        
        start_time = perf_counter()

        queue = [(0.0, start)]
        distance = {start: 0.0} #g_score
        parent = {start: None}

        result = PathResult()

        while queue:
            f_score, current = heapq.heappop(queue)

            g_score = distance[current]

            if f_score > g_score + manhattan(current, goal):
                continue
            
            x,y = current
            for neighbor in maze.neighbors(x,y):
                nx,ny = neighbor

                edge_cost = cost_fn(maze, x,y,nx,ny)
                new_cost = g_score + edge_cost #distance moi cho neighbor dang xet
                if (neighbor not in distance) or (new_cost < distance[neighbor]): #neu chua xet neighbor do, hoac distance moi < distance cu => cap nhat
                    distance[neighbor] = new_cost
                    parent[neighbor] = current

                    h = manhattan(neighbor, goal)
                    f = new_cost + h

                    heapq.heappush(queue, (f, neighbor))

    def _reconstruct_path(self, parent: dict[tuple[int,int], tuple[int, int] | None], goal: tuple[int,int]) -> list[tuple[int,int]]:
        path = [goal]
        current = goal

        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]
        path.reverse()
        return path
        
    
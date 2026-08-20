import heapq
from time import perf_counter

from core.path import PathResult
from core.maze import Maze
from .base import SearchAlgorithms

class Dijkstra(SearchAlgorithms):
    def search(self, maze: Maze, start: tuple[int,int], goal: tuple[int,int], cost_fn) -> PathResult:
        
        start_time = perf_counter()

        queue = [(0.0, start)]
        distance = {start: 0.0}
        parent = {start: None}

        result = PathResult()

        while queue:
            current_cost, current = heapq.heappop(queue)

            # Bỏ entry cũ trong priority queue
            if current_cost > distance[current]:
                continue

            result.visited_order.append(current)
            result.expanded_nodes+=1

            if current == goal:
                result.path = self._reconstruct_path(parent, goal)
                result.path_cost = current_cost
                break
            
            x,y = current
            for neighbor in maze.neighbors(x,y):
                nx,ny = neighbor
                edge_cost = cost_fn(maze, x,y,nx,ny)
                new_cost = edge_cost + current_cost

                if (neighbor not in distance) or (new_cost < distance[neighbor]):
                    distance[neighbor] = new_cost
                    parent[neighbor] = current
                    
                    heapq.heappush(queue, (new_cost, neighbor))

        result.runtime_ms = (perf_counter() - start_time)*1000

        return result
    def _reconstruct_path(self, parent: dict[tuple[int,int], tuple[int, int] | None], goal: tuple[int,int]) -> list[tuple[int,int]]:
        path = [goal]
        current = goal

        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]
        path.reverse()
        return path
        
    
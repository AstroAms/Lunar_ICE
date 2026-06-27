import numpy as np
import heapq

def astar_path(start, goal, hazard_map, slope_map):
    """
    A* pathfinding algorithm for rover navigation.
    Avoids high hazard and steep slope areas.
    """
    rows, cols = hazard_map.shape
    
    def heuristic(a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
    
    def cost(pos):
        r, c = pos
        if 0 <= r < rows and 0 <= c < cols:
            h = float(hazard_map[r, c])
            s = float(slope_map[r, c]) / 30.0
            return 1 + h * 5 + s * 3
        return 999
    
    open_heap = []
    heapq.heappush(open_heap, (0, start))
    came_from = {start: None}
    g_score = {start: 0}
    
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    
    iterations = 0
    max_iterations = 50000
    
    while open_heap and iterations < max_iterations:
        iterations += 1
        current_f, current = heapq.heappop(open_heap)
        
        if current == goal:
            # Reconstruct path
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path
        
        for dr, dc in directions:
            neighbor = (current[0]+dr, current[1]+dc)
            nr, nc = neighbor
            
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if hazard_map[nr, nc] > 0.85:
                continue
            
            tentative_g = g_score[current] + cost(neighbor)
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f, neighbor))
                came_from[neighbor] = current
    
    # If no path found, return straight line
    return simple_path(start, goal)

def simple_path(start, goal):
    """Fallback: simple straight-line path."""
    path = []
    r0, c0 = start
    r1, c1 = goal
    steps = max(abs(r1-r0), abs(c1-c0))
    if steps == 0:
        return [start]
    for i in range(steps+1):
        r = int(r0 + (r1-r0)*i/steps)
        c = int(c0 + (c1-c0)*i/steps)
        path.append((r, c))
    return path

def calculate_path_metrics(path, slope_map, pixel_size_m=30):
    """Calculate distance and difficulty metrics for the rover path."""
    if len(path) < 2:
        return {'distance_m': 0, 'distance_km': 0, 'avg_slope': 0, 'waypoints': 0}
    
    distance_pixels = 0
    slopes = []
    
    for i in range(1, len(path)):
        dr = path[i][0] - path[i-1][0]
        dc = path[i][1] - path[i-1][1]
        distance_pixels += np.sqrt(dr**2 + dc**2)
        r, c = path[i]
        if 0 <= r < slope_map.shape[0] and 0 <= c < slope_map.shape[1]:
            slopes.append(float(slope_map[r, c]))
    
    distance_m = distance_pixels * pixel_size_m
    
    return {
        'distance_m': float(distance_m),
        'distance_km': float(distance_m / 1000),
        'avg_slope': float(np.mean(slopes)) if slopes else 0,
        'waypoints': len(path)
    }
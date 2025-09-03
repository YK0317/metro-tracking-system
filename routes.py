"""
Routes Module for Real-Time KL Metro Tracking System
Handles HTTP API endpoints for stations, fares, and routing
"""

from flask import jsonify, request
try:
    from database_enhanced import get_all_stations, get_enhanced_fare, get_db_connection, log_system_event
    enhanced_db = True
except ImportError:
    from database import get_all_stations, get_fare, get_db_connection
    enhanced_db = False
    
from collections import deque, defaultdict
import heapq
import time

def init_routes(app):
    """Initialize all HTTP API routes"""
    
    @app.route('/api/stations')
    def api_get_stations():
        """Get all stations - FR3.1"""
        try:
            stations = get_all_stations()
            return jsonify(stations)
        except Exception as e:
            return jsonify({'error': f'Failed to retrieve stations: {str(e)}'}), 500
    
    @app.route('/api/fare')
    def api_get_fare():
        """Get fare between two stations - FR3.2 (Enhanced)"""
        from_id = request.args.get('from')
        to_id = request.args.get('to')
        is_peak = request.args.get('peak', 'false').lower() == 'true'
        
        # Validate parameters
        if not from_id or not to_id:
            return jsonify({'error': 'Missing required parameters: from and to'}), 400
        
        try:
            from_id = int(from_id)
            to_id = int(to_id)
        except ValueError:
            return jsonify({'error': 'Invalid station IDs. Must be integers.'}), 400
        
        # Same station
        if from_id == to_id:
            return jsonify({'fare': 0.0, 'distance_km': 0, 'travel_time_min': 0})
        
        try:
            if enhanced_db:
                # Use enhanced fare system with peak hour pricing
                fare_data = get_enhanced_fare(from_id, to_id, 'standard', is_peak)
                if fare_data:
                    return jsonify({
                        'fare': fare_data['fare_amount'],
                        'distance_km': fare_data.get('distance_km', 0),
                        'travel_time_min': fare_data.get('travel_time_min', 0),
                        'fare_type': fare_data.get('fare_type', 'standard'),
                        'is_peak_hour': is_peak
                    })
                else:
                    return jsonify({'error': 'No fare found between stations'}), 404
            else:
                # Use basic fare system
                fare = get_fare(from_id, to_id)
                if fare is not None:
                    return jsonify({'fare': fare})
                else:
                    return jsonify({'error': 'No direct fare found between stations'}), 404
                    
        except Exception as e:
            if enhanced_db:
                log_system_event('ERROR', f'Fare query error: {str(e)}', 3)
            return jsonify({'error': f'Failed to retrieve fare: {str(e)}'}), 500
    
    @app.route('/api/route')
    def api_get_route():
        """Get shortest route between two stations - FR3.3"""
        from_id = request.args.get('from')
        to_id = request.args.get('to')
        
        # Validate parameters
        if not from_id or not to_id:
            return jsonify({'error': 'Missing required parameters: from and to'}), 400
        
        try:
            from_id = int(from_id)
            to_id = int(to_id)
        except ValueError:
            return jsonify({'error': 'Invalid station IDs. Must be integers.'}), 400
        
        # Same station
        if from_id == to_id:
            return jsonify({'path': [from_id], 'total_fare': 0.0, 'total_hops': 0})
        
        try:
            route_result = find_shortest_route(from_id, to_id)
            return jsonify(route_result)
            
        except Exception as e:
            return jsonify({'error': f'Failed to calculate route: {str(e)}'}), 500

def build_graph():
    """Build a graph representation of the metro network from fare data"""
    graph = defaultdict(list)
    
    with get_db_connection() as conn:
        # Get all fare connections
        fares = conn.execute('SELECT origin_id, destination_id, price FROM fares').fetchall()
        
        for fare in fares:
            origin = fare['origin_id']
            destination = fare['destination_id']
            price = fare['price']
            
            # Add edge to graph (bidirectional for metro systems)
            graph[origin].append((destination, price))
            # Ensure bidirectionality by checking reverse connection
            reverse_fare = conn.execute(
                'SELECT price FROM fares WHERE origin_id = ? AND destination_id = ?',
                (destination, origin)
            ).fetchone()
            
            if not reverse_fare:
                # If no explicit reverse fare, assume same price
                graph[destination].append((origin, price))
    
    return graph

def find_shortest_route(origin_id, destination_id):
    """
    Find shortest route using BFS for minimum hops, then calculate total fare
    Returns: {'path': [station_ids], 'total_fare': float, 'total_hops': int}
    """
    graph = build_graph()
    
    # Validate that stations exist in graph
    if origin_id not in graph:
        return {'error': f'Origin station {origin_id} not found in network'}
    
    if destination_id not in graph:
        return {'error': f'Destination station {destination_id} not found in network'}
    
    # BFS for shortest path by hops
    queue = deque([(origin_id, [origin_id])])
    visited = {origin_id}
    
    while queue:
        current_station, path = queue.popleft()
        
        # Check all connected stations
        for next_station, _ in graph[current_station]:
            if next_station == destination_id:
                # Found destination
                final_path = path + [next_station]
                total_fare = calculate_path_fare(final_path)
                
                return {
                    'path': final_path,
                    'total_fare': total_fare,
                    'total_hops': len(final_path) - 1
                }
            
            if next_station not in visited:
                visited.add(next_station)
                queue.append((next_station, path + [next_station]))
    
    # No path found
    return {'error': f'No route found from station {origin_id} to station {destination_id}'}

def calculate_path_fare(path):
    """Calculate total fare for a given path"""
    if len(path) < 2:
        return 0.0
    
    total_fare = 0.0
    
    with get_db_connection() as conn:
        for i in range(len(path) - 1):
            from_station = path[i]
            to_station = path[i + 1]
            
            # Get fare for this segment
            fare_result = conn.execute(
                'SELECT price FROM fares WHERE origin_id = ? AND destination_id = ?',
                (from_station, to_station)
            ).fetchone()
            
            if fare_result:
                total_fare += fare_result['price']
            else:
                # If no direct fare found, this shouldn't happen in a well-formed path
                # but we'll estimate based on average fare
                total_fare += 2.0  # Default fare estimate
    
    return round(total_fare, 2)

def find_shortest_route_dijkstra(origin_id, destination_id):
    """
    Alternative implementation using Dijkstra's algorithm for shortest path by cost
    This can be used instead of BFS if you want cheapest route rather than fewest hops
    """
    graph = build_graph()
    
    # Dijkstra's algorithm
    distances = defaultdict(lambda: float('inf'))
    previous = {}
    distances[origin_id] = 0
    
    # Priority queue: (distance, station_id)
    pq = [(0, origin_id)]
    visited = set()
    
    while pq:
        current_distance, current_station = heapq.heappop(pq)
        
        if current_station in visited:
            continue
            
        visited.add(current_station)
        
        if current_station == destination_id:
            break
        
        # Check all neighbors
        for neighbor, fare in graph[current_station]:
            if neighbor not in visited:
                new_distance = current_distance + fare
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_station
                    heapq.heappush(pq, (new_distance, neighbor))
    
    # Reconstruct path
    if destination_id not in previous and destination_id != origin_id:
        return {'error': f'No route found from station {origin_id} to station {destination_id}'}
    
    path = []
    current = destination_id
    while current is not None:
        path.append(current)
        current = previous.get(current)
    
    path.reverse()
    
    return {
        'path': path,
        'total_fare': round(distances[destination_id], 2),
        'total_hops': len(path) - 1
    }

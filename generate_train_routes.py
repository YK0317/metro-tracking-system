"""
Generate Expected Routes for Current Trains
Shows the predicted path for each active train based on their current position and line sequence
"""

import sqlite3
import json
from train_movement import TrainMovement

def get_current_trains():
    """Get all current active trains from database"""
    try:
        conn = sqlite3.connect('metro_tracking_enhanced.db')
        conn.row_factory = sqlite3.Row
        
        trains = conn.execute("""
            SELECT t.train_id, t.current_station_id, t.line, t.direction, t.status,
                   s.name as current_station_name, s.latitude, s.longitude
            FROM trains t
            JOIN stations s ON t.current_station_id = s.station_id
            WHERE t.status = 'active'
            ORDER BY t.line, t.train_id
        """).fetchall()
        
        conn.close()
        return trains
        
    except Exception as e:
        print(f"Error getting current trains: {e}")
        return []

def generate_train_route(train_movement, train_data, route_length=10):
    """Generate expected route for a single train"""
    train_id = train_data['train_id']
    current_station = train_data['current_station_name']
    line = train_data['line']
    direction = train_data['direction']
    
    # Initialize train in movement system if needed
    if train_id not in train_movement.train_states:
        train_movement.initialize_train(train_id, train_data['current_station_id'], line)
    
    route = [{
        'step': 0,
        'station_name': current_station,
        'station_id': train_data['current_station_id'],
        'latitude': train_data['latitude'],
        'longitude': train_data['longitude'],
        'direction': direction,
        'action': 'Current Position'
    }]
    
    # Simulate next stations
    for step in range(1, route_length + 1):
        next_station = train_movement.get_next_station(train_id)
        
        if next_station:
            current_state = train_movement.train_states[train_id]
            
            route.append({
                'step': step,
                'station_name': next_station['name'],
                'station_id': next_station['station_id'],
                'latitude': next_station['latitude'],
                'longitude': next_station['longitude'],
                'direction': current_state['direction'],
                'action': f"Move {current_state['direction']}"
            })
            
            # Check if direction changed
            if step > 1 and route[step]['direction'] != route[step-1]['direction']:
                route[step]['action'] = f"Direction change to {current_state['direction']}"
        else:
            break
    
    return route

def generate_all_train_routes():
    """Generate expected routes for all active trains"""
    print("🚇 EXPECTED TRAIN ROUTES GENERATOR")
    print("=" * 60)
    
    # Get current trains
    trains = get_current_trains()
    if not trains:
        print("❌ No active trains found in database")
        return
    
    print(f"📊 Found {len(trains)} active trains")
    print()
    
    # Initialize train movement system
    train_movement = TrainMovement()
    
    all_routes = {}
    
    for train in trains:
        train_id = train['train_id']
        print(f"🚂 TRAIN {train_id} ({train['line']} Line)")
        print(f"   Current: {train['current_station_name']} (Station {train['current_station_id']})")
        print(f"   Direction: {train['direction']}")
        print()
        
        # Generate route
        route = generate_train_route(train_movement, train, route_length=15)
        all_routes[train_id] = {
            'train_info': dict(train),
            'expected_route': route
        }
        
        # Display route
        print(f"   📍 Expected Route (Next 15 stations):")
        for step_data in route:
            step = step_data['step']
            station = step_data['station_name']
            direction = step_data['direction']
            action = step_data['action']
            
            if step == 0:
                print(f"   {step:2d}. 📍 {station} ({action})")
            else:
                arrow = "→" if direction == "forward" else "←"
                print(f"   {step:2d}. {arrow} {station} ({action})")
        
        print()
        print("-" * 60)
        print()
    
    # Save routes to JSON file
    save_routes_to_file(all_routes)
    
    # Generate summary statistics
    generate_route_summary(all_routes)
    
    return all_routes

def save_routes_to_file(routes):
    """Save generated routes to JSON file"""
    try:
        # Convert to JSON-serializable format
        json_routes = {}
        for train_id, data in routes.items():
            json_routes[str(train_id)] = {
                'train_info': dict(data['train_info']),
                'expected_route': data['expected_route']
            }
        
        filename = 'expected_train_routes.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_routes, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Routes saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error saving routes: {e}")

def generate_route_summary(routes):
    """Generate summary statistics for all routes"""
    print("📊 ROUTE SUMMARY STATISTICS")
    print("=" * 60)
    
    line_stats = {}
    direction_stats = {'forward': 0, 'backward': 0}
    
    for train_id, data in routes.items():
        train_info = data['train_info']
        route = data['expected_route']
        
        line = train_info['line']
        direction = train_info['direction']
        
        # Count by line
        if line not in line_stats:
            line_stats[line] = {'trains': 0, 'total_stops': 0}
        
        line_stats[line]['trains'] += 1
        line_stats[line]['total_stops'] += len(route)
        
        # Count by direction
        direction_stats[direction] += 1
    
    # Display statistics
    print(f"🚂 Total Active Trains: {len(routes)}")
    print()
    
    print("📈 By Line:")
    for line, stats in line_stats.items():
        avg_route_length = stats['total_stops'] / stats['trains']
        print(f"   {line} Line: {stats['trains']} trains (avg route length: {avg_route_length:.1f} stations)")
    
    print()
    print("🧭 By Direction:")
    for direction, count in direction_stats.items():
        percentage = (count / len(routes)) * 100
        print(f"   {direction.capitalize()}: {count} trains ({percentage:.1f}%)")
    
    print()

def analyze_route_conflicts():
    """Analyze potential route conflicts between trains"""
    print("⚠️  POTENTIAL ROUTE CONFLICTS")
    print("=" * 60)
    
    routes = generate_all_train_routes()
    
    # Check for trains on same line moving in opposite directions
    line_directions = {}
    for train_id, data in routes.items():
        line = data['train_info']['line']
        direction = data['train_info']['direction']
        
        if line not in line_directions:
            line_directions[line] = {'forward': [], 'backward': []}
        
        line_directions[line][direction].append(train_id)
    
    for line, directions in line_directions.items():
        forward_trains = directions['forward']
        backward_trains = directions['backward']
        
        if forward_trains and backward_trains:
            print(f"🔄 {line} Line: Bidirectional traffic detected")
            print(f"   Forward trains: {forward_trains}")
            print(f"   Backward trains: {backward_trains}")
            print(f"   ⚠️  Monitor for potential conflicts at passing points")
            print()

def main():
    """Main function"""
    try:
        # Generate routes for all trains
        routes = generate_all_train_routes()
        
        # Analyze potential conflicts
        analyze_route_conflicts()
        
        print("✅ Route generation completed!")
        print("📁 Check 'expected_train_routes.json' for detailed route data")
        
    except Exception as e:
        print(f"❌ Error generating routes: {e}")

if __name__ == "__main__":
    main()

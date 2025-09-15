"""
Enhanced Route Planner using Route.csv data
Provides accurate route planning with line transfers and detailed step information
"""

import csv
import os
from database import get_db_connection

class EnhancedRoutePlanner:
    """Route planner that uses the detailed Route.csv data for accurate planning"""
    
    def __init__(self):
        self.route_matrix = {}
        self.time_matrix = {}
        self.station_name_to_id = {}
        self.station_id_to_name = {}
        self.load_route_data()
        self.load_station_mappings()
        self.load_time_data()
    
    def load_station_mappings(self):
        """Load station ID to name mappings from database"""
        try:
            with get_db_connection() as conn:
                stations = conn.execute('SELECT station_id, name FROM stations').fetchall()
                
                for station in stations:
                    station_id = station['station_id']
                    station_name = station['name']
                    self.station_name_to_id[station_name] = station_id
                    self.station_id_to_name[station_id] = station_name
                    
                print(f"✅ Loaded {len(stations)} station mappings")
                
        except Exception as e:
            print(f"❌ Error loading station mappings: {e}")
    
    def load_route_data(self):
        """Load route data from Route.csv"""
        route_file = 'data/Route.csv'
        
        if not os.path.exists(route_file):
            print(f"❌ Route.csv not found at {route_file}")
            return
        
        try:
            with open(route_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Get station names from header
                destination_stations = header[1:]  # Skip first empty column
                
                for row in reader:
                    origin_station = row[0]
                    route_data = row[1:]
                    
                    # Store route data for this origin
                    self.route_matrix[origin_station] = {}
                    
                    for i, destination_station in enumerate(destination_stations):
                        route_description = route_data[i] if i < len(route_data) else ""
                        self.route_matrix[origin_station][destination_station] = route_description
            
            print(f"✅ Loaded route matrix for {len(self.route_matrix)} origin stations")
            
        except Exception as e:
            print(f"❌ Error loading Route.csv: {e}")
    
    def parse_route_description(self, route_desc):
        """Parse route description into detailed steps"""
        if not route_desc or route_desc.strip() == "":
            return []
        
        # Handle same station (should be direct)
        if route_desc.startswith("KJL[") and ">" in route_desc and route_desc.count(">") == 1:
            # Simple single-line route like "KJL[Origin > Destination]"
            parts = route_desc.split("[")[1].split("]")[0].split(" > ")
            if len(parts) == 2 and parts[0] == parts[1]:
                return [{
                    'line': route_desc[:3],
                    'from_station': parts[0],
                    'to_station': parts[1],
                    'action': 'Same station',
                    'transfer': False
                }]
        
        steps = []
        
        # Check if it's a transfer route (contains ">>")
        if " >> " in route_desc:
            segments = route_desc.split(" >> ")
            
            for i, segment in enumerate(segments):
                line_info = self.parse_line_segment(segment)
                if line_info:
                    line_info['step'] = i + 1
                    line_info['transfer'] = (i > 0)  # Mark as transfer if not first segment
                    steps.append(line_info)
        else:
            # Single line route
            line_info = self.parse_line_segment(route_desc)
            if line_info:
                line_info['step'] = 1
                line_info['transfer'] = False
                steps.append(line_info)
        
        return steps
    
    def parse_line_segment(self, segment):
        """Parse a single line segment like 'KJL[Origin > Destination]'"""
        try:
            # Extract line (KJL or SBK)
            line = segment[:3]
            
            # Extract stations from brackets
            bracket_content = segment.split("[")[1].split("]")[0]
            stations = bracket_content.split(" > ")
            
            if len(stations) == 2:
                return {
                    'line': line,
                    'from_station': stations[0],
                    'to_station': stations[1],
                    'action': f"Travel on {line} line"
                }
        except:
            pass
        
        return None
    
    def get_route_by_names(self, origin_name, destination_name):
        """Get route using station names"""
        if origin_name not in self.route_matrix:
            return {'error': f'Origin station "{origin_name}" not found in route data'}
        
        if destination_name not in self.route_matrix[origin_name]:
            return {'error': f'No route from "{origin_name}" to "{destination_name}"'}
        
        route_desc = self.route_matrix[origin_name][destination_name]
        
        if not route_desc:
            return {'error': f'No route data available from "{origin_name}" to "{destination_name}"'}
        
        # Parse the route description
        steps = self.parse_route_description(route_desc)
        
        if not steps:
            return {'error': f'Could not parse route: {route_desc}'}
        
        # Build detailed route information
        route_info = {
            'origin': origin_name,
            'destination': destination_name,
            'route_description': route_desc,
            'steps': steps,
            'total_steps': len(steps),
            'has_transfer': any(step.get('transfer', False) for step in steps),
            'lines_used': list(set(step['line'] for step in steps))
        }
        
        # Get intermediate stations for full path
        full_path = self.get_full_station_path(steps)
        route_info['full_path'] = full_path
        route_info['station_count'] = len(full_path)
        
        return route_info
    
    def get_full_station_path(self, steps):
        """Extract full station path from route steps"""
        path = []
        
        for step in steps:
            from_station = step['from_station']
            to_station = step['to_station']
            
            # Add origin if it's the first step or if there's a transfer
            if not path or step.get('transfer', False):
                path.append(from_station)
            
            # Add destination
            path.append(to_station)
        
        return path
    
    def get_route_by_ids(self, origin_id, destination_id):
        """Get route using station IDs (converted to names)"""
        # Convert IDs to names
        origin_name = self.station_id_to_name.get(origin_id)
        destination_name = self.station_id_to_name.get(destination_id)
        
        if not origin_name:
            return {'error': f'Station ID {origin_id} not found'}
        
        if not destination_name:
            return {'error': f'Station ID {destination_id} not found'}
        
        # Get route by names
        route_info = self.get_route_by_names(origin_name, destination_name)
        
        if 'error' in route_info:
            return route_info
        
        # Add station IDs to the result
        route_info['origin_id'] = origin_id
        route_info['destination_id'] = destination_id
        
        # Convert station names in path to IDs
        if 'full_path' in route_info:
            path_ids = []
            for station_name in route_info['full_path']:
                station_id = self.station_name_to_id.get(station_name)
                if station_id:
                    path_ids.append(station_id)
            route_info['path_ids'] = path_ids
        
        # Calculate fare and time
        if 'path_ids' in route_info and len(route_info['path_ids']) > 0:
            route_info['fare'] = self.calculate_route_fare(route_info['path_ids'])
            
            # Calculate travel time
            travel_time_minutes = self.calculate_route_time(origin_name, destination_name)
            route_info['travel_time_minutes'] = travel_time_minutes
            route_info['travel_time_formatted'] = self.format_travel_time(travel_time_minutes)
        
        return route_info
    
    def calculate_route_fare(self, path_ids):
        """Calculate total fare for a route using path IDs"""
        if len(path_ids) < 2:
            return 0.0
        
        total_fare = 0.0
        
        try:
            with get_db_connection() as conn:
                # Use the fare from origin to final destination
                origin_id = path_ids[0]
                destination_id = path_ids[-1]
                
                fare_result = conn.execute(
                    'SELECT price FROM fares WHERE origin_id = ? AND destination_id = ?',
                    (origin_id, destination_id)
                ).fetchone()
                
                if fare_result:
                    total_fare = fare_result['price']
                else:
                    # Fallback: estimate based on distance
                    total_fare = len(path_ids) * 0.5  # 50 cents per station
        
        except Exception as e:
            print(f"Error calculating fare: {e}")
            # Fallback calculation
            total_fare = len(path_ids) * 0.5
        
        return round(total_fare, 2)
    
    def calculate_route_time(self, origin_name, destination_name):
        """Calculate total travel time using Time.csv data"""
        if not hasattr(self, 'time_matrix') or not self.time_matrix:
            self.load_time_data()
        
        # Direct lookup in time matrix
        if (origin_name, destination_name) in self.time_matrix:
            return self.time_matrix[(origin_name, destination_name)]
        
        # Fallback: estimate based on station count
        return 30  # Default 30 minutes
    
    def load_time_data(self):
        """Load travel times from Time.csv file"""
        self.time_matrix = {}
        time_file = 'data/Time.csv'
        
        if not os.path.exists(time_file):
            print(f"⚠️  Time.csv not found at {time_file}")
            return
        
        try:
            with open(time_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Get station names from header
                destination_stations = header[1:]  # Skip first empty column
                
                for row in reader:
                    origin_station = row[0]
                    time_data = row[1:]
                    
                    for i, destination_station in enumerate(destination_stations):
                        if i < len(time_data):
                            try:
                                travel_time = int(time_data[i])
                                self.time_matrix[(origin_station, destination_station)] = travel_time
                            except (ValueError, IndexError):
                                continue
            
            print(f"✅ Loaded travel times for {len(self.time_matrix)} station pairs")
            
        except Exception as e:
            print(f"❌ Error loading Time.csv: {e}")
    
    def format_travel_time(self, minutes):
        """Format travel time into human readable format"""
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {remaining_minutes}min"

def get_enhanced_route(origin_id, destination_id):
    """Main function to get enhanced route using Route.csv data"""
    planner = EnhancedRoutePlanner()
    
    # Same station
    if origin_id == destination_id:
        return {
            'path': [origin_id],
            'path_ids': [origin_id],
            'total_fare': 0.0,
            'total_hops': 0,
            'route_description': 'Same station',
            'steps': [],
            'has_transfer': False,
            'lines_used': []
        }
    
    # Get route information
    route_info = planner.get_route_by_ids(origin_id, destination_id)
    
    if 'error' in route_info:
        return route_info
    
    # Calculate fare
    if 'path_ids' in route_info:
        total_fare = planner.calculate_route_fare(route_info['path_ids'])
        route_info['total_fare'] = total_fare
        route_info['total_hops'] = len(route_info['path_ids']) - 1
        route_info['path'] = route_info['path_ids']  # For compatibility with existing frontend
    
    return route_info

# Test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced Route Planner")
    print("=" * 50)
    
    # Test with some sample routes
    test_routes = [
        (1, 10),   # Gombak to KLCC (same line)
        (10, 53),  # KLCC to Bukit Bintang (transfer required)
        (1, 68),   # Gombak to Kajang (transfer required)
    ]
    
    for origin_id, dest_id in test_routes:
        print(f"\n🚇 Route from Station {origin_id} to Station {dest_id}")
        result = get_enhanced_route(origin_id, dest_id)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Route found:")
            print(f"   Origin: {result.get('origin', 'Unknown')}")
            print(f"   Destination: {result.get('destination', 'Unknown')}")
            print(f"   Transfer required: {'Yes' if result.get('has_transfer', False) else 'No'}")
            print(f"   Lines used: {', '.join(result.get('lines_used', []))}")
            print(f"   Total fare: RM {result.get('total_fare', 0):.2f}")
            print(f"   Total stops: {result.get('total_hops', 0)}")
            
            if 'steps' in result:
                print(f"   Route steps:")
                for i, step in enumerate(result['steps'], 1):
                    transfer_note = " (Transfer)" if step.get('transfer', False) else ""
                    print(f"     {i}. {step['line']} line: {step['from_station']} → {step['to_station']}{transfer_note}")

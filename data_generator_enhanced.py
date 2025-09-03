"""
Enhanced Data Generator with Threading and Multicast Support
Incorporates concepts from practical exercises for better performance and reliability
"""

import time
import random
import threading
import json
import pickle
from queue import Queue
from database_enhanced import get_db_connection, get_all_stations, update_train_position_enhanced
from realtime_enhanced import broadcast_train_update_enhanced, broadcast_system_alert

class EnhancedTrainSimulator:
    """
    Enhanced train simulator with threading support (inspired by Lab2/RPyC threading concepts)
    """
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.stations = []
        self.simulation_running = False
        self.update_queue = Queue()
        self.worker_threads = []
        self.train_states = {}
        self.update_interval = (3, 7)  # Random interval range
        
    def initialize_simulation(self):
        """Initialize simulation with error handling and validation"""
        try:
            print("Initializing Enhanced Train Simulation...")
            
            # Load stations
            self.stations = get_all_stations()
            if not self.stations:
                raise Exception("No stations available for simulation")
            
            # Initialize train states
            self.init_train_states()
            
            # Start worker threads (concept from threading examples)
            self.start_worker_threads()
            
            print(f"Enhanced simulation initialized with {len(self.stations)} stations and {len(self.train_states)} trains")
            return True
            
        except Exception as e:
            print(f"Failed to initialize simulation: {e}")
            return False
    
    def init_train_states(self):
        """Initialize train positions with validation"""
        print("Initializing train states...")
        try:
            with get_db_connection() as conn:
                print("Connected to database for train initialization")
                
                # Clear existing trains
                print("Clearing existing trains...")
                conn.execute('DELETE FROM trains')
                print("Existing trains cleared")
                
                # Add enhanced train fleet
                initial_trains = [
                    (1, 1, 3.1348, 101.6868, 'LRT Kelana Jaya'),
                    (2, 3, 3.1578, 101.7122, 'LRT Kelana Jaya'),
                    (3, 10, 3.1486, 101.7617, 'LRT Ampang'),
                    (4, 15, 3.1258, 101.6858, 'LRT Ampang'),
                    (5, 5, 3.1735, 101.7258, 'LRT Ampang'),
                    (6, 11, 3.1471, 101.7000, 'LRT Kelana Jaya'),
                ]
                
                print("Adding line column if needed...")
                # Enhanced train table with line information - add column safely
                try:
                    # Try to add the column, ignore if it already exists
                    conn.execute('ALTER TABLE trains ADD COLUMN line TEXT DEFAULT "Unknown"')
                    print("Added 'line' column to trains table")
                except Exception as e:
                    # Column probably already exists, which is fine
                    print(f"Column 'line' handling: {e}")
                    pass
                
                print("Inserting train data...")
                for i, train_data in enumerate(initial_trains):
                    print(f"Processing train {i+1}/{len(initial_trains)}")
                    train_id, station_id, lat, lng, line = train_data
                    conn.execute('''
                        INSERT INTO trains (train_id, current_station_id, latitude, longitude, line)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (train_id, station_id, lat, lng, line))
                    
                    # Store in memory for quick access
                    self.train_states[train_id] = {
                        'current_station_id': station_id,
                        'line': line,
                        'last_update': time.time(),
                        'direction': 'forward',
                        'speed_factor': random.uniform(0.8, 1.2)
                    }
                
                print("Committing changes...")
                conn.commit()
                print("Train states initialized successfully")
                
        except Exception as e:
            print(f"Error initializing train states: {e}")
            raise
    
    def column_exists(self, conn, table_name, column_name):
        """Check if column exists in table - simplified version"""
        try:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        except Exception as e:
            print(f"Error checking column existence: {e}")
            return False
    
    def start_worker_threads(self):
        """Start background worker threads for simulation"""
        # Main simulation thread
        simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        simulation_thread.start()
        self.worker_threads.append(simulation_thread)
        
        # Update processor thread
        processor_thread = threading.Thread(target=self.process_updates, daemon=True)
        processor_thread.start()
        self.worker_threads.append(processor_thread)
        
        # System monitor thread (inspired by monitoring concepts)
        monitor_thread = threading.Thread(target=self.system_monitor, daemon=True)
        monitor_thread.start()
        self.worker_threads.append(monitor_thread)
    
    def simulation_loop(self):
        """Main simulation loop with enhanced error handling"""
        self.simulation_running = True
        iteration_count = 0
        
        while self.simulation_running:
            try:
                iteration_count += 1
                print(f"\n--- Enhanced Simulation Iteration {iteration_count} ---")
                
                # Process each train
                for train_id in list(self.train_states.keys()):
                    try:
                        self.simulate_single_train(train_id)
                    except Exception as e:
                        print(f"Error simulating train {train_id}: {e}")
                        continue
                
                # Occasional system events (inspired by alert system)
                if iteration_count % 20 == 0:  # Every 20 iterations
                    self.generate_system_event()
                
                # Dynamic sleep interval
                sleep_time = random.randint(*self.update_interval)
                print(f"Simulation sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Critical error in simulation loop: {e}")
                time.sleep(10)  # Longer sleep on critical errors
    
    def simulate_single_train(self, train_id):
        """Enhanced single train simulation with intelligent movement"""
        train_state = self.train_states[train_id]
        current_station_id = train_state['current_station_id']
        line = train_state['line']
        
        # Get connected stations based on line and fare data
        connected_stations = self.get_connected_stations(current_station_id, line)
        
        if not connected_stations:
            # Fallback to random movement
            available_stations = [s for s in self.stations if s['station_id'] != current_station_id]
            if available_stations:
                new_station = random.choice(available_stations)
            else:
                return
        else:
            # Intelligent movement based on direction and line
            new_station = self.choose_next_station(train_id, connected_stations)
        
        if new_station:
            # Update database with enhanced function
            update_train_position_enhanced(
                train_id,
                new_station['station_id'],
                new_station['latitude'],
                new_station['longitude'],
                random.randint(-10, 20)  # Random passenger change
            )
            
            # Update local state
            train_state['current_station_id'] = new_station['station_id']
            train_state['last_update'] = time.time()
            
            # Queue update for broadcast
            update_data = {
                'train_id': train_id,
                'station_id': new_station['station_id'],
                'station_name': new_station['name'],
                'latitude': new_station['latitude'],
                'longitude': new_station['longitude'],
                'timestamp': time.time(),
                'previous_station_id': current_station_id,
                'line': line,
                'speed_factor': train_state['speed_factor']
            }
            
            self.update_queue.put(update_data)
    
    def get_connected_stations(self, station_id, line):
        """Get stations connected to current station on the same line"""
        try:
            with get_db_connection() as conn:
                # Get directly connected stations from fare table
                connected = conn.execute('''
                    SELECT DISTINCT s.station_id, s.name, s.latitude, s.longitude
                    FROM fares f
                    JOIN stations s ON (f.destination_id = s.station_id OR f.origin_id = s.station_id)
                    WHERE (f.origin_id = ? OR f.destination_id = ?) AND s.station_id != ?
                ''', (station_id, station_id, station_id)).fetchall()
                
                return [dict(station) for station in connected]
        except Exception as e:
            print(f"Error getting connected stations: {e}")
            return []
    
    def choose_next_station(self, train_id, connected_stations):
        """Intelligent station selection based on train direction and patterns"""
        train_state = self.train_states[train_id]
        
        if not connected_stations:
            return None
        
        # Simple direction-based logic (can be enhanced)
        if len(connected_stations) == 1:
            return connected_stations[0]
        
        # For multiple options, add some intelligence
        if train_state['direction'] == 'forward':
            # Prefer stations with higher IDs
            return max(connected_stations, key=lambda s: s['station_id'])
        else:
            # Prefer stations with lower IDs
            return min(connected_stations, key=lambda s: s['station_id'])
    
    def process_updates(self):
        """Process queued updates for broadcasting"""
        while True:
            try:
                if not self.update_queue.empty():
                    update_data = self.update_queue.get()
                    
                    # Broadcast using enhanced method
                    broadcast_train_update_enhanced(self.socketio, update_data)
                    
                    # Mark task as done
                    self.update_queue.task_done()
                else:
                    time.sleep(0.1)  # Short sleep when queue is empty
                    
            except Exception as e:
                print(f"Error processing updates: {e}")
                time.sleep(1)
    
    def system_monitor(self):
        """System monitoring thread (inspired by monitoring examples)"""
        while True:
            try:
                # Monitor simulation health
                if self.simulation_running:
                    active_trains = len(self.train_states)
                    queue_size = self.update_queue.qsize()
                    
                    if queue_size > 50:  # Queue backup warning
                        broadcast_system_alert(self.socketio, {
                            'type': 'SYSTEM_WARNING',
                            'message': f'Update queue backup detected: {queue_size} pending updates',
                            'severity': 2,
                            'zone': 'system'
                        })
                    
                    # Log system stats every 5 minutes
                    print(f"System Monitor: {active_trains} trains active, queue size: {queue_size}")
                
                time.sleep(300)  # Monitor every 5 minutes
                
            except Exception as e:
                print(f"Error in system monitor: {e}")
                time.sleep(60)
    
    def generate_system_event(self):
        """Generate occasional system events for realism"""
        events = [
            {'type': 'MAINTENANCE', 'message': 'Scheduled maintenance completed', 'severity': 1},
            {'type': 'TRAFFIC', 'message': 'Minor delay on LRT Ampang line', 'severity': 2},
            {'type': 'INFO', 'message': 'Service operating normally', 'severity': 1},
        ]
        
        event = random.choice(events)
        broadcast_system_alert(self.socketio, event)
    
    def stop_simulation(self):
        """Stop the simulation gracefully"""
        print("Stopping enhanced simulation...")
        self.simulation_running = False
        
        # Wait for queue to empty
        self.update_queue.join()
        
        print("Enhanced simulation stopped")
    
    def get_simulation_stats(self):
        """Get detailed simulation statistics"""
        return {
            'active_trains': len(self.train_states),
            'stations_count': len(self.stations),
            'queue_size': self.update_queue.qsize(),
            'worker_threads': len(self.worker_threads),
            'simulation_running': self.simulation_running,
            'train_states': dict(self.train_states)
        }

# Global simulator instance
_simulator_instance = None

def start_data_generator(socketio):
    """
    Enhanced data generator startup function
    """
    global _simulator_instance
    
    print("Starting Enhanced Data Generator...")
    
    # Create simulator instance
    _simulator_instance = EnhancedTrainSimulator(socketio)
    
    # Initialize and start simulation
    if _simulator_instance.initialize_simulation():
        print("Enhanced data generator started successfully!")
    else:
        print("Failed to start enhanced data generator")

def get_simulator_instance():
    """Get the current simulator instance for external access"""
    return _simulator_instance

# Backward compatibility functions
def add_train_to_simulation(train_id, initial_station_id):
    """Enhanced train addition with validation"""
    if _simulator_instance:
        try:
            stations = _simulator_instance.stations
            initial_station = next((s for s in stations if s['station_id'] == initial_station_id), None)
            
            if initial_station:
                with get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO trains (train_id, current_station_id, latitude, longitude, line)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (train_id, initial_station_id, initial_station['latitude'], 
                          initial_station['longitude'], 'Dynamic'))
                    conn.commit()
                
                # Update simulator state
                _simulator_instance.train_states[train_id] = {
                    'current_station_id': initial_station_id,
                    'line': 'Dynamic',
                    'last_update': time.time(),
                    'direction': 'forward',
                    'speed_factor': random.uniform(0.8, 1.2)
                }
                
                print(f"Enhanced: Added Train {train_id} at Station {initial_station_id}")
                return True
            else:
                print(f"Invalid station {initial_station_id} for new train")
                return False
                
        except Exception as e:
            print(f"Error adding train {train_id}: {e}")
            return False
    
    return False

def remove_train_from_simulation(train_id):
    """Enhanced train removal with cleanup"""
    if _simulator_instance:
        try:
            with get_db_connection() as conn:
                result = conn.execute('DELETE FROM trains WHERE train_id = ?', (train_id,))
                conn.commit()
                
                if result.rowcount > 0:
                    # Remove from simulator state
                    if train_id in _simulator_instance.train_states:
                        del _simulator_instance.train_states[train_id]
                    
                    print(f"Enhanced: Removed Train {train_id} from simulation")
                    return True
                else:
                    print(f"Train {train_id} not found in simulation")
                    return False
                    
        except Exception as e:
            print(f"Error removing train {train_id}: {e}")
            return False
    
    return False

def get_simulation_stats():
    """Get enhanced simulation statistics"""
    if _simulator_instance:
        return _simulator_instance.get_simulation_stats()
    else:
        return {'error': 'Simulator not initialized'}

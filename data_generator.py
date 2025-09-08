"""
Data Generator for KL Metro System
Implements train simulation with line-based movement
"""

import time
import random
import threading
from queue import Queue
from database_enhanced import get_db_connection, get_all_stations, update_train_position_enhanced
from realtime_enhanced import broadcast_train_update_enhanced, broadcast_system_alert
from train_movement import TrainMovement

class TrainSimulator:
    """Train simulator with line-based movement"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.stations = []
        self.simulation_running = False
        self.update_queue = Queue()
        self.worker_threads = []
        self.train_states = {}
        self.update_interval = (4, 8)  # Realistic movement intervals
        self.train_movement = TrainMovement()  # Initialize movement system
        
    def initialize_simulation(self):
        """Initialize simulation with stations and trains"""
        try:
            print("Initializing Train Simulation...")
            
            # Load stations
            self.stations = get_all_stations()
            if not self.stations:
                raise Exception("No stations available for simulation")
            
            # Initialize train states
            self.init_train_states()
            
            # Start worker threads
            self.start_worker_threads()
            
            print(f"Simulation initialized with {len(self.stations)} stations and {len(self.train_states)} trains")
            return True
            
        except Exception as e:
            print(f"Failed to initialize simulation: {e}")
            return False
    
    def init_train_states(self):
        """Initialize train positions"""
        print("Initializing train states...")
        try:
            with get_db_connection() as conn:
                print("Connected to database for train initialization")
                
                # Load existing trains from database instead of clearing them
                existing_trains = conn.execute('SELECT train_id, current_station_id FROM trains').fetchall()
                print(f"Found {len(existing_trains)} existing trains in database")
                
                # Initialize train states for existing trains
                for train_id, station_id in existing_trains:
                    self.train_states[train_id] = {
                        'current_station_id': station_id,
                        'last_update': time.time(),
                        'active': True
                    }
                    print(f"Initialized train {train_id} at station {station_id}")
                
                print("Adding line column if needed...")
                # Add line column to trains table safely
                try:
                    conn.execute('ALTER TABLE trains ADD COLUMN line TEXT DEFAULT "Unknown"')
                    print("Added 'line' column to trains table")
                except Exception as e:
                    # Column probably already exists
                    print(f"Column 'line' handling: {e}")
                    pass
                
                print("Committing changes...")
                conn.commit()
                print(f"Train states initialized successfully with {len(self.train_states)} trains")
                
        except Exception as e:
            print(f"Error initializing train states: {e}")
            raise
    
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
        
        # System monitor thread
        monitor_thread = threading.Thread(target=self.system_monitor, daemon=True)
        monitor_thread.start()
        self.worker_threads.append(monitor_thread)
    
    def simulation_loop(self):
        """Main simulation loop"""
        self.simulation_running = True
        iteration_count = 0
        
        while self.simulation_running:
            try:
                iteration_count += 1
                print(f"\n--- Simulation Iteration {iteration_count} ---")
                
                # Process each train
                for train_id in list(self.train_states.keys()):
                    try:
                        self.simulate_single_train(train_id)
                    except Exception as e:
                        print(f"Error simulating train {train_id}: {e}")
                        continue
                
                # Occasional system events
                if iteration_count % 20 == 0:  # Every 20 iterations
                    self.generate_system_event()
                
                # Dynamic sleep interval
                sleep_time = random.randint(*self.update_interval)
                print(f"Simulation sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Critical error in simulation loop: {e}")
                time.sleep(10)
    
    def simulate_single_train(self, train_id):
        """Simulate single train movement using line-based movement"""
        try:
            # Use train movement system
            movement_result = self.train_movement.move_train(train_id)
            
            if movement_result:
                # Update local state
                if train_id in self.train_states:
                    self.train_states[train_id]['current_station_id'] = movement_result['station_id']
                    self.train_states[train_id]['last_update'] = time.time()
                
                # Queue update for broadcast
                self.update_queue.put(movement_result)
                
                print(f"🚊 Train {train_id}: {movement_result['station_name']} ({movement_result['direction']}) "
                      f"on {movement_result['line']}")
            else:
                print(f"⚠️  Train {train_id} movement failed - skipping this cycle")
                
        except Exception as e:
            print(f"❌ Error in train {train_id} simulation: {e}")
    
    def process_updates(self):
        """Process queued updates for broadcasting"""
        while True:
            try:
                if not self.update_queue.empty():
                    update_data = self.update_queue.get()
                    
                    # Broadcast update
                    broadcast_train_update_enhanced(self.socketio, update_data)
                    
                    # Mark task as done
                    self.update_queue.task_done()
                else:
                    time.sleep(0.1)  # Short sleep when queue is empty
                    
            except Exception as e:
                print(f"Error processing updates: {e}")
                time.sleep(1)
    
    def system_monitor(self):
        """System monitoring thread"""
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
        """Generate occasional system events"""
        events = [
            {'type': 'MAINTENANCE', 'message': 'Scheduled maintenance completed', 'severity': 1},
            {'type': 'TRAFFIC', 'message': 'Minor delay on LRT Ampang line', 'severity': 2},
            {'type': 'INFO', 'message': 'Service operating normally', 'severity': 1},
        ]
        
        event = random.choice(events)
        broadcast_system_alert(self.socketio, event)
    
    def stop_simulation(self):
        """Stop the simulation gracefully"""
        print("Stopping simulation...")
        self.simulation_running = False
        
        # Wait for queue to empty
        self.update_queue.join()
        
        print("Simulation stopped")
    
    def get_simulation_stats(self):
        """Get simulation statistics"""
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
    """Start the data generator"""
    global _simulator_instance
    
    print("Starting Data Generator...")
    
    # Create simulator instance
    _simulator_instance = TrainSimulator(socketio)
    
    # Initialize and start simulation
    if _simulator_instance.initialize_simulation():
        print("Data generator started successfully!")
    else:
        print("Failed to start data generator")

def get_simulator_instance():
    """Get the current simulator instance"""
    return _simulator_instance

def add_train_to_simulation(train_id, initial_station_id):
    """Add train to simulation"""
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
                
                print(f"Added Train {train_id} at Station {initial_station_id}")
                return True
            else:
                print(f"Invalid station {initial_station_id} for new train")
                return False
                
        except Exception as e:
            print(f"Error adding train {train_id}: {e}")
            return False
    
    return False

def remove_train_from_simulation(train_id):
    """Remove train from simulation"""
    if _simulator_instance:
        try:
            with get_db_connection() as conn:
                result = conn.execute('DELETE FROM trains WHERE train_id = ?', (train_id,))
                conn.commit()
                
                if result.rowcount > 0:
                    # Remove from simulator state
                    if train_id in _simulator_instance.train_states:
                        del _simulator_instance.train_states[train_id]
                    
                    print(f"Removed Train {train_id} from simulation")
                    return True
                else:
                    print(f"Train {train_id} not found in simulation")
                    return False
                    
        except Exception as e:
            print(f"Error removing train {train_id}: {e}")
            return False
    
    return False

def get_simulation_stats():
    """Get simulation statistics"""
    if _simulator_instance:
        return _simulator_instance.get_simulation_stats()
    else:
        return {'error': 'Simulator not initialized'}

"""
Data Generator Module for Real-Time KL Metro Tracking System
Simulates train movements and generates real-time position updates
"""

import time
import random
import threading
from database import get_db_connection, update_train_position, get_all_stations
from realtime import broadcast_train_update

def start_data_generator(socketio):
    """
    Start the background data generator - FR2
    This function runs in a separate thread to continuously generate train updates
    """
    print("Data generator thread started...")
    
    # Wait a bit for the system to initialize
    time.sleep(2)
    
    try:
        # Run the train simulation loop
        simulate_train_movements(socketio)
    except Exception as e:
        print(f"Error in data generator: {e}")

def simulate_train_movements(socketio):
    """
    Main simulation loop for train movements - FR2.1, FR2.2, FR2.3
    Updates train positions every 2-5 seconds and broadcasts via WebSocket
    """
    print("Starting train movement simulation...")
    
    # Get all available stations for movement simulation
    stations = get_all_stations()
    if not stations:
        print("No stations available for simulation!")
        return
    
    station_dict = {station['station_id']: station for station in stations}
    print(f"Simulation running with {len(stations)} stations")
    
    iteration_count = 0
    
    while True:
        try:
            iteration_count += 1
            print(f"\n--- Simulation Iteration {iteration_count} ---")
            
            # Get current train positions
            with get_db_connection() as conn:
                trains = conn.execute('SELECT * FROM trains ORDER BY train_id').fetchall()
                
                for train in trains:
                    train_id = train['train_id']
                    current_station_id = train['current_station_id']
                    
                    # Simulate train movement to a new station
                    new_station = simulate_train_movement(
                        train_id, 
                        current_station_id, 
                        station_dict, 
                        conn
                    )
                    
                    if new_station:
                        # Update database
                        update_train_position(
                            train_id,
                            new_station['station_id'],
                            new_station['latitude'],
                            new_station['longitude']
                        )
                        
                        # Prepare update data for broadcast - FR2.3
                        update_data = {
                            'train_id': train_id,
                            'station_id': new_station['station_id'],
                            'station_name': new_station['name'],
                            'latitude': new_station['latitude'],
                            'longitude': new_station['longitude'],
                            'timestamp': time.time(),
                            'previous_station_id': current_station_id
                        }
                        
                        # Broadcast update via WebSocket - FR4.2
                        broadcast_train_update(socketio, update_data)
            
            # Wait before next update cycle - FR2.2 (2-5 seconds)
            sleep_time = random.randint(3, 6)
            print(f"Waiting {sleep_time} seconds before next update...")
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Error in simulation iteration {iteration_count}: {e}")
            time.sleep(5)  # Wait before retrying

def simulate_train_movement(train_id, current_station_id, station_dict, conn):
    """
    Simulate movement of a single train to a connected station
    
    Args:
        train_id: ID of the train to move
        current_station_id: Current station of the train
        station_dict: Dictionary of all stations
        conn: Database connection
    
    Returns:
        Dictionary of new station data, or None if no movement
    """
    try:
        # Get stations connected to current station (via fare table)
        connected_stations = conn.execute('''
            SELECT DISTINCT destination_id 
            FROM fares 
            WHERE origin_id = ?
        ''', (current_station_id,)).fetchall()
        
        # Also check reverse connections
        reverse_connected = conn.execute('''
            SELECT DISTINCT origin_id 
            FROM fares 
            WHERE destination_id = ?
        ''', (current_station_id,)).fetchall()
        
        # Combine all possible destinations
        possible_destinations = set()
        for station in connected_stations:
            possible_destinations.add(station['destination_id'])
        for station in reverse_connected:
            possible_destinations.add(station['origin_id'])
        
        # Remove current station from possibilities
        possible_destinations.discard(current_station_id)
        
        if not possible_destinations:
            # No connected stations found, move to a random station
            print(f"Train {train_id}: No connected stations found, moving randomly")
            possible_destinations = [s['station_id'] for s in station_dict.values() 
                                   if s['station_id'] != current_station_id]
        
        # Choose a random destination
        if possible_destinations:
            new_station_id = random.choice(list(possible_destinations))
            new_station = station_dict.get(new_station_id)
            
            if new_station:
                print(f"Train {train_id}: Moving from Station {current_station_id} to Station {new_station_id} ({new_station['name']})")
                return new_station
            else:
                print(f"Train {train_id}: Invalid destination station {new_station_id}")
        else:
            print(f"Train {train_id}: No valid destinations found")
        
        return None
        
    except Exception as e:
        print(f"Error simulating movement for train {train_id}: {e}")
        return None

def add_train_to_simulation(train_id, initial_station_id):
    """
    Add a new train to the simulation
    
    Args:
        train_id: Unique ID for the new train
        initial_station_id: Starting station for the train
    """
    try:
        stations = get_all_stations()
        initial_station = next((s for s in stations if s['station_id'] == initial_station_id), None)
        
        if initial_station:
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO trains (train_id, current_station_id, latitude, longitude)
                    VALUES (?, ?, ?, ?)
                ''', (train_id, initial_station_id, initial_station['latitude'], initial_station['longitude']))
                conn.commit()
                
            print(f"Added Train {train_id} at Station {initial_station_id} ({initial_station['name']})")
            return True
        else:
            print(f"Invalid initial station {initial_station_id} for new train")
            return False
            
    except Exception as e:
        print(f"Error adding train {train_id}: {e}")
        return False

def remove_train_from_simulation(train_id):
    """
    Remove a train from the simulation
    
    Args:
        train_id: ID of the train to remove
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute('DELETE FROM trains WHERE train_id = ?', (train_id,))
            conn.commit()
            
            if result.rowcount > 0:
                print(f"Removed Train {train_id} from simulation")
                return True
            else:
                print(f"Train {train_id} not found in simulation")
                return False
                
    except Exception as e:
        print(f"Error removing train {train_id}: {e}")
        return False

def get_simulation_stats():
    """
    Get current simulation statistics
    
    Returns:
        Dictionary with simulation statistics
    """
    try:
        with get_db_connection() as conn:
            train_count = conn.execute('SELECT COUNT(*) as count FROM trains').fetchone()['count']
            station_count = conn.execute('SELECT COUNT(*) as count FROM stations').fetchone()['count']
            
            # Get train positions
            trains = conn.execute('''
                SELECT t.train_id, t.current_station_id, s.name as station_name
                FROM trains t
                LEFT JOIN stations s ON t.current_station_id = s.station_id
                ORDER BY t.train_id
            ''').fetchall()
            
            return {
                'train_count': train_count,
                'station_count': station_count,
                'trains': [dict(train) for train in trains],
                'timestamp': time.time()
            }
            
    except Exception as e:
        print(f"Error getting simulation stats: {e}")
        return {'error': str(e)}

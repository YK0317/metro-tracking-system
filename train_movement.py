"""
Train Movement Logic for KL Metro System
Implements realistic line-based sequential movement
"""

from database_enhanced import get_db_connection, update_train_position_enhanced
import random
import time

class TrainMovement:
    """Handles realistic train movement along KL Metro lines"""
    
    def __init__(self):
        self.line_sequences = self.get_line_sequences()
        self.train_states = {}
        
    def get_line_sequences(self):
        """Define actual KL Metro line sequences based on real topology"""
        return {
            'LRT Kelana Jaya': [
                "Gombak", "Taman Melati", "Wangsa Maju", "Sri Rampai", 
                "Setiawangsa", "Jelatek", "Dato' Keramat", "Damai",
                "Ampang Park", "KLCC", "Kampung Baru", "Dang Wangi",
                "Masjid Jamek (KJL)", "Pasar Seni (KJL)", "KL Sentral (KJL)",
                "Bangsar", "Abdullah Hukum", "Kerinchi", "Universiti",
                "Taman Jaya", "Asia Jaya", "Taman Paramount", "Taman Bahagia",
                "Kelana Jaya", "Lembah Subang", "Ara Damansara", "Glenmarie",
                "Subang Jaya", "SS 15", "SS 18", "USJ 7 (KJL)", "Taipan",
                "Wawasan", "USJ 21", "Alam Megah", "Subang Alam", "Putra Heights (KJL)"
            ],
            
            'LRT Ampang': [
                "Sungai Buloh", "Kampung Selamat", "Kwasa Damansara", "Kwasa Sentral",
                "Kota Damansara", "Surian", "Mutiara Damansara", "Bandar Utama",
                "TTDI", "Phileo Damansara", "Pusat Bandar Damansara", "Semantan",
                "Muzium Negara"
            ],
            
            'MRT SBK': [
                "Pasar Seni (SBK)", "Merdeka", "Bukit Bintang", "Tun Razak Exchange (TRX)",
                "Cochrane", "Maluri (SBK)", "Taman Pertama", "Taman Midah",
                "Taman Mutiara", "Taman Connaught", "Taman Suntex", "Sri Raya",
                "Bandar Tun Hussein Onn", "Batu 11 Cheras", "Bukit Dukung",
                "Sungai Jernih", "Stadium Kajang", "Kajang"
            ]
        }
    
    def get_station_id(self, station_name):
        """Get station ID from database by name"""
        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    'SELECT station_id FROM stations WHERE name = ?',
                    (station_name,)
                ).fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting station ID for {station_name}: {e}")
            return None
    
    def get_station(self, station_id):
        """Get station details by ID"""
        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    'SELECT station_id, name, latitude, longitude, line FROM stations WHERE station_id = ?',
                    (station_id,)
                ).fetchone()
                if result:
                    return {
                        'station_id': result[0],
                        'name': result[1],
                        'latitude': result[2],
                        'longitude': result[3],
                        'line': result[4]
                    }
                return None
        except Exception as e:
            print(f"Error getting station by ID {station_id}: {e}")
            return None
    
    def get_travel_time(self, origin_id, dest_id):
        """Get travel time from Time.csv data stored in fares table"""
        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    'SELECT travel_time_min FROM fares WHERE origin_id = ? AND destination_id = ?',
                    (origin_id, dest_id)
                ).fetchone()
                
                if result and result[0] > 0:
                    # Add realistic variation (±20%)
                    base_time = result[0]
                    variation = random.uniform(0.8, 1.2)
                    return max(1, int(base_time * variation))
                
                # Default time if no data found
                return 3
                
        except Exception as e:
            print(f"Error getting travel time: {e}")
            return 3
    
    def initialize_train(self, train_id, current_station_id, line):
        """Initialize train state for movement"""
        try:
            current_station = self.get_station(current_station_id)
            if not current_station:
                print(f"Warning: Could not find station {current_station_id}")
                return False
            
            station_name = current_station['name']
            
            # Find which line sequence this station belongs to
            for line_name, sequence in self.line_sequences.items():
                if station_name in sequence:
                    position = sequence.index(station_name)
                    
                    # Determine initial direction based on position
                    # Start near beginning -> forward, near end -> backward
                    initial_direction = 'forward'
                    if position > len(sequence) * 0.7:  # If in last 30% of line
                        initial_direction = 'backward'
                    
                    self.train_states[train_id] = {
                        'current_station_id': current_station_id,
                        'current_station_name': station_name,
                        'line': line_name,
                        'line_sequence': sequence,
                        'position_in_sequence': position,
                        'direction': initial_direction,
                        'last_update': time.time(),
                        'speed_factor': random.uniform(0.9, 1.1),
                        'direction_changes': 0
                    }
                    
                    print(f"Train {train_id} initialized on {line_name} at {station_name} "
                          f"(position {position}/{len(sequence)-1}) direction: {initial_direction}")
                    return True
            
            print(f"Warning: Station {station_name} not found in any line sequence")
            return False
            
        except Exception as e:
            print(f"Error initializing train {train_id}: {e}")
            return False
    
    def get_next_station(self, train_id):
        """Get next station following line sequence"""
        if train_id not in self.train_states:
            print(f"Train {train_id} state not initialized")
            return None
        
        state = self.train_states[train_id]
        sequence = state['line_sequence']
        current_pos = state['position_in_sequence']
        direction = state['direction']
        
        try:
            if direction == 'forward':
                if current_pos < len(sequence) - 1:
                    # Move to next station
                    next_pos = current_pos + 1
                    next_station_name = sequence[next_pos]
                else:
                    # Reached end of line, reverse direction
                    state['direction'] = 'backward'
                    state['direction_changes'] = state.get('direction_changes', 0) + 1
                    next_pos = current_pos - 1
                    next_station_name = sequence[next_pos]
                    print(f"🔄 Train {train_id} reached END of {state['line']}, reversing to BACKWARD "
                          f"(changes: {state['direction_changes']})")
            
            else:  # backward
                if current_pos > 0:
                    # Move to previous station
                    next_pos = current_pos - 1
                    next_station_name = sequence[next_pos]
                else:
                    # Reached start of line, reverse direction
                    state['direction'] = 'forward'
                    state['direction_changes'] = state.get('direction_changes', 0) + 1
                    next_pos = current_pos + 1
                    next_station_name = sequence[next_pos]
                    print(f"🔄 Train {train_id} reached START of {state['line']}, reversing to FORWARD "
                          f"(changes: {state['direction_changes']})")
            
            # Get station details
            next_station_id = self.get_station_id(next_station_name)
            if next_station_id:
                next_station = self.get_station(next_station_id)
                if next_station:
                    # Update state
                    state['position_in_sequence'] = next_pos
                    state['current_station_id'] = next_station_id
                    state['current_station_name'] = next_station_name
                    state['last_update'] = time.time()
                    
                    # Calculate travel time
                    travel_time = self.get_travel_time(state['current_station_id'], next_station_id)
                    next_station['travel_time'] = travel_time
                    
                    return next_station
            
            print(f"Could not find next station: {next_station_name}")
            return None
            
        except Exception as e:
            print(f"Error getting next station for train {train_id}: {e}")
            return None
    
    def move_train(self, train_id):
        """Move train using line-based movement"""
        try:
            # Initialize train state if not exists
            if train_id not in self.train_states:
                # Get current train position from database
                with get_db_connection() as conn:
                    train_data = conn.execute(
                        'SELECT current_station_id, line FROM trains WHERE train_id = ?',
                        (train_id,)
                    ).fetchone()
                    
                    if train_data:
                        current_station_id, line = train_data
                        if not self.initialize_train(train_id, current_station_id, line):
                            return None
                    else:
                        print(f"Train {train_id} not found in database")
                        return None
            
            # Capture current station name BEFORE getting next station
            state = self.train_states[train_id]
            old_station_name = state['current_station_name']
            
            # Get next station following sequence
            next_station = self.get_next_station(train_id)
            
            if next_station:
                # Update database with new position
                update_train_position_enhanced(
                    train_id,
                    next_station['station_id'],
                    next_station['latitude'],
                    next_station['longitude'],
                    random.randint(-5, 15)  # Passenger change
                )
                
                print(f"Train {train_id} moved from {old_station_name} to {next_station['name']} "
                      f"({state['direction']}) on {state['line']}")
                
                return {
                    'train_id': train_id,
                    'station_id': next_station['station_id'],
                    'station_name': next_station['name'],
                    'latitude': next_station['latitude'],
                    'longitude': next_station['longitude'],
                    'line': state['line'],
                    'direction': state['direction'],
                    'travel_time': next_station.get('travel_time', 3),
                    'timestamp': time.time()
                }
            
            return None
            
        except Exception as e:
            print(f"Error moving train {train_id}: {e}")
            return None

# Global instance
train_movement = TrainMovement()

def initialize_all_trains():
    """Initialize movement for all trains in database"""
    try:
        with get_db_connection() as conn:
            trains = conn.execute('SELECT train_id, current_station_id, line FROM trains').fetchall()
            
            for train_id, station_id, line in trains:
                success = train_movement.initialize_train(train_id, station_id, line)
                if success:
                    print(f"✅ Train {train_id} initialized for movement")
                else:
                    print(f"❌ Failed to initialize train {train_id}")
                    
    except Exception as e:
        print(f"Error initializing trains: {e}")

def test_movement():
    """Test the movement system"""
    print("=== Testing Train Movement ===")
    
    # Initialize all trains
    initialize_all_trains()
    
    # Test movement for first few trains
    for i in range(3):
        train_id = i + 1
        print(f"\nTesting train {train_id}:")
        
        for move in range(5):
            result = train_movement.move_train(train_id)
            if result:
                print(f"  Move {move + 1}: {result['station_name']} ({result['direction']})")
            else:
                print(f"  Move {move + 1}: Failed")
            time.sleep(0.5)

if __name__ == "__main__":
    test_movement()

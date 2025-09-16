#!/usr/bin/env python3
"""
Generate trains for each metro line - one forward and one backward
"""

import sys

# Fix Windows console encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from database import get_db_connection
import random
import os

def get_line_stations(conn, line):
    """Get all stations for a specific line ordered by station_id"""
    stations = conn.execute(
        'SELECT station_id, name, latitude, longitude FROM stations WHERE line = ? ORDER BY station_id', 
        (line,)
    ).fetchall()
    return stations

def add_trains_for_lines():
    """Add 2 trains per line (forward and backward)"""
    conn = get_db_connection()
    
    # Clear existing trains first
    conn.execute('DELETE FROM trains')
    conn.commit()
    print("✅ Cleared existing trains")
    
    # Get available lines
    lines = conn.execute('SELECT DISTINCT line FROM stations ORDER BY line').fetchall()
    
    train_id = 1
    
    for line_row in lines:
        line = line_row[0]
        print(f"\n🚇 Setting up trains for {line} line...")
        
        # Get stations for this line
        stations = get_line_stations(conn, line)
        
        if not stations:
            print(f"❌ No stations found for line {line}")
            continue
            
        print(f"   Found {len(stations)} stations")
        
        # Forward train - starts at first station
        first_station = stations[0]
        conn.execute('''
            INSERT INTO trains (
                train_id, current_station_id, latitude, longitude, 
                line, direction, capacity, current_load, speed_kmh, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            train_id,
            first_station[0],  # station_id
            first_station[2],  # latitude
            first_station[3],  # longitude
            line,
            'forward',
            300,  # capacity
            random.randint(50, 200),  # current_load
            40.0,  # speed_kmh
            'active'
        ))
        
        print(f"   ➡️  Train {train_id} (Forward) at {first_station[1]}")
        train_id += 1
        
        # Backward train - starts at last station
        last_station = stations[-1]
        conn.execute('''
            INSERT INTO trains (
                train_id, current_station_id, latitude, longitude, 
                line, direction, capacity, current_load, speed_kmh, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            train_id,
            last_station[0],   # station_id
            last_station[2],   # latitude
            last_station[3],   # longitude
            line,
            'backward',
            300,  # capacity
            random.randint(50, 200),  # current_load
            40.0,  # speed_kmh
            'active'
        ))
        
        print(f"   ⬅️  Train {train_id} (Backward) at {last_station[1]}")
        train_id += 1
    
    conn.commit()
    
    # Verify trains were added
    trains = conn.execute('SELECT train_id, line, direction, current_station_id FROM trains ORDER BY train_id').fetchall()
    
    print(f"\n✅ Successfully added {len(trains)} trains:")
    for train in trains:
        station_name = conn.execute('SELECT name FROM stations WHERE station_id = ?', (train[3],)).fetchone()[0]
        print(f"   Train {train[0]}: {train[1]} line ({train[2]}) at {station_name}")
    
    conn.close()
    return len(trains)

def create_trains_csv():
    """Create a CSV file with the train data"""
    conn = get_db_connection()
    
    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Get all trains with station information
    trains_data = conn.execute('''
        SELECT t.train_id, t.line, t.direction, t.capacity, t.current_load, 
               t.speed_kmh, t.status, s.name as station_name, s.latitude, s.longitude
        FROM trains t
        JOIN stations s ON t.current_station_id = s.station_id
        ORDER BY t.train_id
    ''').fetchall()
    
    # Create CSV content
    csv_content = "train_id,line,direction,capacity,current_load,speed_kmh,status,current_station,latitude,longitude\n"
    
    for train in trains_data:
        csv_content += f"{train[0]},{train[1]},{train[2]},{train[3]},{train[4]},{train[5]},{train[6]},{train[7]},{train[8]},{train[9]}\n"
    
    # Write to CSV file
    with open('data/Trains.csv', 'w', newline='', encoding='utf-8') as f:
        f.write(csv_content)
    
    print(f"✅ Created data/Trains.csv with {len(trains_data)} trains")
    conn.close()

if __name__ == "__main__":
    print("🚇 Metro Train Generator")
    print("=" * 40)
    
    # Add trains to database
    train_count = add_trains_for_lines()
    
    # Create CSV file
    create_trains_csv()
    
    print(f"\n🎉 Setup complete! Added {train_count} trains to the system.")

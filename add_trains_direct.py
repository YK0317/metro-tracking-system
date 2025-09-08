"""
Add Trains to Running System
This script adds trains to the running Flask application by reading from CSV file
"""

import sqlite3
import time
import random
import csv
import os

def load_trains_from_csv():
    """Load train configuration from CSV file"""
    csv_file = 'data/Trains.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ Train configuration file not found: {csv_file}")
        return []
    
    trains = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                trains.append({
                    'train_id': int(row['train_id']),
                    'train_type': row['train_type'],
                    'initial_station_id': int(row['initial_station_id']),
                    'line': row['line'],
                    'max_speed': float(row['max_speed']),
                    'initial_passengers': int(row['initial_passengers']),
                    'status': row['status']
                })
        print(f"✅ Loaded {len(trains)} train configurations from CSV")
        return trains
        
    except Exception as e:
        print(f"❌ Error loading trains from CSV: {e}")
        return []

def add_trains_to_running_system():
    """Add trains directly to the database while Flask is running"""
    print("🚊 Adding Trains to Running System")
    print("=" * 40)
    
    try:
        # Wait a moment to ensure database is not locked
        print("⏳ Waiting for database access...")
        time.sleep(2)
        
        # Connect to database
        conn = sqlite3.connect('metro_tracking_enhanced.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Check if stations exist
        station_count = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
        if station_count == 0:
            print("❌ No stations found! Please run initialize_database.py first.")
            return False
        
        print(f"✅ Found {station_count} stations")
        
        # Load train configurations from CSV
        train_configs = load_trains_from_csv()
        if not train_configs:
            print("❌ No train configurations loaded. Cannot proceed.")
            return False
        
        # Clear existing trains
        print("🧹 Clearing existing trains...")
        conn.execute("DELETE FROM trains")
        conn.commit()
        
        trains_added = 0
        print("🚂 Adding trains to database...")
        
        for train_config in train_configs:
            try:
                train_id = train_config['train_id']
                station_id = train_config['initial_station_id']
                line = train_config['line']
                train_type = train_config['train_type']
                max_speed = train_config['max_speed']
                initial_passengers = train_config['initial_passengers']
                status = train_config['status']
                
                # Verify station exists
                station_data = conn.execute(
                    "SELECT name, latitude, longitude, line FROM stations WHERE station_id = ?", 
                    (station_id,)
                ).fetchone()
                
                if not station_data:
                    print(f"   ⚠️  Station {station_id} not found, skipping train {train_id}")
                    continue
                
                # Insert train
                conn.execute("""
                    INSERT INTO trains (
                        train_id, current_station_id, latitude, longitude, 
                        line, direction, capacity, current_load, speed_kmh, 
                        status, last_updated, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    train_id, station_id, station_data['latitude'], station_data['longitude'],
                    line, 'forward', 200, initial_passengers, max_speed, status
                ))
                
                print(f"   ✅ Train {train_id} ({train_type}) at {station_data['name']} (Station {station_id}) - {line} Line")
                trains_added += 1
                
            except Exception as e:
                print(f"   ❌ Failed to add Train {train_config.get('train_id', 'Unknown')}: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Verify trains were added
        final_count = conn.execute("SELECT COUNT(*) FROM trains WHERE status = 'active'").fetchone()[0]
        
        print(f"\n📊 Results:")
        print(f"   ✅ Successfully added: {trains_added} trains")
        print(f"   📈 Total active trains: {final_count}")
        
        # Show train details
        if final_count > 0:
            print(f"\n🚂 Current Active Trains:")
            trains = conn.execute("""
                SELECT t.train_id, t.line, s.name as station_name, t.speed_kmh, t.current_load
                FROM trains t
                JOIN stations s ON t.current_station_id = s.station_id
                WHERE t.status = 'active'
                ORDER BY t.line, t.train_id
            """).fetchall()
            
            for train in trains:
                print(f"   Train {train['train_id']} | {train['line']} Line | {train['station_name']} | {train['speed_kmh']} km/h | {train['current_load']} passengers")
        
        conn.close()
        
        if trains_added > 0:
            print(f"\n✅ Success! {trains_added} trains are now active!")
            print("🔄 The simulation should pick them up automatically within a few seconds.")
            print("📊 Check the Flask console for 'System Monitor' messages to see train counts.")
            return True
        else:
            print(f"\n❌ No trains were added successfully.")
            return False
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("❌ Database is locked. This might happen if:")
            print("   1. Flask app is initializing - wait a few seconds and try again")
            print("   2. Another process is using the database")
            print("   3. Try restarting the Flask app")
        else:
            print(f"❌ Database error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if add_trains_to_running_system():
        print("\n🎉 Trains added successfully!")
        print("🌐 Visit http://localhost:5000 to see the metro tracking system.")
        print("🚊 You should see train movements in the Flask console output.")
    else:
        print("\n❌ Failed to add trains.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Flask app is running and fully initialized")
        print("2. Wait for 'Data generator started successfully!' message")
        print("3. Try running this script again")
        print("4. Check Flask console for any error messages")

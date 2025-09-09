"""
Database Initialization Script
Loads station and fare data from CSV files into the database
"""

import sqlite3
import csv
import os

def initialize_database_with_data():
    """Initialize database with station and fare data from CSV files"""
    print("🚀 Database Initialization Script")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect('metro_tracking_enhanced.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Clear existing data
        print("🧹 Clearing existing data...")
        conn.execute("DELETE FROM fares")
        conn.execute("DELETE FROM stations")
        conn.commit()
        
        # Load stations from CSV header
        print("📍 Loading stations...")
        stations_loaded = load_stations_from_csv(conn)
        
        # Load fares from CSV
        print("💰 Loading fare data...")
        fares_loaded = load_fares_from_csv(conn)
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        print_database_summary(conn)
        
        conn.close()
        
        if stations_loaded > 0 and fares_loaded > 0:
            print("✅ Database initialization completed successfully!")
            return True
        else:
            print("❌ Some data failed to load.")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def load_stations_from_csv(conn):
    """Load station data from CSV file with accurate coordinates"""
    try:
        stations_loaded = 0
        
        # Check if Stations.csv exists
        if os.path.exists('data/Stations.csv'):
            print("📍 Loading stations from Stations.csv with accurate coordinates...")
            
            with open('data/Stations.csv', 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    # Insert station with data from CSV
                    conn.execute("""
                        INSERT INTO stations (station_id, name, latitude, longitude, line, zone, operational)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(row['station_id']),
                        row['name'],
                        float(row['latitude']),
                        float(row['longitude']),
                        row['line'],
                        int(row['zone']),
                        int(row['operational'])
                    ))
                    stations_loaded += 1
                    
        else:
            print("📍 Stations.csv not found, loading from Fare.csv header with hardcoded coordinates...")
            
            # Fallback: Read station names from CSV header
            with open('data/Fare.csv', 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                station_names = header[1:]  # Skip first empty column
            
            for i, station_name in enumerate(station_names, 1):
                # Use default coordinates (central KL) since Stations.csv should be used
                lat, lng, line = 3.1390, 101.6869, 'Unknown'
                print(f"⚠️  Using default coordinates for {station_name} - Stations.csv recommended")
                
                # Insert station
                conn.execute("""
                    INSERT INTO stations (station_id, name, latitude, longitude, line, zone, operational)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (i, station_name, lat, lng, line, 1, 1))
                
                stations_loaded += 1
        
        print(f"✅ Loaded {stations_loaded} stations")
        return stations_loaded
        
    except Exception as e:
        print(f"❌ Error loading stations: {e}")
        return 0

def load_fares_from_csv(conn):
    """Load fare data from CSV file"""
    try:
        fares_loaded = 0
        
        with open('data/Fare.csv', 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            station_names = header[1:]  # Skip first empty column
            
            for row_idx, row in enumerate(reader, 1):
                from_station = row[0]
                
                for col_idx, fare_str in enumerate(row[1:], 1):
                    to_station = station_names[col_idx - 1]
                    
                    try:
                        fare = float(fare_str)
                        
                        # Insert fare with correct column names
                        conn.execute("""
                            INSERT INTO fares (origin_id, destination_id, price, peak_price, distance_km, travel_time_min, fare_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (row_idx, col_idx, fare, fare * 1.2, col_idx * 2.5, col_idx * 3, 'standard'))  # Estimated values
                        
                        fares_loaded += 1
                        
                    except ValueError:
                        continue  # Skip invalid fare values
        
        print(f"✅ Loaded {fares_loaded} fare records")
        return fares_loaded
        
    except Exception as e:
        print(f"❌ Error loading fares: {e}")
        return 0

def print_database_summary(conn):
    """Print comprehensive database summary"""
    tables = ['stations', 'fares', 'trains', 'train_movements', 'system_events', 'user_sessions']
    
    print("\n" + "="*50)
    print("DATABASE SUMMARY")
    print("="*50)
    
    for table in tables:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            print(f"  - {table.capitalize()}: {count} records")
        except:
            print(f"  - {table.capitalize()}: Table not found")
    
    print("="*50)
    
    # Show sample stations
    print("\n📍 Sample Stations:")
    stations = conn.execute("SELECT station_id, name, line FROM stations LIMIT 10").fetchall()
    for station in stations:
        print(f"   {station['station_id']}: {station['name']} ({station['line']} Line)")
    
    print(f"   ... and {conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0] - 10} more stations")

if __name__ == "__main__":
    # Check if CSV files exist
    if not os.path.exists('data/Fare.csv'):
        print("❌ Fare.csv not found in data/ directory")
        exit(1)
    
    if not os.path.exists('data/Route.csv'):
        print("❌ Route.csv not found in data/ directory")
        exit(1)
    
    # Initialize database
    if initialize_database_with_data():
        print("\n🎉 Ready to start the metro tracking system!")
        print("   Run: python app.py")
    else:
        print("\n❌ Initialization failed. Check the errors above.")

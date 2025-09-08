"""
Database Initialization Script
Loads station and fare data from CSV files into the database
"""

import sqlite3
import csv
import os

# Station coordinates (approximate real coordinates for KL metro stations)
STATION_COORDINATES = {
    'Gombak': (3.2647, 101.6478, 'KJL'),
    'Taman Melati': (3.2732, 101.6532, 'KJL'),
    'Wangsa Maju': (3.2806, 101.6587, 'KJL'),
    'Sri Rampai': (3.2889, 101.6641, 'KJL'),
    'Setiawangsa': (3.2972, 101.6695, 'KJL'),
    'Jelatek': (3.3056, 101.6750, 'KJL'),
    "Dato' Keramat": (3.3139, 101.6804, 'KJL'),
    'Damai': (3.3222, 101.6858, 'KJL'),
    'Ampang Park': (3.3306, 101.6913, 'KJL'),
    'KLCC': (3.3389, 101.6967, 'KJL'),
    'Kampung Baru': (3.3472, 101.7021, 'KJL'),
    'Dang Wangi': (3.3556, 101.7076, 'KJL'),
    'Masjid Jamek (KJL)': (3.3639, 101.7130, 'KJL'),
    'Pasar Seni (KJL)': (3.3722, 101.7184, 'KJL'),
    'KL Sentral (KJL)': (3.3806, 101.7239, 'KJL'),
    'Bangsar': (3.3889, 101.7293, 'KJL'),
    'Abdullah Hukum': (3.3972, 101.7347, 'KJL'),
    'Kerinchi': (3.4056, 101.7402, 'KJL'),
    'Universiti': (3.4139, 101.7456, 'KJL'),
    'Taman Jaya': (3.4222, 101.7510, 'KJL'),
    'Asia Jaya': (3.4306, 101.7565, 'KJL'),
    'Taman Paramount': (3.4389, 101.7619, 'KJL'),
    'Taman Bahagia': (3.4472, 101.7673, 'KJL'),
    'Kelana Jaya': (3.4556, 101.7728, 'KJL'),
    'Lembah Subang': (3.4639, 101.7782, 'KJL'),
    'Ara Damansara': (3.4722, 101.7836, 'KJL'),
    'Glenmarie': (3.4806, 101.7891, 'KJL'),
    'Subang Jaya': (3.4889, 101.7945, 'KJL'),
    'SS 15': (3.4972, 101.7999, 'KJL'),
    'SS 18': (3.5056, 101.8054, 'KJL'),
    'USJ 7 (KJL)': (3.5139, 101.8108, 'KJL'),
    'Taipan': (3.5222, 101.8162, 'KJL'),
    'Wawasan': (3.5306, 101.8217, 'KJL'),
    'USJ 21': (3.5389, 101.8271, 'KJL'),
    'Alam Megah': (3.5472, 101.8325, 'KJL'),
    'Subang Alam': (3.5556, 101.8380, 'KJL'),
    'Putra Heights (KJL)': (3.5639, 101.8434, 'KJL'),
    
    # SBK Line stations
    'Sungai Buloh': (3.6500, 101.5500, 'SBK'),
    'Kampung Selamat': (3.6400, 101.5600, 'SBK'),
    'Kwasa Damansara': (3.6300, 101.5700, 'SBK'),
    'Kwasa Sentral': (3.6200, 101.5800, 'SBK'),
    'Kota Damansara': (3.6100, 101.5900, 'SBK'),
    'Surian': (3.6000, 101.6000, 'SBK'),
    'Mutiara Damansara': (3.5900, 101.6100, 'SBK'),
    'Bandar Utama': (3.5800, 101.6200, 'SBK'),
    'TTDI': (3.5700, 101.6300, 'SBK'),
    'Phileo Damansara': (3.5600, 101.6400, 'SBK'),
    'Pusat Bandar Damansara': (3.5500, 101.6500, 'SBK'),
    'Semantan': (3.5400, 101.6600, 'SBK'),
    'Muzium Negara': (3.5300, 101.6700, 'SBK'),
    'Pasar Seni (SBK)': (3.5200, 101.6800, 'SBK'),
    'Merdeka': (3.5100, 101.6900, 'SBK'),
    'Bukit Bintang': (3.5000, 101.7000, 'SBK'),
    'Tun Razak Exchange (TRX)': (3.4900, 101.7100, 'SBK'),
    'Cochrane': (3.4800, 101.7200, 'SBK'),
    'Maluri (SBK)': (3.4700, 101.7300, 'SBK'),
    'Taman Pertama': (3.4600, 101.7400, 'SBK'),
    'Taman Midah': (3.4500, 101.7500, 'SBK'),
    'Taman Mutiara': (3.4400, 101.7600, 'SBK'),
    'Taman Connaught': (3.4300, 101.7700, 'SBK'),
    'Taman Suntex': (3.4200, 101.7800, 'SBK'),
    'Sri Raya': (3.4100, 101.7900, 'SBK'),
    'Bandar Tun Hussein Onn': (3.4000, 101.8000, 'SBK'),
    'Batu 11 Cheras': (3.3900, 101.8100, 'SBK'),
    'Bukit Dukung': (3.3800, 101.8200, 'SBK'),
    'Sungai Jernih': (3.3700, 101.8300, 'SBK'),
    'Stadium Kajang': (3.3600, 101.8400, 'SBK'),
    'Kajang': (3.3500, 101.8500, 'SBK'),
}

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
                # Get coordinates and line info
                if station_name in STATION_COORDINATES:
                    lat, lng, line = STATION_COORDINATES[station_name]
                else:
                    # Default coordinates if not found
                    lat, lng, line = 3.1390, 101.6869, 'Unknown'
                    print(f"⚠️  Using default coordinates for {station_name}")
                
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

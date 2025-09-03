"""
Database Module for Real-Time KL Metro Tracking System
Handles SQLite database operations, CSV data ingestion, and database initialization
"""

import sqlite3
import csv
import os
from contextlib import contextmanager

DATABASE_PATH = 'metro_tracking.db'

def get_db_connection():
    """Get a database connection with row factory for easier access"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the SQLite database and create tables"""
    print("Initializing database...")
    
    with get_db() as conn:
        # Create stations table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                station_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        ''')
        
        # Create fares table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS fares (
                origin_id INTEGER,
                destination_id INTEGER,
                price REAL NOT NULL,
                PRIMARY KEY (origin_id, destination_id),
                FOREIGN KEY (origin_id) REFERENCES stations (station_id),
                FOREIGN KEY (destination_id) REFERENCES stations (station_id)
            )
        ''')
        
        # Create trains table for simulation state
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trains (
                train_id INTEGER PRIMARY KEY,
                current_station_id INTEGER,
                latitude REAL,
                longitude REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_station_id) REFERENCES stations (station_id)
            )
        ''')
        
        conn.commit()
        print("Database tables created successfully!")
        
        # Load CSV data if tables are empty
        load_csv_data(conn)

def load_csv_data(conn):
    """Load station and fare data from CSV files"""
    print("Loading CSV data...")
    
    # Check if data already exists
    stations_count = conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0]
    
    if stations_count == 0:
        print("Loading sample station data...")
        
        # Sample KL Metro stations (MyRapidKL network)
        sample_stations = [
            (1, 'KL Sentral', 3.1348, 101.6868),
            (2, 'Masjid Jamek', 3.1488, 101.6942),
            (3, 'KLCC', 3.1578, 101.7122),
            (4, 'Ampang Park', 3.1592, 101.7167),
            (5, 'Damai', 3.1735, 101.7258),
            (6, 'Jelatek', 3.1798, 101.7342),
            (7, 'Setiawangsa', 3.1842, 101.7425),
            (8, 'Wangsa Maju', 3.1886, 101.7508),
            (9, 'Sri Rampai', 3.1930, 101.7591),
            (10, 'Ampang', 3.1486, 101.7617),
            (11, 'Dang Wangi', 3.1471, 101.7000),
            (12, 'Plaza Rakyat', 3.1425, 101.6958),
            (13, 'Hang Tuah', 3.1383, 101.6925),
            (14, 'Pudu', 3.1333, 101.6892),
            (15, 'Chan Sow Lin', 3.1258, 101.6858),
        ]
        
        conn.executemany(
            'INSERT INTO stations (station_id, name, latitude, longitude) VALUES (?, ?, ?, ?)',
            sample_stations
        )
        
        print("Loading sample fare data...")
        
        # Sample fare matrix (simplified - in real system would be more comprehensive)
        sample_fares = [
            # From KL Sentral
            (1, 2, 2.50), (1, 3, 4.20), (1, 4, 4.50), (1, 11, 2.10),
            # From Masjid Jamek
            (2, 1, 2.50), (2, 3, 2.80), (2, 11, 1.50), (2, 12, 1.80),
            # From KLCC
            (3, 1, 4.20), (3, 2, 2.80), (3, 4, 1.50), (3, 5, 2.10),
            # From Ampang Park
            (4, 3, 1.50), (4, 5, 1.80), (4, 6, 2.10),
            # Continue pattern for all stations...
            (5, 4, 1.80), (5, 6, 1.50), (5, 7, 1.80),
            (6, 5, 1.50), (6, 7, 1.50), (6, 8, 1.80),
            (7, 6, 1.50), (7, 8, 1.50), (7, 9, 1.80),
            (8, 7, 1.50), (8, 9, 1.50), (8, 10, 2.10),
            (9, 8, 1.50), (9, 10, 1.80),
            (10, 9, 1.80), (10, 8, 2.10),
            # Cross-connections
            (11, 1, 2.10), (11, 2, 1.50), (11, 12, 1.50),
            (12, 11, 1.50), (12, 2, 1.80), (12, 13, 1.50),
            (13, 12, 1.50), (13, 1, 2.80), (13, 14, 1.50),
            (14, 13, 1.50), (14, 15, 1.50),
            (15, 14, 1.50), (15, 1, 3.50),
        ]
        
        conn.executemany(
            'INSERT INTO fares (origin_id, destination_id, price) VALUES (?, ?, ?)',
            sample_fares
        )
        
        # Initialize some trains
        print("Initializing train positions...")
        initial_trains = [
            (1, 1, 3.1348, 101.6868),  # Train 1 at KL Sentral
            (2, 3, 3.1578, 101.7122),  # Train 2 at KLCC
            (3, 10, 3.1486, 101.7617), # Train 3 at Ampang
            (4, 15, 3.1258, 101.6858), # Train 4 at Chan Sow Lin
        ]
        
        conn.executemany(
            'INSERT INTO trains (train_id, current_station_id, latitude, longitude) VALUES (?, ?, ?, ?)',
            initial_trains
        )
        
        conn.commit()
        print("Sample data loaded successfully!")
        
        # Print summary
        stations_count = conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0]
        fares_count = conn.execute('SELECT COUNT(*) FROM fares').fetchone()[0]
        trains_count = conn.execute('SELECT COUNT(*) FROM trains').fetchone()[0]
        
        print(f"Database initialized with:")
        print(f"  - {stations_count} stations")
        print(f"  - {fares_count} fare entries")
        print(f"  - {trains_count} trains")
    
    else:
        print("Database already contains data, skipping CSV load.")

def load_csv_file(file_path, table_name, conn):
    """Helper function to load CSV file into database table"""
    if not os.path.exists(file_path):
        print(f"Warning: CSV file {file_path} not found. Using sample data instead.")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if table_name == 'stations':
                for row in reader:
                    conn.execute(
                        'INSERT INTO stations (station_id, name, latitude, longitude) VALUES (?, ?, ?, ?)',
                        (row['station_id'], row['name'], float(row['latitude']), float(row['longitude']))
                    )
            
            elif table_name == 'fares':
                for row in reader:
                    conn.execute(
                        'INSERT INTO fares (origin_id, destination_id, price) VALUES (?, ?, ?)',
                        (row['origin_id'], row['destination_id'], float(row['price']))
                    )
        
        print(f"Successfully loaded {file_path} into {table_name} table.")
        return True
        
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return False

def get_all_stations():
    """Get all stations from the database"""
    with get_db() as conn:
        stations = conn.execute('SELECT * FROM stations ORDER BY station_id').fetchall()
        return [dict(station) for station in stations]

def get_fare(origin_id, destination_id):
    """Get fare between two stations"""
    with get_db() as conn:
        fare = conn.execute(
            'SELECT price FROM fares WHERE origin_id = ? AND destination_id = ?',
            (origin_id, destination_id)
        ).fetchone()
        
        if fare:
            return fare['price']
        return None

def get_all_trains():
    """Get all current train positions"""
    with get_db() as conn:
        trains = conn.execute('''
            SELECT t.train_id, t.current_station_id, t.latitude, t.longitude, 
                   s.name as station_name, t.last_updated
            FROM trains t
            LEFT JOIN stations s ON t.current_station_id = s.station_id
            ORDER BY t.train_id
        ''').fetchall()
        return [dict(train) for train in trains]

def update_train_position(train_id, station_id, latitude, longitude):
    """Update a train's position in the database"""
    with get_db() as conn:
        conn.execute('''
            UPDATE trains 
            SET current_station_id = ?, latitude = ?, longitude = ?, last_updated = CURRENT_TIMESTAMP
            WHERE train_id = ?
        ''', (station_id, latitude, longitude, train_id))
        conn.commit()

"""
Simple Database Module - Fallback version for testing
"""

import sqlite3
import csv
import os
from contextlib import contextmanager

DATABASE_PATH = 'metro_tracking_simple.db'

@contextmanager
def get_db():
    """Simple database connection context manager"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_db_connection():
    """Get a simple database connection"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Simple database initialization"""
    print("Initializing Simple Database...")
    
    with get_db() as conn:
        # Create basic tables
        print("Creating stations table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                station_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        ''')
        
        print("Creating fares table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS fares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_id INTEGER,
                destination_id INTEGER,
                price REAL NOT NULL,
                FOREIGN KEY (origin_id) REFERENCES stations (station_id),
                FOREIGN KEY (destination_id) REFERENCES stations (station_id)
            )
        ''')
        
        print("Creating trains table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trains (
                train_id INTEGER PRIMARY KEY,
                current_station_id INTEGER,
                latitude REAL,
                longitude REAL,
                FOREIGN KEY (current_station_id) REFERENCES stations (station_id)
            )
        ''')
        
        conn.commit()
        print("Simple database tables created!")
        
        # Load basic data
        print("Loading basic data...")
        load_basic_data(conn)

def load_basic_data(conn):
    """Load basic station and fare data"""
    # Check if data exists
    stations_count = conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0]
    
    if stations_count == 0:
        print("Loading station data...")
        basic_stations = [
            (1, 'KL Sentral', 3.1348, 101.6868),
            (2, 'Masjid Jamek', 3.1488, 101.6942),
            (3, 'KLCC', 3.1578, 101.7122),
            (4, 'Ampang Park', 3.1592, 101.7167),
            (5, 'Damai', 3.1735, 101.7258),
            (10, 'Ampang', 3.1486, 101.7617),
        ]
        
        conn.executemany('''
            INSERT INTO stations (station_id, name, latitude, longitude)
            VALUES (?, ?, ?, ?)
        ''', basic_stations)
        
        print("Loading fare data...")
        basic_fares = [
            (1, 2, 2.50), (2, 3, 2.80), (3, 4, 1.50),
            (4, 5, 1.80), (5, 10, 2.10),
        ]
        
        conn.executemany('''
            INSERT INTO fares (origin_id, destination_id, price)
            VALUES (?, ?, ?)
        ''', basic_fares)
        
        print("Loading train data...")
        basic_trains = [
            (1, 1, 3.1348, 101.6868),
            (2, 3, 3.1578, 101.7122),
            (3, 10, 3.1486, 101.7617),
        ]
        
        conn.executemany('''
            INSERT INTO trains (train_id, current_station_id, latitude, longitude)
            VALUES (?, ?, ?, ?)
        ''', basic_trains)
        
        conn.commit()
        print("Basic data loaded successfully!")
    else:
        print("Database already contains data.")

# Query functions
def get_stations():
    """Get all stations"""
    with get_db() as conn:
        return conn.execute('SELECT * FROM stations ORDER BY station_id').fetchall()

def get_trains():
    """Get all trains"""
    with get_db() as conn:
        return conn.execute('SELECT * FROM trains').fetchall()

def get_fares():
    """Get all fares"""
    with get_db() as conn:
        return conn.execute('SELECT * FROM fares').fetchall()

if __name__ == '__main__':
    init_db()
    print("Simple database setup complete!")

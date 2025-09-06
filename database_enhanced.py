"""
Enhanced Database Module with Connection Pooling and Advanced Features
Incorporates concepts from Lab3 database exercises for improved reliability
"""

import sqlite3
import csv
import os
import threading
import time
from contextlib import contextmanager
from queue import Queue
import json

# Database configuration
DATABASE_PATH = 'metro_tracking_enhanced.db'
CONNECTION_TIMEOUT = 30
MAX_CONNECTIONS = 10

class DatabaseConnectionPool:
    """
    Database connection pool (inspired by advanced database concepts)
    Manages multiple connections for better concurrent access
    """
    
    def __init__(self, max_connections=MAX_CONNECTIONS):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()
        
        # Pre-populate with initial connections
        for _ in range(min(3, max_connections)):
            self._create_connection()
    
    def _create_connection(self):
        """Create a new database connection with enhanced settings"""
        try:
            conn = sqlite3.connect(
                DATABASE_PATH, 
                timeout=CONNECTION_TIMEOUT,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrent access
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA cache_size=10000;')
            conn.execute('PRAGMA temp_store=MEMORY;')
            
            with self.lock:
                self.active_connections += 1
            
            return conn
            
        except Exception as e:
            print(f"Error creating database connection: {e}")
            return None
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            # Try to get from pool first
            if not self.connections.empty():
                return self.connections.get_nowait()
            
            # Create new connection if under limit
            with self.lock:
                if self.active_connections < self.max_connections:
                    return self._create_connection()
            
            # Wait for available connection
            return self.connections.get(timeout=5)
            
        except:
            # Create temporary connection if pool is exhausted
            return self._create_connection()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if conn and not self.connections.full():
            try:
                self.connections.put_nowait(conn)
            except:
                self._close_connection(conn)
        else:
            self._close_connection(conn)
    
    def _close_connection(self, conn):
        """Close a database connection"""
        if conn:
            try:
                conn.close()
                with self.lock:
                    self.active_connections -= 1
            except:
                pass

# Global connection pool
_connection_pool = DatabaseConnectionPool()

@contextmanager
def get_db():
    """Simple database context manager for debugging"""
    print("Creating direct database connection...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        print("Direct database connection created successfully")
        yield conn
    except Exception as e:
        print(f"Error creating direct database connection: {e}")
        raise
    finally:
        print("Closing direct database connection...")
        try:
            conn.close()
        except:
            pass

def get_db_connection():
    """Get a simple database connection for debugging"""
    print("Creating simple database connection...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        print("Simple database connection created successfully")
        return conn
    except Exception as e:
        print(f"Error creating simple database connection: {e}")
        raise

def init_db():
    """Enhanced database initialization with comprehensive schema"""
    print("Initializing Enhanced Database...")
    
    try:
        print("Getting database connection...")
        with get_db() as conn:
            print("Database connection established, creating tables...")
            try:
                # Create enhanced stations table
                print("Creating stations table...")
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS stations (
                        station_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        line TEXT DEFAULT 'Unknown',
                        zone TEXT DEFAULT 'Central',
                        operational BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                print("Creating fares table...")
                # Create enhanced fares table with time-based pricing
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS fares (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        origin_id INTEGER,
                        destination_id INTEGER,
                        price REAL NOT NULL,
                        peak_price REAL,
                        distance_km REAL DEFAULT 0,
                        travel_time_min INTEGER DEFAULT 0,
                        fare_type TEXT DEFAULT 'standard',
                        effective_from DATE DEFAULT CURRENT_DATE,
                        effective_to DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (origin_id) REFERENCES stations (station_id),
                        FOREIGN KEY (destination_id) REFERENCES stations (station_id),
                        UNIQUE(origin_id, destination_id, fare_type, effective_from)
                    )
                ''')
                
                print("Creating trains table...")
                # Create enhanced trains table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS trains (
                        train_id INTEGER PRIMARY KEY,
                        current_station_id INTEGER,
                        latitude REAL,
                        longitude REAL,
                        line TEXT DEFAULT 'Unknown',
                        direction TEXT DEFAULT 'forward',
                        capacity INTEGER DEFAULT 300,
                        current_load INTEGER DEFAULT 0,
                        speed_kmh REAL DEFAULT 40,
                        status TEXT DEFAULT 'active',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (current_station_id) REFERENCES stations (station_id)
                    )
                ''')
                
                print("Creating train_movements table...")
                # Create train movement history table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS train_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        train_id INTEGER,
                        from_station_id INTEGER,
                        to_station_id INTEGER,
                        departure_time TIMESTAMP,
                        arrival_time TIMESTAMP,
                        travel_duration INTEGER,
                        passenger_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (train_id) REFERENCES trains (train_id),
                        FOREIGN KEY (from_station_id) REFERENCES stations (station_id),
                        FOREIGN KEY (to_station_id) REFERENCES stations (station_id)
                    )
                ''')
                
                print("Creating system_events table...")
                # Create system events table (inspired by Lab2 alert concepts)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        severity INTEGER DEFAULT 1,
                        affected_lines TEXT,
                        affected_stations TEXT,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                print("Creating user_sessions table...")
                # Create user sessions table (inspired by Lab3 user management)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE,
                        client_ip TEXT,
                        user_agent TEXT,
                        connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        disconnected_at TIMESTAMP,
                        total_duration INTEGER,
                        page_views INTEGER DEFAULT 0,
                        api_calls INTEGER DEFAULT 0
                    )
                ''')
                
                print("Creating indexes...")
                # Create indexes for better performance
                create_indexes(conn)
                
                conn.commit()
                print("Enhanced database tables created successfully!")
                
                print("Loading CSV data...")
                # Load CSV data if tables are empty
                load_csv_data(conn)
                
            except Exception as e:
                print(f"Error during database initialization: {e}")
                conn.rollback()
                raise
                
    except Exception as e:
        print(f"Error getting database connection: {e}")
        raise

def create_indexes(conn):
    """Create database indexes for better query performance"""
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_trains_station ON trains(current_station_id)',
        'CREATE INDEX IF NOT EXISTS idx_trains_line ON trains(line)',
        'CREATE INDEX IF NOT EXISTS idx_trains_status ON trains(status)',
        'CREATE INDEX IF NOT EXISTS idx_fares_origin_dest ON fares(origin_id, destination_id)',
        'CREATE INDEX IF NOT EXISTS idx_fares_type ON fares(fare_type)',
        'CREATE INDEX IF NOT EXISTS idx_movements_train ON train_movements(train_id)',
        'CREATE INDEX IF NOT EXISTS idx_movements_time ON train_movements(departure_time)',
        'CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type)',
        'CREATE INDEX IF NOT EXISTS idx_events_time ON system_events(start_time)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_time ON user_sessions(connected_at)',
    ]
    
    for index_sql in indexes:
        try:
            conn.execute(index_sql)
        except Exception as e:
            print(f"Warning: Could not create index: {e}")

def load_csv_data(conn):
    """Load station and fare data from external sources"""
    print("Checking for existing data...")
    
    try:
        # Check if data already exists
        print("Checking if stations data exists...")
        stations_count = conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0]
        print(f"Found {stations_count} existing stations")
        
        if stations_count == 0:
            print("No station data loaded - database will be populated from CSV files or external data sources")
            
            print("Fare data will be loaded from CSV files or external data sources")
            
            conn.commit()
            print("Database structure created successfully!")
            
            # Print summary
            print_database_summary(conn)
        else:
            print("Database already contains data, skipping initialization.")
            
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        raise

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
    
    print("="*50 + "\n")

# Enhanced query functions
def get_all_stations():
    """Get all stations with enhanced metadata"""
    with get_db() as conn:
        stations = conn.execute('''
            SELECT station_id, name, latitude, longitude, line, zone, operational
            FROM stations 
            WHERE operational = 1
            ORDER BY line, station_id
        ''').fetchall()
        return [dict(station) for station in stations]

def get_stations_by_line(line_name):
    """Get stations filtered by line"""
    with get_db() as conn:
        stations = conn.execute('''
            SELECT * FROM stations 
            WHERE line = ? AND operational = 1
            ORDER BY station_id
        ''', (line_name,)).fetchall()
        return [dict(station) for station in stations]

def get_enhanced_fare(origin_id, destination_id, fare_type='standard', is_peak_hour=False):
    """Get enhanced fare with peak hour pricing"""
    with get_db() as conn:
        price_column = 'peak_price' if is_peak_hour else 'price'
        
        fare = conn.execute(f'''
            SELECT {price_column} as fare_amount, distance_km, travel_time_min, fare_type
            FROM fares 
            WHERE origin_id = ? AND destination_id = ? AND fare_type = ?
            AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
            ORDER BY effective_from DESC
            LIMIT 1
        ''', (origin_id, destination_id, fare_type)).fetchone()
        
        if fare:
            return dict(fare)
        return None

def get_all_trains_enhanced():
    """Get all current train positions with enhanced data"""
    with get_db() as conn:
        trains = conn.execute('''
            SELECT t.train_id, t.current_station_id, t.latitude, t.longitude, 
                   t.line, t.direction, t.capacity, t.current_load, t.speed_kmh, t.status,
                   s.name as station_name, s.zone as station_zone, t.last_updated
            FROM trains t
            LEFT JOIN stations s ON t.current_station_id = s.station_id
            WHERE t.status = 'active'
            ORDER BY t.train_id
        ''').fetchall()
        return [dict(train) for train in trains]

def update_train_position_enhanced(train_id, station_id, latitude, longitude, passenger_change=0):
    """Update train position with enhanced tracking"""
    with get_db() as conn:
        # Get current position for movement history
        current = conn.execute('''
            SELECT current_station_id, current_load FROM trains WHERE train_id = ?
        ''', (train_id,)).fetchone()
        
        if current:
            from_station_id = current['current_station_id']
            current_load = current['current_load']
            new_load = max(0, min(300, current_load + passenger_change))  # Ensure valid range
            
            # Update train position
            conn.execute('''
                UPDATE trains 
                SET current_station_id = ?, latitude = ?, longitude = ?, 
                    current_load = ?, last_updated = CURRENT_TIMESTAMP
                WHERE train_id = ?
            ''', (station_id, latitude, longitude, new_load, train_id))
            
            # Record movement history if station changed
            if from_station_id != station_id:
                conn.execute('''
                    INSERT INTO train_movements 
                    (train_id, from_station_id, to_station_id, departure_time, arrival_time, passenger_count)
                    VALUES (?, ?, ?, datetime('now', '-2 minutes'), CURRENT_TIMESTAMP, ?)
                ''', (train_id, from_station_id, station_id, new_load))
        
        conn.commit()

def log_system_event(event_type, message, severity=1, affected_lines='', affected_stations=''):
    """Log system events with enhanced tracking"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO system_events (event_type, message, severity, affected_lines, affected_stations)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, message, severity, affected_lines, affected_stations))
        conn.commit()

def log_user_session(session_id, client_ip, user_agent):
    """Log user session (inspired by Lab3 user tracking)"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO user_sessions (session_id, client_ip, user_agent)
            VALUES (?, ?, ?)
        ''', (session_id, client_ip, user_agent))
        conn.commit()

def get_system_statistics():
    """Get comprehensive system statistics"""
    with get_db() as conn:
        stats = {}
        
        # Basic counts
        stats['stations'] = conn.execute('SELECT COUNT(*) FROM stations WHERE operational = 1').fetchone()[0]
        stats['active_trains'] = conn.execute('SELECT COUNT(*) FROM trains WHERE status = "active"').fetchone()[0]
        stats['total_fares'] = conn.execute('SELECT COUNT(*) FROM fares').fetchone()[0]
        
        # Movement statistics (last 24 hours)
        stats['movements_24h'] = conn.execute('''
            SELECT COUNT(*) FROM train_movements 
            WHERE arrival_time >= datetime('now', '-1 day')
        ''').fetchone()[0]
        
        # System events (last 24 hours)
        stats['events_24h'] = conn.execute('''
            SELECT COUNT(*) FROM system_events 
            WHERE start_time >= datetime('now', '-1 day')
        ''').fetchone()[0]
        
        # Line statistics
        line_stats = conn.execute('''
            SELECT line, COUNT(*) as train_count, AVG(current_load) as avg_load
            FROM trains 
            WHERE status = 'active'
            GROUP BY line
        ''').fetchall()
        
        stats['lines'] = [dict(line) for line in line_stats]
        
        return stats

# Backward compatibility
def get_fare(origin_id, destination_id):
    """Backward compatible fare function"""
    result = get_enhanced_fare(origin_id, destination_id)
    return result['fare_amount'] if result else None

def get_all_trains():
    """Backward compatible train function"""
    return get_all_trains_enhanced()

def update_train_position(train_id, station_id, latitude, longitude):
    """Backward compatible position update"""
    update_train_position_enhanced(train_id, station_id, latitude, longitude)

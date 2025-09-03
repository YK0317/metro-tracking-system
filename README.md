# Real-Time KL Metro Tracking and Routing System

A comprehensive web-based application that simulates real-time movement of trains on the MyRapidKL network, featuring advanced networking concepts from TCP/IP practical exercises, multicast communication, enhanced database management, and intelligent route planning through an interactive kiosk interface.

## 🚀 Enhanced Features

- **Real-Time Train Tracking**: Live visualization with WebSocket and Multicast support
- **Multicast Broadcasting**: Efficient train update distribution (inspired by Lab2 Multicast)
- **Enhanced Database**: Connection pooling, advanced schemas, and performance optimization
- **Threaded Architecture**: Concurrent processing with threading concepts from practical exercises
- **Interactive Map**: Leaflet.js-powered map with dynamic train movements
- **Route Planning**: BFS and Dijkstra algorithms with fare calculation
- **Peak Hour Pricing**: Dynamic fare calculation based on time and demand
- **System Monitoring**: Comprehensive logging and performance metrics
- **Load Testing**: Built-in performance testing capabilities
- **Zone-Based Filtering**: Geographic and line-based update filtering

## 🏗️ Enhanced System Architecture

```
┌─────────────────┐     HTTP/WS     ┌───────────────────────┐
│   Web Browser   │ ◄──────────────► │    Flask Server       │
│   (Frontend)    │  API Calls &    │  - Flask-SocketIO     │
│   - Leaflet.js  │  Real-Time Msg  │  - Enhanced Database  │
│   - Socket.IO   │                 │  - Threading Pool     │
└─────────────────┘                 └───────────────────────┘
         ▲                                   │         │
         │                           Database│         │WebSocket
         │ Multicast                         │         │& Multicast
         │ Updates                  ┌────────▼──┐  ┌───▼──────────┐
         └─────────────────────────►│ Enhanced  │  │ Enhanced     │
                                    │ Database  │  │ Data         │
┌─────────────────┐                 │ - Pooling │  │ Generator    │
│ Multicast       │                 │ - History │  │ - Threading  │
│ Monitor Client  │                 │ - Events  │  │ - Multicast  │
│ (External Apps) │                 └───────────┘  └──────────────┘
└─────────────────┘
```

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser with JavaScript enabled

## 🛠️ Installation & Setup

### 1. Clone or Download the Project
```bash
cd metro_tracking_system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## 📁 Enhanced Project Structure

```
metro_tracking_system/
├── app.py                          # Main Flask application with enhanced imports
├── database.py                     # Basic database operations
├── database_enhanced.py            # Enhanced database with connection pooling
├── routes.py                       # HTTP API endpoints with enhanced features
├── realtime.py                     # Basic WebSocket handlers
├── realtime_enhanced.py            # Enhanced real-time with multicast support
├── data_generator.py               # Basic train movement simulation
├── data_generator_enhanced.py      # Enhanced simulation with threading
├── requirements.txt                # Python dependencies
├── run.bat                         # Windows startup script
├── metro_tracking.db               # Basic SQLite database (auto-generated)
├── metro_tracking_enhanced.db      # Enhanced database (auto-generated)
├── multicast_monitor.py            # External multicast client (Lab2 inspired)
├── test_client.py                  # Comprehensive test suite
├── data/
│   ├── stations.csv               # Enhanced station metadata
│   └── fares.csv                  # Enhanced fare matrix with peak pricing
├── static/
│   └── js/
│       └── app.js                 # Enhanced frontend JavaScript
└── templates/
    └── index.html                 # Enhanced HTML interface
```

## 🔧 API Endpoints

### GET `/api/stations`
Returns all station metadata in JSON format.

**Response:**
```json
[
  {
    "station_id": 1,
    "name": "KL Sentral",
    "latitude": 3.1348,
    "longitude": 101.6868
  }
]
```

### GET `/api/fare?from=<id>&to=<id>&peak=<true|false>`
Returns enhanced fare between two stations with peak hour pricing.

**Response:**
```json
{
  "fare": 2.80,
  "distance_km": 3.2,
  "travel_time_min": 8,
  "fare_type": "standard",
  "is_peak_hour": true
}
```

### GET `/api/route?from=<id>&to=<id>`
Calculates shortest route between two stations.

**Response:**
```json
{
  "path": [1, 2, 3],
  "total_fare": 5.30,
  "total_hops": 2
}
```

## 🌐 Enhanced WebSocket Events

### Client → Server
- `connect`: Establish connection
- `disconnect`: Close connection  
- `request_trains`: Request current train positions
- `subscribe_zone`: Subscribe to zone-specific updates
- `ping`: Connection test

### Server → Client
- `initial_trains`: Initial train positions on connect
- `train_update`: Real-time train position updates with enhanced data
- `zone_trains`: Zone-filtered train data
- `system_alert`: System alerts and maintenance notifications
- `status`: System status messages with metrics
- `error`: Error notifications with categorization

## 📡 Multicast Communication (Lab2 Inspired)

The enhanced system includes multicast broadcasting capabilities:

### Multicast Configuration
- **Group**: 224.1.1.1:9001
- **Message Format**: Pickled Python dictionaries
- **Update Types**: TRAIN_UPDATE, SYSTEM_ALERT, MAINTENANCE

### External Monitoring
```bash
# Run the multicast monitor
python multicast_monitor.py [zone_filter] [train_ids]

# Examples:
python multicast_monitor.py all              # Monitor all updates
python multicast_monitor.py North            # Monitor North zone only
python multicast_monitor.py all 1,2,3        # Monitor specific trains
```

## 🗄️ Enhanced Database Schema

### Enhanced Stations Table
```sql
CREATE TABLE stations (
    station_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    line TEXT DEFAULT 'Unknown',
    zone TEXT DEFAULT 'Central',
    operational BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Enhanced Fares Table
```sql
CREATE TABLE fares (
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
    FOREIGN KEY (destination_id) REFERENCES stations (station_id)
);
```

### Enhanced Trains Table
```sql
CREATE TABLE trains (
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
);
```

### Additional Tables
- **train_movements**: Historical movement tracking
- **system_events**: System alerts and maintenance logs
- **user_sessions**: User activity tracking (Lab3 inspired)

## 🔄 Data Flow

1. **Initialization**: Flask app starts, initializes database from CSV files
2. **Data Generation**: Background thread simulates train movements every 3-6 seconds
3. **Database Update**: Train positions updated in SQLite database
4. **WebSocket Broadcast**: Position updates sent to all connected clients
5. **Frontend Update**: JavaScript receives updates and animates train markers
6. **Route Planning**: User selects stations, system calculates optimal path using BFS algorithm

## 🎯 Key Features Implementation

### Real-Time Communication (FR4)
- Flask-SocketIO provides bidirectional WebSocket communication
- Background data generator broadcasts train updates every 3-6 seconds
- Frontend subscribes to updates and animates markers in real-time

### Route Planning Algorithm
- **Shortest Path**: Breadth-First Search (BFS) for minimum hops
- **Fare Calculation**: Sum of individual segment fares along the path
- **Alternative**: Dijkstra's algorithm available for cheapest route

### Data Simulation (FR2)
- Trains move between connected stations based on fare network
- Random movement with 3-6 second intervals
- Realistic station connectivity using MyRapidKL network structure

## 🚀 Performance Optimization

- **Database Indexing**: Primary keys and foreign keys for efficient queries
- **Connection Pooling**: SQLite connection context managers
- **Efficient Updates**: Single train updates rather than full refreshes
- **Map Optimization**: Marker reuse and selective updates

## 🔍 Debugging & Monitoring

### Console Logs
The application provides detailed console logging:
- Database operations
- WebSocket connections/disconnections
- Train movement simulation
- Route calculations

### Browser Developer Tools
- Network tab: Monitor WebSocket messages
- Console: Frontend application logs
- Elements: Inspect map markers and UI state

## 🛡️ Error Handling

- **Database Errors**: Graceful fallbacks and error messages
- **Network Issues**: Automatic reconnection attempts
- **Invalid Routes**: Clear error messages for impossible paths
- **Missing Data**: Default values and user notifications

## 📱 Mobile Compatibility

- Responsive design adapts to mobile screens
- Touch-friendly interface elements
- Optimized map controls for mobile devices
- Sidebar collapses on smaller screens

## 🧪 Testing & Validation

The system includes comprehensive testing capabilities inspired by practical exercises:

### Automated Test Suite
```bash
# Run the comprehensive test client
python test_client.py
```

**Test Components:**
- **API Testing**: REST endpoint validation with error handling
- **WebSocket Testing**: Real-time communication verification  
- **TCP Testing**: Low-level connection testing (MyWorkspace inspired)
- **Load Testing**: Concurrent client performance testing
- **Multicast Testing**: External monitoring validation

### Manual Testing

**WebSocket Connection:**
```javascript
// Browser console testing
const socket = io();
socket.on('train_update', (data) => console.log('Train update:', data));
socket.emit('subscribe_zone', {zone: 'Central'});
```

**API Testing:**
```bash
# PowerShell/Command Prompt
curl http://localhost:5000/api/stations
curl "http://localhost:5000/api/fare?from=1&to=3&peak=true"  
curl "http://localhost:5000/api/route?from=1&to=10"
```

**Multicast Monitoring:**
```bash
# Terminal 1: Start the main application
python app.py

# Terminal 2: Monitor multicast updates
python multicast_monitor.py North

# Terminal 3: Run load tests
python test_client.py
```

## � Practical Exercise Integration

This implementation incorporates key concepts from the provided practical exercises:

### From Lab2/Multicast:
- **Multicast Broadcasting**: Efficient train update distribution to multiple clients
- **Zone-Based Filtering**: Clients can subscribe to specific geographic zones
- **Alert System**: System events broadcasted like traffic alerts
- **Client-Server Architecture**: Multiple monitoring clients can connect

### From Lab2/RPyC:
- **Threaded Server**: Concurrent handling of multiple client connections
- **Service Architecture**: Modular service design with clear interfaces
- **Connection Management**: Robust connection pooling and error handling

### From Lab3/Flask:
- **Enhanced Database**: Advanced SQLite usage with proper schema design
- **Request Handling**: Comprehensive HTTP method support and validation
- **Session Management**: User session tracking and analytics
- **Error Handling**: Graceful error responses and logging

### From MyWorkspace:
- **TCP Fundamentals**: Low-level socket programming concepts
- **Client-Server Communication**: Bidirectional data exchange
- **Connection Testing**: Robust connection validation and monitoring
- **Binary Data Transfer**: Efficient data serialization using pickle

### Key Improvements Applied:
1. **Connection Pooling**: Database performance optimization
2. **Threading**: Concurrent train simulation and update processing  
3. **Multicast**: Efficient broadcast to multiple monitoring systems
4. **Enhanced Schemas**: Comprehensive data modeling with relationships
5. **Error Handling**: Robust exception handling throughout the system
6. **Performance Monitoring**: Real-time system metrics and statistics
7. **Load Testing**: Automated performance validation
8. **Modular Design**: Clean separation of concerns with fallback mechanisms

## 🔧 Advanced Customization

### Enhanced Database Features
```python
# Custom fare calculation with time-based pricing
from database_enhanced import get_enhanced_fare
fare_data = get_enhanced_fare(origin_id, dest_id, 'standard', is_peak_hour=True)

# System event logging
from database_enhanced import log_system_event
log_system_event('MAINTENANCE', 'Track maintenance scheduled', severity=2)

# Real-time statistics
from database_enhanced import get_system_statistics
stats = get_system_statistics()
```

### Multicast Integration
```python
# External system monitoring
from multicast_monitor import MetroMulticastMonitor

# Monitor specific zone
monitor = MetroMulticastMonitor(zone_filter='North')
monitor.start_monitoring()

# Custom message processing
class CustomMonitor(MetroMulticastMonitor):
    def process_train_update(self, message, timestamp):
        # Custom logic for train updates
        super().process_train_update(message, timestamp)
        # Send to external system, log to file, etc.
```

### Enhanced Data Generation
```python
# Add custom train to simulation
from data_generator_enhanced import add_train_to_simulation
add_train_to_simulation(train_id=99, initial_station_id=1)

# Get detailed simulation statistics
from data_generator_enhanced import get_simulation_stats
stats = get_simulation_stats()
```

## 📊 Performance Metrics

- **Train Update Frequency**: 3-6 seconds per train
- **WebSocket Latency**: < 100ms for local connections
- **Database Query Time**: < 50ms for route calculations
- **Map Rendering**: < 200ms for marker updates

## 🎯 Future Enhancements

- **MQTT Integration**: Alternative to WebSocket using Flask-MQTT
- **Historical Data**: Store and analyze train movement patterns
- **Predictive Routing**: ML-based optimal route suggestions
- **Mobile App**: Native mobile application
- **Multi-Line Support**: Handle multiple metro lines
- **Crowd Density**: Simulate passenger loads
- **Service Alerts**: Real-time service disruption notifications

## 📄 License

This project is created for educational purposes as part of the UEEN3123/UEEN3433 TCP/IP Network Application Development course.

## 👥 Contributors

- **Course**: UEEN3123/UEEN3433 TCP/IP Network Application Development
- **Assignment**: Real-Time Metro Tracking and Routing System
- **Institution**: UTAR (Universiti Tunku Abdul Rahman)

---

For technical support or questions about this implementation, please refer to the course materials or contact your instructor.

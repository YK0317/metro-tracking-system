# Real-Time KL Metro Tracking and Routing System

A comprehensive web-based application that simulates real-time movement of trains on the Kuala Lumpur metro network, featuring realistic train movement patterns, live tracking, route planning, and interactive visualization. Built for the UEEN3123/UEEN3433 TCP/IP Network Application Development course.

## 🚀 Key Features

- **Real-Time Train Tracking**: Live visualization of 4 trains across 2 metro lines with WebSocket communication
- **Realistic Train Movement**: Sequential movement along actual metro line routes with proper terminal reversals
- **Interactive Route Planning**: Find shortest path between any two stations with fare calculation
- **Multicast Broadcasting**: UDP multicast support for external monitoring systems
- **Interactive Map**: Leaflet.js-power## 🛠️ Troubleshooting

### Component Interaction Matrix

| Component | Inputs | Outputs | Dependencies | Purpose |
|-----------|--------|---------|--------------|---------|
| **Flask App (app.py)** | HTTP requests, WebSocket connections | HTML pages, API responses | Flask, Flask-SocketIO | Main application server |
| **Route Planning (routes.py)** | Origin/destination stations | Shortest path, total fare | Database, Graph algorithms | Path calculation service |
| **Real-time Service (realtime
.py)** | Train position updates | WebSocket broadcasts, UDP multicast | Socket.IO, Threading | Live communication hub |
| **Train Simulation (data_generator.py)** | Timer events, station data | Train position updates | TrainMovement, Database | Movement coordination |
| **Train Movement (train_movement.py)** | Current position, line data | Next station, updated position | Database, Line sequences | Core movement logic |
| **Database (database.py)** | CSV data, position updates | Station data, fare info | SQLite, Pandas | Data persistence layer |
| **Frontend (app.js)** | WebSocket events, user clicks | Map updates, API requests | Leaflet.js, Socket.IO | User interface |
| **Multicast Monitor (multicast_monitor.py)** | UDP multicast messages | Console logs, analytics | UDP sockets | External monitoring |

## 📋 Requirements

- **Python**: 3.8 or higher
- **pip**: Python package installer
- **Dependencies**: Listed in requirements.txt
  - Flask 2.3.3 (Web framework)
  - Flask-SocketIO 5.3.6 (WebSocket support)
  - pandas 1.5.0+ (CSV data processing)
  - eventlet 0.33.3 (Async server support)
- **Browser**: Modern web browser with JavaScript enabled
- **Storage**: ~50MB for database and CSV files
- **Network**: Port 5000 for web server, Port 9001 for multicast (optional)

## 🛠️ Installation & Setup

### Option 1: Automated Setup (Recommended)
```bash
# Navigate to project directory
cd metro-tracking-system

# Run automated setup script
python setup_system.py
```
The setup script will:
- Check Python version compatibility (3.8+)
- Install all required dependencies
- Initialize the database with CSV data
- Generate trains for all metro lines
- Verify system functionality

### Option 2: Manual Setup
```bash
# Navigate to project directory
cd metro-tracking-system

# Install dependencies
pip install -r requirements.txt

# Initialize database with station and fare data
python initialize_database.py

# Generate trains for metro lines
python add_trains_direct.py

# Run the application
python app.py
```


### 4. Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

### 5. System Verification
To verify the system is working correctly:
```bash
# Check if all trains are active
python generate_train_routes.py

# Monitor multicast updates (optional)
python -c "from realtime
 import *; print('Multicast system ready')"
```

## 📁 Project Structure

```
metro-tracking-system/
├── app.py                          # Main Flask application entry point
├── database.py            # Enhanced database operations with connection pooling
├── routes.py                       # API endpoints for stations, fares, and routing
├── realtime.py            # WebSocket and multicast communication handlers
├── data_generator.py               # Train simulation coordinator and background threading
├── train_movement.py               # Core train movement logic with line-based routing
├── route_planner.py       # Enhanced route planning using Route.csv data
├── setup_system.py                 # Automated system setup and initialization
├── initialize_database.py          # Database initialization from CSV files
├── generate_trains.py              # Train generation utility (2 trains per line)
├── add_trains_direct.py            # Add trains to running system from CSV
├── requirements.txt                # Python dependencies
├── metro_tracking_enhanced.db      # SQLite database (auto-generated)
├── README.md                       # Project documentation
├── SETUP.md                        # Setup instructions
├── data/
│   ├── Fare.csv                   # Station fare matrix (Kaggle dataset)
│   ├── Route.csv                  # Station connectivity data
│   ├── Time.csv                   # Travel time between stations
│   ├── Stations.csv               # Station information and coordinates
│   └── Trains.csv                 # Train configuration data
├── static/
│   └── js/
│       └── app.js                 # Frontend JavaScript with Leaflet.js map integration
└── templates/
    └── index.html                 # Main web interface with responsive design
```

## 🔧 API Endpoints

### GET `/api/stations`
Returns all station information including coordinates and line information.

**Response:**
```json
[
  {
    "station_id": 1,
    "name": "KL Sentral",
    "latitude": 3.1348,
    "longitude": 101.6868,
    "line": "LRT Kelana Jaya Line"
  }
]
```

### GET `/api/fare?from=<id>&to=<id>&peak=<boolean>`
Returns enhanced fare calculation between two stations with optional peak hour pricing.

**Parameters:**
- `from`: Origin station ID (required)
- `to`: Destination station ID (required)  
- `peak`: Peak hour pricing flag (optional, default: false)

**Response:**
```json
{
  "fare": 2.80,
  "origin": "KL Sentral",
  "destination": "Ampang Park",
  "distance_km": 5.2,
  "travel_time_min": 12,
  "is_peak": false
}
```

### GET `/api/route?from=<id>&to=<id>`
Calculates optimal route between stations using enhanced route planner with Route.csv data.

**Response:**
```json
{
  "path": [1, 2, 3],
  "total_fare": 5.30,
  "total_hops": 2,
  "total_distance_km": 8.7,
  "estimated_time_min": 18,
  "stations": ["KL Sentral", "Bangsar", "Kerinchi"],
  "transfers": [],
  "route_details": [
    {
      "from": "KL Sentral",
      "to": "Bangsar", 
      "line": "LRT Kelana Jaya Line",
      "fare": 2.50,
      "time_min": 8
    }
  ]
}
```

## 🌐 WebSocket Events

### Client → Server Events
- `connect`: Establish WebSocket connection
- `disconnect`: Close WebSocket connection
- `request_trains`: Request current train positions
- `request_status`: Request system status information

### Server → Client Events
- `initial_trains`: Initial train positions sent upon connection
- `train_update`: Real-time train position updates (every 3-6 seconds)
- `system_alert`: System notifications and alerts
- `status_update`: System status and performance metrics
- `connection_status`: Connection health information

### Example WebSocket Implementation
```javascript
// Connect to WebSocket
const socket = io();

// Listen for train updates
socket.on('train_update', (data) => {
    console.log('Train update received:', data);
    // data contains: train_id, station_id, latitude, longitude, line, direction
});

// Listen for initial train data
socket.on('initial_trains', (trains) => {
    console.log('Initial trains loaded:', trains.length);
    // Initialize map with train positions
});

// Request current train positions
socket.emit('request_trains');
```

## 📡 Multicast Communication

The system includes UDP multicast broadcasting for external monitoring and analytics:

### Multicast Configuration
- **Group Address**: 224.1.1.1
- **Port**: 9001
- **Protocol**: UDP with Python pickle serialization
- **Update Frequency**: Every 3-6 seconds per train movement
- **TTL**: 1 (local network only)

### Multicast Message Format
```python
# Message structure sent via multicast
{
    'type': 'train_update',
    'timestamp': '2025-09-09 10:30:15',
    'train_id': 1,
    'current_station_id': 15,
    'latitude': 3.1548,
    'longitude': 101.7147,
    'line': 'LRT Kelana Jaya Line',
    'direction': 'forward',
    'next_station': 'KLCC',
    'estimated_arrival': 180  # seconds
}
```

### External Monitoring Client
```python
# Example multicast monitor implementation
import socket
import struct
import pickle

def monitor_trains():
    # Create multicast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to multicast group
    sock.bind(('', 9001))
    mreq = struct.pack('4sl', socket.inet_aton('224.1.1.1'), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    print("Monitoring KL Metro multicast updates...")
    while True:
        data, addr = sock.recvfrom(1024)
        train_data = pickle.loads(data)
        print(f"Train {train_data['train_id']}: {train_data['current_station']}")

# Run monitor
monitor_trains()
```


## 🎯 Key Features Implementation

### Real-Time Communication
- **Flask-SocketIO**: Bidirectional WebSocket communication between server and clients
- **Background Simulation**: Continuous train movement simulation using threading
- **Update Broadcasting**: Real-time position updates sent to all connected browsers
- **UDP Multicast**: External monitoring capability for third-party applications

### Realistic Train Movement
- **Line-Based Movement**: Trains follow actual metro line sequences (no random movement)
- **Terminal Reversals**: Trains properly reverse direction only at line terminals
- **Sequential Stations**: Trains move station-by-station along predefined routes
- **2 Metro Lines**: LRT Kelana Jaya (37 stations) and MRT SBK (31 stations)

### Route Planning Algorithm
- **Shortest Path**: Breadth-First Search (BFS) for minimum number of hops
- **Fare Calculation**: Accurate fare computation using real Kaggle dataset
- **Interactive Selection**: Click-to-select stations on the interactive map
- **Path Visualization**: Route highlighted on map with total fare display

### Data Management
- **CSV Integration**: Authentic Malaysian metro data from Kaggle (Fare.csv, Route.csv, Time.csv)
- **SQLite Database**: Efficient local storage with proper foreign key relationships
- **Dynamic Loading**: CSV data automatically loaded into database on startup
- **Real-time Updates**: Live train position tracking and historical movement storage

## 🚀 Metro Lines & Stations

### LRT Kelana Jaya Line (KJL) - 37 stations
- **Route**: Gombak ↔ Putra Heights (KJL)
- **Trains**: 2 trains with realistic bidirectional movement (1 forward, 1 backward)
- **Key Stations**: KL Sentral (KJL), KLCC, Ampang Park, Wangsa Maju, Bangsar
- **Zones**: 3 zones (Zone 1: Gombak-Damai, Zone 2: Ampang Park-Taman Bahagia, Zone 3: Kelana Jaya-Putra Heights)

### MRT Sungai Buloh-Kajang Line (SBK) - 31 stations  
- **Route**: Sungai Buloh ↔ Kajang
- **Trains**: 2 trains with north-south bidirectional movement (1 forward, 1 backward)
- **Key Stations**: Semantan, Muzium Negara, Merdeka, Bukit Bintang, TRX, Maluri
- **Zones**: 3 zones (Zone 1: Sungai Buloh-Semantan, Zone 2: Muzium Negara-Batu 11 Cheras, Zone 3: Stadium Kajang-Kajang)

### System Overview
- **Total Stations**: 68 stations across 2 metro lines
- **Total Active Trains**: 4 trains (2 per line with bidirectional coverage)
- **Coverage Area**: Greater Kuala Lumpur metropolitan area
- **Real-time Simulation**: Sequential station-to-station movement with authentic travel times

## 🔍 Testing & Validation

### API Testing
```bash
# Test station data endpoint
curl http://localhost:5000/api/stations

# Test fare calculation with peak hour pricing
curl "http://localhost:5000/api/fare?from=1&to=10&peak=true"

# Test enhanced route planning
curl "http://localhost:5000/api/route?from=1&to=20"

# Test with invalid parameters
curl "http://localhost:5000/api/fare?from=invalid&to=10"
```

### WebSocket Testing
```javascript
// Browser console testing
const socket = io();

// Test train update reception
socket.on('train_update', (data) => {
    console.log('Train update:', data);
    console.log(`Train ${data.train_id} at station ${data.current_station_id}`);
});

// Test initial trains loading
socket.on('initial_trains', (data) => {
    console.log('Initial trains loaded:', data.length);
});

// Test connection status
socket.on('connect', () => console.log('Connected to WebSocket'));
socket.on('disconnect', () => console.log('Disconnected from WebSocket'));

// Request train positions
socket.emit('request_trains');
```

### Database Validation
```bash
# Check database integrity
python -c "from database import get_db_connection; conn = get_db_connection(); print('Stations:', len(conn.execute('SELECT * FROM stations').fetchall())); print('Trains:', len(conn.execute('SELECT * FROM trains').fetchall()))"

# Validate CSV data loading
python initialize_database.py

# Check train generation
python generate_trains.py
```

### System Monitoring
```bash
# Monitor multicast updates
python -c "
import socket, struct, pickle
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 9001))
mreq = struct.pack('4sl', socket.inet_aton('224.1.1.1'), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
print('Monitoring multicast...')
while True:
    data, addr = sock.recvfrom(1024)
    try:
        msg = pickle.loads(data)
        print(f'Train {msg.get(\"train_id\", \"?\")}: {msg.get(\"type\", \"update\")}')
    except: pass
"

# Generate train route analysis
python generate_train_routes.py

# System health check
python -c "
import requests
try:
    r = requests.get('http://localhost:5000/api/stations', timeout=5)
    print('API Status:', r.status_code, 'Stations:', len(r.json()) if r.status_code == 200 else 'Error')
except Exception as e:
    print('API Error:', e)
"
```

### Module Dependencies and Architecture

#### Core Runtime Modules (Essential for Application)
```
app.py (Main Entry Point)
├── database.py (Database Layer)
├── realtime.py (Communication Layer)
├── data_generator.py (Simulation Layer)
│   ├── train_movement.py (Movement Logic)
│   └── realtime.py (Broadcasting)
└── routes.py (API Layer)
    ├── database.py (Data Access)
    └── route_planner.py (Route Calculation)
```

#### Utility/Setup Modules (Development and Maintenance)
```
setup_system.py (Automated Setup)
├── initialize_database.py (Database Initialization)
├── generate_trains.py (Train Population)
└── System Verification

Administrative Tools:
├── add_trains_direct.py (Live Train Addition)
└── Database Management Scripts
```

#### Module Usage Analysis
| Module | Type | Used By | Purpose | Status |
|--------|------|---------|---------|--------|
| `app.py` | Entry Point | - | Flask application server | **ESSENTIAL** |
| `database.py` | Core | All modules | Database operations & connection pooling | **ESSENTIAL** |
| `realtime
.py` | Core | app.py, data_generator.py | WebSocket & multicast communication | **ESSENTIAL** |
| `data_generator.py` | Core | app.py | Train simulation coordinator | **ESSENTIAL** |
| `train_movement.py` | Core | data_generator.py, generate_train_routes.py | Train movement logic | **ESSENTIAL** |
| `routes.py` | Core | app.py | HTTP API endpoints | **ESSENTIAL** |
| `route_planner.py` | Core | routes.py | Enhanced route planning | **ESSENTIAL** |
| `setup_system.py` | Utility | - | Automated system setup | **SETUP ONLY** |
| `initialize_database.py` | Utility | setup_system.py | Database initialization | **SETUP ONLY** |
| `generate_trains.py` | Utility | setup_system.py | Train data population | **SETUP ONLY** |
| `add_trains_direct.py` | Utility | - | Administrative tool | **ADMIN TOOL** |



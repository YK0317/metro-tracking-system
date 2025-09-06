# Real-Time KL Metro Tracking and Routing System

A comprehensive web-based application that simulates real-time movement of trains on the Kuala Lumpur metro network, featuring realistic train movement patterns, live tracking, route planning, and interactive visualization. Built for the UEEN3123/UEEN3433 TCP/IP Network Application Development course.

## 🚀 Key Features

- **Real-Time Train Tracking**: Live visualization of 8 trains across 3 metro lines with WebSocket communication
- **Realistic Train Movement**: Sequential movement along actual metro line routes with proper terminal reversals
- **Interactive Route Planning**: Find shortest path between any two stations with fare calculation
- **Multicast Broadcasting**: UDP multicast support for external monitoring systems
- **Interactive Map**: Leaflet.js-powered map with dynamic train movements and station markers
- **RESTful API**: Complete API endpoints for stations, fares, and route calculations
- **Multi-Line Support**: Supports LRT Kelana Jaya (37 stations), LRT Ampang (13 stations), and MRT SBK (18 stations)
- **Real Kaggle Dataset**: Uses authentic Malaysian metro data (Fare.csv, Route.csv, Time.csv)

## 🏗️ System Architecture

### High-Level Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                           KL Metro Tracking System Architecture                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  PRESENTATION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Web Browser   │    │   Mobile View   │    │ External Client │                     │
│  │  - Leaflet.js   │    │  - Responsive   │    │  - API Access   │                     │
│  │  - Socket.IO    │    │  - Touch UI     │    │  - Monitoring   │                     │
│  │  - Bootstrap    │    │  - Mobile Map   │    │  - Analytics    │                     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                     │
└──────────────┬──────────────────┬──────────────────┬───────────────────────────────────┘
               │                  │                  │
               │ HTTP/WebSocket   │ HTTP/WebSocket   │ HTTP API
               │                  │                  │
┌──────────────▼──────────────────▼──────────────────▼───────────────────────────────────┐
│                                 APPLICATION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Flask Web Server (app.py)                            │   │
│  │  - HTTP Request Routing                                                        │   │
│  │  - WebSocket Connection Management                                             │   │
│  │  - Static File Serving                                                        │   │
│  │  - Session Management                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                              │
│  ┌───────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Route Planning  │  │  Real-time      │  │  Train Movement │  │  API Endpoints  │  │
│  │   Service         │  │  Communication  │  │  Simulation     │  │  Service        │  │
│  │  (routes.py)      │  │ (realtime_      │  │ (data_generator │  │  (routes.py)    │  │
│  │                   │  │  enhanced.py)   │  │  .py + train_   │  │                 │  │
│  │ • BFS Algorithm   │  │                 │  │  movement.py)   │  │ • GET /api/     │  │
│  │ • Fare Calc       │  │ • WebSocket     │  │                 │  │   stations      │  │
│  │ • Path Finding    │  │   Broadcasting  │  │ • 8 Active      │  │ • GET /api/fare │  │
│  │ • Graph Building  │  │ • Client Mgmt   │  │   Trains        │  │ • GET /api/     │  │
│  │                   │  │ • UDP Multicast │  │ • 3 Metro Lines │  │   route         │  │
│  └───────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────────────────┐
│                                   DATA LAYER                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                      SQLite Database (database_enhanced.py)                     │   │
│  │                                                                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│  │  │  STATIONS   │  │   FARES     │  │   TRAINS    │  │   TRAIN_MOVEMENTS       │ │   │
│  │  │             │  │             │  │             │  │                         │ │   │
│  │  │ station_id  │  │ origin_id   │  │ train_id    │  │ movement_id             │ │   │
│  │  │ name        │  │ dest_id     │  │ current_    │  │ train_id                │ │   │
│  │  │ latitude    │  │ price       │  │ station_id  │  │ from_station_id         │ │   │
│  │  │ longitude   │  │ distance    │  │ latitude    │  │ to_station_id           │ │   │
│  │  │ line        │  │ travel_time │  │ longitude   │  │ departure_time          │ │   │
│  │  └─────────────┘  └─────────────┘  │ line        │  │ arrival_time            │ │   │
│  │                                    │ direction   │  │ timestamp               │ │   │
│  │                                    │ last_update │  └─────────────────────────┘ │   │
│  │                                    └─────────────┘                              │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                          ▲                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CSV Data Sources (Kaggle Dataset)                     │   │
│  │                                                                                 │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                      │   │
│  │  │   Fare.csv    │  │  Route.csv    │  │   Time.csv    │                      │   │
│  │  │               │  │               │  │               │                      │   │
│  │  │ • Station     │  │ • Origin      │  │ • Travel      │                      │   │
│  │  │   Fare Matrix │  │   Station     │  │   Times       │                      │   │
│  │  │ • Price Data  │  │ • Dest        │  │ • Line-based  │                      │   │
│  │  │ • Distance    │  │   Station     │  │   Timing      │                      │   │
│  │  │   Info        │  │ • Route Info  │  │ • Schedule    │                      │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘                      │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                COMMUNICATION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐           │
│  │   WebSocket     │         │  UDP Multicast  │         │   HTTP REST     │           │
│  │   (TCP-based)   │         │   Broadcasting  │         │      API        │           │
│  │                 │         │                 │         │                 │           │
│  │ • Real-time     │         │ • Group:        │         │ • GET Requests  │           │
│  │   Updates       │         │   224.1.1.1     │         │ • JSON Response │           │
│  │ • Bidirectional │         │ • Port: 9001    │         │ • RESTful       │           │
│  │ • Event-driven  │         │ • External      │         │ • Stateless     │           │
│  │ • Low Latency   │         │   Monitoring    │         │ • Cacheable     │           │
│  └─────────────────┘         └─────────────────┘         └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               EXTERNAL SYSTEMS                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Multicast       │    │ Third-party     │    │ Analytics &     │                     │
│  │ Monitor Client  │    │ Applications    │    │ Monitoring      │                     │
│  │                 │    │                 │    │ Tools           │                     │
│  │ • Real-time     │    │ • API           │    │ • Performance   │                     │
│  │   Monitoring    │    │   Integration   │    │   Metrics       │                     │
│  │ • System        │    │ • Data Export   │    │ • System Health │                     │
│  │   Analytics     │    │ • External      │    │ • Usage Stats   │                     │
│  │ • Alerting      │    │   Dashboards    │    │ • Reporting     │                     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAM                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION PHASE
   ┌─────────────┐    CSV Load    ┌──────────────┐    Table Creation    ┌─────────────┐
   │ Kaggle CSV  │ ──────────────► │ Data Parser  │ ───────────────────► │ SQLite DB   │
   │ Files       │                │ (Pandas)     │                     │ Schema      │
   └─────────────┘                └──────────────┘                     └─────────────┘

2. TRAIN SIMULATION PHASE
   ┌─────────────┐    Movement    ┌──────────────┐    Position Update   ┌─────────────┐
   │ Train       │ ──────────────► │ TrainMovement│ ───────────────────► │ Database    │
   │ Simulator   │                │ Algorithm    │                     │ Update      │
   └─────────────┘                └──────────────┘                     └─────────────┘
          │                              │                                     │
          │ 3-6 sec cycle               │ Sequential                          │
          │                              │ Movement                            │
          ▼                              ▼                                     ▼
   ┌─────────────┐                ┌──────────────┐                     ┌─────────────┐
   │ Background  │                │ Line-based   │                     │ Real-time   │
   │ Threading   │                │ Routing      │                     │ Storage     │
   └─────────────┘                └──────────────┘                     └─────────────┘

3. REAL-TIME BROADCASTING PHASE
   ┌─────────────┐    WebSocket   ┌──────────────┐    Map Update       ┌─────────────┐
   │ Database    │ ──────────────► │ Socket.IO    │ ───────────────────► │ Frontend    │
   │ Changes     │                │ Broadcasting │                     │ Animation   │
   └─────────────┘                └──────────────┘                     └─────────────┘
          │                              │                                     │
          │ Parallel                     │ Event-driven                       │
          │                              │                                     │
          ▼                              ▼                                     ▼
   ┌─────────────┐                ┌──────────────┐                     ┌─────────────┐
   │ UDP         │                │ Client       │                     │ Leaflet.js  │
   │ Multicast   │                │ Management   │                     │ Markers     │
   └─────────────┘                └──────────────┘                     └─────────────┘

4. USER INTERACTION PHASE
   ┌─────────────┐    Station     ┌──────────────┐    BFS Algorithm    ┌─────────────┐
   │ User Click  │ ──────────────► │ Route        │ ───────────────────► │ Path        │
   │ on Map      │                │ Planning     │                     │ Calculation │
   └─────────────┘                └──────────────┘                     └─────────────┘
          │                              │                                     │
          │ HTTP API                     │ Graph Theory                       │
          │                              │                                     │
          ▼                              ▼                                     ▼
   ┌─────────────┐                ┌──────────────┐                     ┌─────────────┐
   │ API         │                │ Fare         │                     │ Route       │
   │ Request     │                │ Calculation  │                     │ Response    │
   └─────────────┘                └──────────────┘                     └─────────────┘
```

### Component Interaction Matrix

| Component | Inputs | Outputs | Dependencies | Purpose |
|-----------|--------|---------|--------------|---------|
| **Flask App (app.py)** | HTTP requests, WebSocket connections | HTML pages, API responses | Flask, Flask-SocketIO | Main application server |
| **Route Planning (routes.py)** | Origin/destination stations | Shortest path, total fare | Database, Graph algorithms | Path calculation service |
| **Real-time Service (realtime_enhanced.py)** | Train position updates | WebSocket broadcasts, UDP multicast | Socket.IO, Threading | Live communication hub |
| **Train Simulation (data_generator.py)** | Timer events, station data | Train position updates | TrainMovement, Database | Movement coordination |
| **Train Movement (train_movement.py)** | Current position, line data | Next station, updated position | Database, Line sequences | Core movement logic |
| **Database (database_enhanced.py)** | CSV data, position updates | Station data, fare info | SQLite, Pandas | Data persistence layer |
| **Frontend (app.js)** | WebSocket events, user clicks | Map updates, API requests | Leaflet.js, Socket.IO | User interface |
| **Multicast Monitor (multicast_monitor.py)** | UDP multicast messages | Console logs, analytics | UDP sockets | External monitoring |

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser with JavaScript enabled

## 🛠️ Installation & Setup

### 1. Navigate to Project Directory
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

## 📁 Project Structure

```
metro_tracking_system/
├── app.py                          # Main Flask application entry point
├── database_enhanced.py            # Database operations and CSV data loading
├── routes.py                       # API endpoints for frontend integration
├── realtime_enhanced.py            # WebSocket handlers for real-time updates
├── data_generator.py               # Train simulation coordinator
├── train_movement.py               # Core train movement logic
├── multicast_monitor.py            # External multicast monitoring client
├── test_client.py                  # API testing utilities
├── requirements.txt                # Python dependencies
├── metro_tracking_enhanced.db      # SQLite database (auto-generated)
├── data/
│   ├── Fare.csv                   # Station fare matrix (Kaggle dataset)
│   ├── Route.csv                  # Station connectivity data
│   └── Time.csv                   # Travel time between stations
├── static/
│   ├── css/                       # Styling files
│   └── js/
│       └── app.js                 # Frontend JavaScript with map integration
└── templates/
    └── index.html                 # Main web interface
```

## 🔧 API Endpoints

### GET `/api/stations`
Returns all station information in JSON format.

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

### GET `/api/fare?from=<id>&to=<id>`
Returns fare calculation between two stations.

**Response:**
```json
{
  "fare": 2.80,
  "origin": "KL Sentral",
  "destination": "Ampang Park"
}
```

### GET `/api/route?from=<id>&to=<id>`
Calculates shortest route between two stations using BFS algorithm.

**Response:**
```json
{
  "path": [1, 2, 3],
  "total_fare": 5.30,
  "total_hops": 2,
  "stations": ["KL Sentral", "Bangsar", "Kerinchi"]
}
```

## 🌐 WebSocket Events

### Client → Server
- `connect`: Establish WebSocket connection
- `disconnect`: Close connection
- `request_trains`: Request current train positions

### Server → Client
- `initial_trains`: Initial train positions sent on connection
- `train_update`: Real-time train position updates
- `status`: System status messages

## 📡 Multicast Communication

The system includes UDP multicast broadcasting for external monitoring:

### Multicast Configuration
- **Group**: 224.1.1.1:9001
- **Protocol**: UDP with Python pickle serialization
- **Update Frequency**: Every 3-6 seconds per train

### External Monitoring
```bash
# Monitor multicast updates
python multicast_monitor.py
```

## 🗄️ Database Schema & Entity Relationship Diagram

### Entity Relationship Diagram

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          KL Metro System - Entity Relationship Diagram                ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ENTITIES                                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────┐                               ┌───────────────────────┐
│      STATIONS         │                               │        FARES          │
│                       │                               │                       │
│ ┌─────────────────┐   │          ┌─────────────┐      │ ┌─────────────────┐   │
│ │ station_id (PK) │   │◄─────────│   HAS_FARE  │──────┤ │ origin_id (FK)  │   │
│ │ name            │   │          │ (1:M)       │      │ │ dest_id (FK)    │   │
│ │ latitude        │   │          └─────────────┘      │ │ price           │   │
│ │ longitude       │   │                               │ │ distance_km     │   │
│ │ line            │   │                               │ │ travel_time_min │   │
│ └─────────────────┘   │                               │ └─────────────────┘   │
└───────────────────────┘                               └───────────────────────┘
           │                                                       │
           │                                                       │
           │ ┌─────────────┐                                      │
           └─│  LOCATED_AT │                                      │
             │   (1:M)     │                                      │
             └─────────────┘                                      │
                    │                                             │
                    ▼                                             │
┌───────────────────────┐                               ┌───────────────────────┐
│       TRAINS          │                               │      ROUTES           │
│                       │                               │                       │
│ ┌─────────────────┐   │          ┌─────────────┐      │ ┌─────────────────┐   │
│ │ train_id (PK)   │   │◄─────────│    MOVES    │──────┤ │ origin_id (FK)  │   │
│ │ current_        │   │          │   (1:M)     │      │ │ dest_id (FK)    │   │
│ │ station_id (FK) │   │          └─────────────┘      │ │ line            │   │
│ │ latitude        │   │                               │ │ sequence_order  │   │
│ │ longitude       │   │                               │ │ is_bidirect     │   │
│ │ line            │   │                               │ │ travel_time     │   │
│ │ direction       │   │                               │ └─────────────────┘   │
│ │ last_updated    │   │                               └───────────────────────┘
│ └─────────────────┘   │                                          │
└───────────────────────┘                                          │
           │                                                       │
           │                                             ┌─────────────┐
           └─────────────────────────────────────────────│ CONNECTED_TO│
                                                         │   (M:M)     │
                                                         └─────────────┘
                    │
                    ▼
┌───────────────────────┐
│   TRAIN_MOVEMENTS     │
│                       │
│ ┌─────────────────┐   │
│ │ movement_id(PK) │   │
│ │ train_id (FK)   │   │
│ │ from_stn_id(FK) │   │
│ │ to_stn_id (FK)  │   │
│ │ departure_time  │   │
│ │ arrival_time    │   │
│ │ timestamp       │   │
│ └─────────────────┘   │
└───────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES (CSV FILES)                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Fare.csv      │         │   Route.csv     │         │   Time.csv      │
│                 │         │                 │         │                 │
│ • Origin Stn    │ ────┐   │ • Origin Stn    │ ────┐   │ • Station Pair  │ ────┐
│ • Dest Station  │     │   │ • Dest Station  │     │   │ • Travel Time   │     │
│ • Price         │     │   │ • Line Info     │     │   │ • Line Specific │     │
│ • Distance      │     │   │ • Connectivity  │     │   │ • Schedule Data │     │
│ • Travel Time   │     │   │ • Bidirectional │     │   │ • Time Matrix   │     │
└─────────────────┘     │   └─────────────────┘     │   └─────────────────┘     │
                        │                           │                           │
                        ▼                           ▼                           ▼
                 ┌─────────────────────────────────────────────────────────────────┐
                 │              KAGGLE DATASET INTEGRATION                        │
                 │                                                                │
                 │  • Authentic Malaysian KL Metro System Data                   │
                 │  • Real station coordinates and connectivity                  │
                 │  • Actual fare structure and pricing                         │
                 │  • Historical travel time patterns                           │
                 │  • 68 Total Stations across 3 Lines                         │
                 │    - LRT Kelana Jaya Line: 37 stations                       │
                 │    - LRT Ampang Line: 13 stations                           │
                 │    - MRT SBK Line: 18 stations                              │
                 └─────────────────────────────────────────────────────────────────┘
```

### Database Tables Specification

#### 1. STATIONS Table
```sql
CREATE TABLE stations (
    station_id INTEGER PRIMARY KEY,      -- Unique identifier for each station
    name TEXT NOT NULL,                  -- Station name (e.g., "KL Sentral")
    latitude REAL NOT NULL,              -- GPS latitude coordinate
    longitude REAL NOT NULL,             -- GPS longitude coordinate
    line TEXT DEFAULT 'Unknown'          -- Metro line (LRT Kelana Jaya, LRT Ampang, MRT SBK)
);
```
**Purpose**: Central repository for all metro stations with geographic coordinates
**Records**: 68 stations total across 3 metro lines
**Key Features**: GPS coordinates for map visualization, line association for route planning

#### 2. FARES Table
```sql
CREATE TABLE fares (
    origin_id INTEGER,                   -- Foreign key to stations table
    destination_id INTEGER,              -- Foreign key to stations table  
    price REAL NOT NULL,                 -- Fare amount in Malaysian Ringgit (RM)
    distance_km REAL DEFAULT 0,          -- Distance between stations in kilometers
    travel_time_min INTEGER DEFAULT 0,   -- Expected travel time in minutes
    FOREIGN KEY (origin_id) REFERENCES stations (station_id),
    FOREIGN KEY (destination_id) REFERENCES stations (station_id)
);
```
**Purpose**: Fare calculation matrix for any station pair
**Data Source**: Kaggle Fare.csv with authentic MyRapidKL pricing
**Key Features**: Distance-based pricing, travel time estimation

#### 3. TRAINS Table  
```sql
CREATE TABLE trains (
    train_id INTEGER PRIMARY KEY,        -- Unique train identifier (1-8)
    current_station_id INTEGER,          -- Current location foreign key
    latitude REAL,                       -- Real-time GPS latitude
    longitude REAL,                      -- Real-time GPS longitude
    line TEXT DEFAULT 'Unknown',         -- Operating line assignment
    direction TEXT DEFAULT 'forward',    -- Movement direction (forward/backward)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Last position update
    FOREIGN KEY (current_station_id) REFERENCES stations (station_id)
);
```
**Purpose**: Real-time train tracking and position management
**Active Records**: 8 trains distributed across 3 metro lines
**Update Frequency**: Every 3-6 seconds during simulation

#### 4. ROUTES Table (Virtual/Derived)
```sql
-- Derived from Route.csv for connectivity mapping
CREATE TABLE routes (
    origin_id INTEGER,                   -- Starting station
    destination_id INTEGER,              -- Connected station
    line TEXT,                          -- Line identifier  
    sequence_order INTEGER,             -- Order in line sequence
    is_bidirectional BOOLEAN DEFAULT 1, -- Two-way connectivity
    travel_time_min INTEGER,            -- Time between adjacent stations
    FOREIGN KEY (origin_id) REFERENCES stations (station_id),
    FOREIGN KEY (destination_id) REFERENCES stations (station_id)
);
```
**Purpose**: Define station connectivity for realistic train movement
**Data Source**: Route.csv from Kaggle dataset
**Key Features**: Sequential ordering, bidirectional links, line-specific routing

#### 5. TRAIN_MOVEMENTS Table (Historical Tracking)
```sql
CREATE TABLE train_movements (
    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique movement record
    train_id INTEGER,                              -- Foreign key to trains
    from_station_id INTEGER,                       -- Origin station
    to_station_id INTEGER,                         -- Destination station  
    departure_time TIMESTAMP,                      -- Movement start time
    arrival_time TIMESTAMP,                        -- Movement end time
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation time
    FOREIGN KEY (train_id) REFERENCES trains (train_id),
    FOREIGN KEY (from_station_id) REFERENCES stations (station_id),
    FOREIGN KEY (to_station_id) REFERENCES stations (station_id)
);
```
**Purpose**: Historical movement tracking and analytics
**Growth**: Continuous logging of all train movements
**Applications**: Performance analysis, scheduling optimization, system monitoring

### Relationship Specifications

| Relationship | Cardinality | Description |
|--------------|-------------|-------------|
| **STATIONS → FARES** | 1:M | Each station can have multiple fare records (as origin or destination) |
| **STATIONS → TRAINS** | 1:M | Each station can host multiple trains, but each train is at one station |
| **STATIONS → ROUTES** | M:M | Stations connect to multiple other stations bidirectionally |
| **TRAINS → TRAIN_MOVEMENTS** | 1:M | Each train generates multiple movement records over time |
| **STATIONS → TRAIN_MOVEMENTS** | 1:M | Each station participates in multiple movements (as origin/destination) |

### Data Integrity & Constraints

- **Primary Keys**: Ensure unique identification for all entities
- **Foreign Keys**: Maintain referential integrity across related tables  
- **NOT NULL Constraints**: Enforce required fields (station names, coordinates, fares)
- **Default Values**: Provide fallback values for optional fields
- **Timestamp Tracking**: Automatic timestamping for audit trails
- **Cascade Operations**: Proper handling of dependent record updates/deletions

## 🔄 Data Flow

1. **Initialization**: Flask app starts and loads CSV data into SQLite database
2. **Train Simulation**: TrainSimulator creates 8 trains across 3 metro lines
3. **Realistic Movement**: TrainMovement class moves trains sequentially along line routes
4. **Database Update**: Train positions updated in SQLite database every 3-6 seconds
5. **WebSocket Broadcast**: Position updates sent to all connected clients via Flask-SocketIO
6. **Multicast Distribution**: Train updates also sent via UDP multicast for external monitoring
7. **Frontend Update**: JavaScript receives updates and animates train markers on the map
8. **Route Planning**: Users select stations, system calculates optimal path using BFS algorithm

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
- **3 Metro Lines**: LRT Kelana Jaya (37 stations), LRT Ampang (13 stations), MRT SBK (18 stations)

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

### LRT Kelana Jaya Line (37 stations)
- **Route**: Gombak ↔ Putra Heights
- **Trains**: 3 trains with realistic sequential movement
- **Key Stations**: KL Sentral, KLCC, Ampang Park, Wangsa Maju

### LRT Ampang Line (13 stations)
- **Route**: Sentul Timur ↔ Ampang
- **Trains**: 2 trains following line sequence
- **Key Stations**: Masjid Jamek, Plaza Rakyat, Hang Tuah

### MRT SBK Line (18 stations)
- **Route**: Sungai Buloh ↔ Kajang
- **Trains**: 3 trains with north-south movement
- **Key Stations**: Semantan, Muzium Negara, Merdeka

## 🔍 Testing & Validation

### API Testing
```bash
# Test station data
curl http://localhost:5000/api/stations

# Test fare calculation
curl "http://localhost:5000/api/fare?from=1&to=10"

# Test route planning
curl "http://localhost:5000/api/route?from=1&to=20"
```

### WebSocket Testing
```javascript
// Browser console testing
const socket = io();
socket.on('train_update', (data) => console.log('Train update:', data));
socket.on('initial_trains', (data) => console.log('Initial trains:', data));
```

### Multicast Monitoring
```bash
# Monitor external updates
python multicast_monitor.py
```

## �️ Error Handling

- **Database Errors**: Graceful fallbacks and connection management
- **Network Issues**: Automatic WebSocket reconnection attempts
- **Invalid Routes**: Clear error messages for impossible paths
- **Missing Data**: Default values and user-friendly notifications
- **API Validation**: Input parameter validation and error responses

## 📱 User Interface

- **Interactive Map**: Leaflet.js map with zoom, pan, and marker interactions
- **Station Selection**: Click stations to select origin and destination
- **Real-time Updates**: Live train position updates with smooth animations
- **Route Visualization**: Shortest path highlighted with fare information
- **Responsive Design**: Mobile-friendly interface that adapts to different screen sizes
- **Train Information**: Hover over trains to see current location and line information

## � Technical Implementation

### Backend Technologies
- **Flask 2.3.3**: Web framework for HTTP API and WebSocket support
- **Flask-SocketIO 5.3.6**: Real-time bidirectional WebSocket communication
- **SQLite**: Lightweight database for station, fare, and train data
- **Pandas**: CSV data processing and manipulation
- **Threading**: Background train simulation and concurrent request handling

### Frontend Technologies
- **Leaflet.js**: Interactive map library for station and train visualization
- **Socket.IO Client**: WebSocket client for real-time train updates
- **Bootstrap**: CSS framework for responsive UI components
- **JavaScript (ES6)**: Modern JavaScript for dynamic map interactions

### Data Sources
- **Kaggle Dataset**: Authentic Malaysian metro system data
- **OpenStreetMap**: Base map tiles for geographical visualization
- **Custom Coordinates**: Accurate GPS coordinates for all metro stations

## 🎯 Academic Learning Outcomes

This project demonstrates key concepts from the UEEN3123/UEEN3433 course:

### CO2: TCP/UDP Applications
- **WebSocket Implementation**: Real-time TCP-based communication using Flask-SocketIO
- **UDP Multicast**: Efficient broadcast distribution for external monitoring
- **HTTP REST API**: Standard TCP-based API endpoints for data exchange
- **Network Programming**: Socket-level communication patterns and protocols

### CO3: Multicast/Broadcast Communication
- **UDP Multicast Groups**: 224.1.1.1:9001 for train update distribution
- **External Monitoring**: Standalone multicast client for system monitoring
- **Efficient Broadcasting**: Single message to multiple subscribers pattern
- **Network Topology**: Understanding of multicast vs unicast communication

### CO4: Network Application Scripting
- **Python Automation**: Automated train simulation and movement patterns
- **Background Processing**: Threading for concurrent train simulation
- **Data Integration**: CSV to database automation with pandas
- **Real-time Systems**: Event-driven programming with WebSocket callbacks

## 🚀 Performance Optimization

- **Efficient Updates**: Only changed train positions sent via WebSocket
- **Database Indexing**: Primary and foreign keys for fast query performance
- **Map Optimization**: Marker reuse and selective DOM updates
- **Connection Pooling**: Efficient SQLite connection management
- **Minimal Data Transfer**: Compressed JSON payloads for network efficiency

## 🔍 Debugging & Monitoring

### Application Logs
- **Train Movement**: Console logs for train position changes
- **WebSocket Events**: Connection, disconnection, and message logs
- **Database Operations**: Query execution and error logging
- **API Requests**: HTTP request/response logging with timing

### Browser Developer Tools
- **Network Tab**: Monitor WebSocket messages and API calls
- **Console Logs**: Frontend application state and error messages
- **Elements Inspector**: Examine map markers and UI component state
- **Performance Tab**: Analyze rendering performance and memory usage

## 🎯 Future Enhancements

- **Real-time Alerts**: Service disruption notifications and maintenance updates
- **Historical Analytics**: Train movement pattern analysis and statistics
- **Mobile Application**: Native mobile app for iOS and Android platforms
- **Advanced Routing**: Alternative route suggestions with transfer optimization
- **Passenger Simulation**: Crowd density and boarding/alighting patterns
- **Integration APIs**: Connect with real MyRapidKL systems and external transit apps
- **Machine Learning**: Predictive analytics for optimal scheduling and routing

## 📚 Course Integration

This project integrates practical concepts from the TCP/IP Network Application Development course:

### Laboratory Exercises Applied
- **Lab2 Multicast**: UDP multicast broadcasting for external monitoring systems
- **Lab2 RPyC**: Client-server architecture with robust connection management
- **Lab3 Flask**: Web application framework with database integration and session handling
- **MyWorkspace Examples**: TCP socket programming fundamentals and binary data transfer

### Networking Concepts Demonstrated
- **Application Layer Protocols**: HTTP REST API and WebSocket real-time communication
- **Transport Layer**: TCP reliability for WebSocket and UDP efficiency for multicast
- **Client-Server Architecture**: Multiple clients connecting to centralized Flask server
- **Real-time Systems**: Event-driven programming with immediate update propagation

## 📄 License

This project is developed for educational purposes as part of the UEEN3123/UEEN3433 TCP/IP Network Application Development course at Universiti Tunku Abdul Rahman (UTAR).

## 👥 Project Information

- **Course**: UEEN3123/UEEN3433 TCP/IP Network Application Development
- **Assignment**: Real-Time Metro Tracking and Routing System
- **Institution**: UTAR (Universiti Tunku Abdul Rahman)
- **Academic Session**: 2024/2025
- **Dataset**: Malaysian KL Metro System (Kaggle)

## 🤝 Acknowledgments

- **MyRapidKL**: For the inspiration of the Kuala Lumpur metro system
- **Kaggle**: For providing the authentic Malaysian metro dataset
- **OpenStreetMap**: For the geographical map tiles and location data
- **Course Instructors**: For the guidance and practical exercise frameworks

---

For technical support, questions, or contributions to this educational project, please refer to the course materials or contact the development team.

#!/usr/bin/env python3
"""
KL Metro Route Line Connections Visualization
Shows how the two metro lines are connected and their station sequences
"""

import sqlite3
import pandas as pd

def show_metro_connections():
    conn = sqlite3.connect('metro_tracking_enhanced.db')
    
    print("=" * 80)
    print("🚇 KL METRO SYSTEM - ROUTE LINE CONNECTIONS")
    print("=" * 80)
    print()
    
    # Get KJL line stations
    print("🟢 LRT KELANA JAYA LINE (KJL) - 37 Stations")
    print("Route: Gombak ↔ Putra Heights (Bidirectional)")
    print("-" * 60)
    
    kjl_stations = conn.execute('''
        SELECT station_id, name FROM stations 
        WHERE line = 'KJL' 
        ORDER BY station_id
    ''').fetchall()
    
    # Show first and last 10 stations to demonstrate the line
    print("Direction A (Gombak → Putra Heights):")
    for i, (sid, name) in enumerate(kjl_stations[:10], 1):
        print(f"  {i:2d}. {name}")
    print("   ... (middle stations)")
    for i, (sid, name) in enumerate(kjl_stations[-7:], len(kjl_stations)-6):
        print(f"  {i:2d}. {name}")
    
    print()
    print("🔵 MRT SUNGAI BULOH-KAJANG LINE (SBK) - 31 Stations")
    print("Route: Sungai Buloh ↔ Kajang (Bidirectional)")
    print("-" * 60)
    
    sbk_stations = conn.execute('''
        SELECT station_id, name FROM stations 
        WHERE line = 'SBK' 
        ORDER BY station_id
    ''').fetchall()
    
    # Show first and last 10 stations to demonstrate the line
    print("Direction A (Sungai Buloh → Kajang):")
    for i, (sid, name) in enumerate(sbk_stations[:10], 1):
        print(f"  {i:2d}. {name}")
    print("   ... (middle stations)")
    for i, (sid, name) in enumerate(sbk_stations[-5:], len(sbk_stations)-4):
        print(f"  {i:2d}. {name}")
    
    print()
    print("🔗 LINE INTERCONNECTION ANALYSIS")
    print("-" * 50)
    
    # Check the Route.csv to understand connections
    route_df = pd.read_csv('data/Route.csv')
    print("📊 Route Data Structure:")
    print(f"   • Total route combinations: {len(route_df)} rows")
    print(f"   • Station pairs covered: {len(route_df.columns)-1} destinations per origin")
    
    # Check for transfer opportunities
    print()
    print("🚉 STATION TRANSFER OPPORTUNITIES:")
    print("   Based on Route.csv analysis:")
    
    # Look for stations that appear in both lines through route connections
    route_header = route_df.columns.tolist()
    print(f"   • All stations can connect via route planning algorithm")
    print(f"   • System uses BFS (Breadth-First Search) for optimal paths")
    print(f"   • Cross-line transfers available through station proximity")
    
    # Check specific interchange possibilities
    pasar_seni_stations = [col for col in route_header if 'Pasar Seni' in col]
    if pasar_seni_stations:
        print(f"   • Pasar Seni serves as key interchange: {pasar_seni_stations}")
    
    print()
    print("🚂 TRAIN OPERATION DETAILS")
    print("-" * 40)
    trains = conn.execute('SELECT train_id, line, direction, current_station_id FROM trains ORDER BY train_id').fetchall()
    
    for train_id, line, direction, current_station in trains:
        station_name = conn.execute('SELECT name FROM stations WHERE station_id = ?', (current_station,)).fetchone()
        station_name = station_name[0] if station_name else "Unknown"
        print(f"  🚋 Train {train_id}: {line} Line ({direction}) - Currently at {station_name}")
    
    print()
    print("📈 SYSTEM CONNECTIVITY MATRIX")
    print("-" * 45)
    print(f"  ├─ Total Stations: {len(kjl_stations) + len(sbk_stations)}")
    print(f"  ├─ KJL Line Stations: {len(kjl_stations)}")
    print(f"  ├─ SBK Line Stations: {len(sbk_stations)}")
    print(f"  ├─ Active Trains: {len(trains)}")
    print(f"  ├─ Operational Lines: 2")
    print(f"  └─ Movement Pattern: Sequential station-to-station with terminal reversals")
    
    print()
    print("🗺️  LINE CONNECTION VISUALIZATION")
    print("-" * 50)
    print("KJL: Gombak ←→ Taman Melati ←→ ... ←→ USJ21 ←→ Putra Heights")
    print("                     ↕️ (Route Planning)")
    print("SBK: Sungai Buloh ←→ Kampung Selamat ←→ ... ←→ Stadium Kajang ←→ Kajang")
    print()
    print("📝 Connection Method: Algorithmic routing using BFS pathfinding")
    print("   • No physical track connection between lines")
    print("   • Route planning calculates optimal multi-line journeys")
    print("   • Transfer recommendations based on proximity and fare optimization")
    
    conn.close()

if __name__ == "__main__":
    show_metro_connections()

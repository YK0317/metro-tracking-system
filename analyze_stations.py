#!/usr/bin/env python3
"""
Analyze KJL station coordinates to identify geographical inconsistencies
"""

import pandas as pd
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def analyze_kjl_stations():
    """Analyze KJL station coordinates"""
    
    # Read stations data
    stations_df = pd.read_csv('data/Stations.csv')
    
    # Filter KJL stations and sort by station_id
    kjl_stations = stations_df[stations_df['line'] == 'KJL'].sort_values('station_id')
    
    print("🚇 KJL Line Station Analysis")
    print("=" * 60)
    print(f"Total KJL stations: {len(kjl_stations)}")
    print()
    
    print("📍 Station Coordinates (in sequence):")
    print("-" * 60)
    
    large_gaps = []
    
    for i, (_, station) in enumerate(kjl_stations.iterrows()):
        print(f"{station['station_id']:2d}. {station['name']:<25} ({station['latitude']:.4f}, {station['longitude']:.4f})")
        
        # Calculate distance to next station
        if i < len(kjl_stations) - 1:
            next_station = kjl_stations.iloc[i + 1]
            
            distance = calculate_distance(
                station['latitude'], station['longitude'],
                next_station['latitude'], next_station['longitude']
            )
            
            print(f"    └─ Distance to {next_station['name']}: {distance:.2f} km")
            
            # Flag large gaps (> 5km)
            if distance > 5.0:
                large_gaps.append({
                    'from': station['name'],
                    'to': next_station['name'],
                    'distance': distance,
                    'from_coords': (station['latitude'], station['longitude']),
                    'to_coords': (next_station['latitude'], next_station['longitude'])
                })
                print(f"    ⚠️  WARNING: Large gap detected!")
            
            print()
    
    if large_gaps:
        print("\n🚨 PROBLEMATIC CONNECTIONS:")
        print("=" * 60)
        for gap in large_gaps:
            print(f"⚠️  {gap['from']} → {gap['to']}")
            print(f"   Distance: {gap['distance']:.2f} km")
            print(f"   From: {gap['from_coords']}")
            print(f"   To: {gap['to_coords']}")
            print()
            
            # Suggest why this might be problematic
            lat_diff = abs(gap['to_coords'][0] - gap['from_coords'][0])
            lng_diff = abs(gap['to_coords'][1] - gap['from_coords'][1])
            
            if lat_diff > 0.1:
                print(f"   📍 Large latitude change: {lat_diff:.4f} degrees")
            if lng_diff > 0.1:
                print(f"   📍 Large longitude change: {lng_diff:.4f} degrees")
            print()

if __name__ == "__main__":
    analyze_kjl_stations()

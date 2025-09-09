import csv
import pandas as pd

# Read Route.csv header to get all stations
with open('data/Route.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    route_header = next(reader)
    route_stations = [station.strip() for station in route_header[1:]]  # Skip first empty column

# Read Stations.csv to get existing stations
stations_df = pd.read_csv('data/Stations.csv')
existing_stations = stations_df['name'].tolist()

print(f"Route.csv has {len(route_stations)} stations")
print(f"Stations.csv has {len(existing_stations)} stations")

# Find missing stations
missing_stations = []
for station in route_stations:
    if station not in existing_stations:
        missing_stations.append(station)

if missing_stations:
    print(f"\nMissing stations in Stations.csv:")
    for i, station in enumerate(missing_stations, 1):
        print(f"{i}. {station}")
else:
    print("\nAll stations from Route.csv are present in Stations.csv")

# Find extra stations
extra_stations = []
for station in existing_stations:
    if station not in route_stations:
        extra_stations.append(station)

if extra_stations:
    print(f"\nExtra stations in Stations.csv (not in Route.csv):")
    for i, station in enumerate(extra_stations, 1):
        print(f"{i}. {station}")

# Print station order comparison
print("\nFirst 10 stations from Route.csv header:")
for i, station in enumerate(route_stations[:10], 1):
    print(f"{i}. {station}")

print("\nFirst 10 stations from Stations.csv:")
for i, station in enumerate(existing_stations[:10], 1):
    print(f"{i}. {station}")

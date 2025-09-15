#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proper Socket.IO Load Test for Flask-SocketIO Server
Tests the actual Socket.IO events and real-time functionality
"""

import socketio
import time
import threading
import json
import statistics
import argparse
from datetime import datetime
import logging
import sys
import os

# Fix for Windows console encoding issues
if sys.platform == "win32":
    # Set UTF-8 encoding for Windows console
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    # Alternative: use environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class SocketIOLoadTest:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.results = {
            'successful_connections': 0,
            'failed_connections': 0,
            'events_received': {},
            'train_updates': [],
            'connection_times': [],
            'errors': []
        }
        
    def create_client(self, client_id, test_duration):
        """Create a Socket.IO client for testing"""
        client_stats = {
            'client_id': client_id,
            'connected': False,
            'events_received': {},
            'train_updates_count': 0,
            'connection_time': None,
            'errors': []
        }
        
        # Create Socket.IO client
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        @sio.event
        def connect():
            """Handle successful connection"""
            client_stats['connected'] = True
            client_stats['connection_time'] = time.time()
            print(f"✅ Client {client_id}: Connected to Socket.IO server")
            
        @sio.event
        def disconnect():
            """Handle disconnection"""
            print(f"🔌 Client {client_id}: Disconnected from Socket.IO server")
            
        @sio.event
        def connect_error(data):
            """Handle connection errors"""
            error_msg = f"Connection error: {data}"
            client_stats['errors'].append(error_msg)
            print(f"❌ Client {client_id}: {error_msg}")
            
        @sio.event
        def initial_trains(data):
            """Handle initial train data"""
            client_stats['events_received']['initial_trains'] = client_stats['events_received'].get('initial_trains', 0) + 1
            
            if isinstance(data, list) and len(data) > 0:
                print(f"🚂 Client {client_id}: Received initial trains data ({len(data)} trains)")
                # Show example of first train data structure
                first_train = data[0]
                if isinstance(first_train, dict):
                    sample_fields = list(first_train.keys())[:5]  # Show first 5 fields
                    print(f"   📋 Sample train fields: {sample_fields}")
            else:
                print(f"🚂 Client {client_id}: Received initial trains data (unknown format)")
            
        @sio.event
        def train_update(data):
            """Handle real-time train updates"""
            client_stats['events_received']['train_update'] = client_stats['events_received'].get('train_update', 0) + 1
            client_stats['train_updates_count'] += 1
            
            if isinstance(data, list):
                print(f"🚄 Client {client_id}: Train update batch ({len(data)} trains)")
                # Show details for first train in batch
                if data and len(data) > 0:
                    first_train = data[0]
                    train_id = first_train.get('train_id', 'unknown')
                    station = (first_train.get('station_name') or 
                              first_train.get('current_station_name') or 
                              first_train.get('station_id', 'unknown'))
                    line = first_train.get('line', 'unknown')
                    print(f"   └─ Example: Train {train_id} ({line}) → {station}")
            else:
                train_id = data.get('train_id', 'unknown')
                # Try multiple possible station name fields
                station = (data.get('station_name') or 
                          data.get('current_station_name') or 
                          data.get('station_id', 'unknown'))
                line = data.get('line', 'unknown')
                direction = data.get('direction', '')
                
                # Enhanced display with more details
                direction_text = f" ({direction})" if direction else ""
                print(f"🚄 Client {client_id}: Train {train_id} ({line}) → {station}{direction_text}")
                
                # Log raw data structure for debugging (first few times only)
                if client_stats['train_updates_count'] <= 3:
                    available_fields = list(data.keys()) if isinstance(data, dict) else []
                    print(f"   🔍 Debug: Available fields: {available_fields}")
            
        @sio.event
        def status(data):
            """Handle status messages"""
            client_stats['events_received']['status'] = client_stats['events_received'].get('status', 0) + 1
            msg = data.get('msg', 'No message')
            print(f"📊 Client {client_id}: Status - {msg}")
            
        try:
            # Connect to Socket.IO server
            connect_start = time.time()
            sio.connect(self.server_url)
            
            if client_stats['connected']:
                self.results['successful_connections'] += 1
                connect_time = time.time() - connect_start
                self.results['connection_times'].append(connect_time)
                
                # Keep connection alive for test duration
                time.sleep(test_duration)
                
                # Test sending events (if your server handles client events)
                try:
                    sio.emit('ping', {'client_id': client_id, 'timestamp': time.time()})
                    sio.emit('request_trains', {'client_id': client_id})
                except Exception as e:
                    client_stats['errors'].append(f"Emit error: {e}")
                
            else:
                self.results['failed_connections'] += 1
                
        except Exception as e:
            error_msg = f"Client {client_id} error: {e}"
            client_stats['errors'].append(error_msg)
            self.results['errors'].append(error_msg)
            self.results['failed_connections'] += 1
            print(f"❌ {error_msg}")
            
        finally:
            try:
                sio.disconnect()
            except:
                pass
                
        return client_stats
        
    def run_load_test(self, num_clients=10, test_duration=30):
        """Run Socket.IO load test"""
        print(f"🚀 Starting Socket.IO Load Test")
        print(f"📡 Server: {self.server_url}")
        print(f"👥 Clients: {num_clients}")
        print(f"⏱️  Duration: {test_duration}s")
        print("-" * 50)
        
        # Create client threads
        threads = []
        client_results = []
        
        def run_client(client_id):
            result = self.create_client(client_id, test_duration)
            client_results.append(result)
            
        # Start all clients
        start_time = time.time()
        for i in range(num_clients):
            thread = threading.Thread(target=run_client, args=(i,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Stagger connections
            
        # Wait for all clients to complete
        for thread in threads:
            thread.join()
            
        total_time = time.time() - start_time
        
        # Aggregate results
        for result in client_results:
            for event_type, count in result['events_received'].items():
                self.results['events_received'][event_type] = self.results['events_received'].get(event_type, 0) + count
                
        # Print results
        self.print_results(total_time)
        self.save_results()
        
    def print_results(self, total_time):
        """Print test results"""
        print("\n" + "=" * 60)
        print("📊 SOCKET.IO LOAD TEST RESULTS")
        print("=" * 60)
        
        total_clients = self.results['successful_connections'] + self.results['failed_connections']
        success_rate = (self.results['successful_connections'] / total_clients * 100) if total_clients > 0 else 0
        
        print(f"✅ Successful Connections: {self.results['successful_connections']}/{total_clients}")
        print(f"📈 Connection Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Total Test Time: {total_time:.2f}s")
        
        if self.results['connection_times']:
            avg_connect = statistics.mean(self.results['connection_times']) * 1000
            print(f"🔌 Average Connection Time: {avg_connect:.2f}ms")
            
        print(f"\n📡 Socket.IO Events Received:")
        for event_type, count in self.results['events_received'].items():
            print(f"   • {event_type}: {count}")
            
        total_events = sum(self.results['events_received'].values())
        if total_events > 0 and total_time > 0:
            events_per_sec = total_events / total_time
            print(f"📊 Event Rate: {events_per_sec:.1f} events/second")
            
        if self.results['errors']:
            print(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
                
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"socketio_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Run the Socket.IO load test with command line arguments"""
    parser = argparse.ArgumentParser(description='Socket.IO Load Testing Tool')
    parser.add_argument('--test-type', choices=['burst', 'ramp', 'endurance'], 
                        default='burst', help='Type of test to run (default: burst)')
    parser.add_argument('--clients', type=int, default=10, 
                        help='Number of concurrent clients (default: 10)')
    parser.add_argument('--duration', type=int, default=15, 
                        help='Test duration in seconds (default: 15)')
    parser.add_argument('--server', default='http://localhost:5000', 
                        help='Socket.IO server URL (default: http://localhost:5000)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print(f"🚀 Starting Socket.IO Load Test")
    print(f"📊 Test Type: {args.test_type}")
    print(f"📡 Server: {args.server}")
    print(f"👥 Clients: {args.clients}")
    print(f"⏱️  Duration: {args.duration}s")
    print("-" * 50)
    
    # Create and run test
    test = SocketIOLoadTest(args.server)
    test.run_load_test(args.clients, args.duration)

if __name__ == "__main__":
    main()
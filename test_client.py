"""
Enhanced Test Client for Metro Tracking System
Incorporates concepts from MyWorkspace TCP examples for comprehensive testing
"""

import socket
import json
import time
import threading
import requests
from datetime import datetime
import pickle
import struct

class MetroAPITestClient:
    """
    API test client (inspired by MyWorkspace HTTP client concepts)
    Tests REST API endpoints with comprehensive error handling
    """
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        
    def test_all_endpoints(self):
        """Test all API endpoints comprehensively"""
        print("🧪 METRO API TEST CLIENT")
        print("="*50)
        
        # Test stations endpoint
        print("1️⃣ Testing /api/stations")
        stations = self.test_stations()
        
        if stations:
            # Test fare endpoint with various combinations
            print("\n2️⃣ Testing /api/fare")
            self.test_fares(stations[:5])  # Test with first 5 stations
            
            # Test route planning
            print("\n3️⃣ Testing /api/route")
            self.test_routes(stations[:5])
            
        print("\n✅ API testing completed")
    
    def test_stations(self):
        """Test stations endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/stations")
            
            if response.status_code == 200:
                stations = response.json()
                print(f"   ✅ Retrieved {len(stations)} stations")
                
                # Validate station data structure
                if stations:
                    sample_station = stations[0]
                    required_fields = ['station_id', 'name', 'latitude', 'longitude']
                    
                    for field in required_fields:
                        if field not in sample_station:
                            print(f"   ⚠️ Missing field: {field}")
                        else:
                            print(f"   ✅ Field '{field}': {sample_station[field]}")
                
                return stations
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
    
    def test_fares(self, stations):
        """Test fare endpoint with multiple station combinations"""
        test_combinations = [
            (stations[0]['station_id'], stations[1]['station_id']),
            (stations[0]['station_id'], stations[2]['station_id']),
            (stations[1]['station_id'], stations[3]['station_id']),
        ]
        
        for origin_id, dest_id in test_combinations:
            try:
                # Test regular fare
                response = self.session.get(
                    f"{self.base_url}/api/fare",
                    params={'from': origin_id, 'to': dest_id}
                )
                
                if response.status_code == 200:
                    fare_data = response.json()
                    print(f"   ✅ Fare {origin_id}→{dest_id}: RM {fare_data.get('fare', 'N/A')}")
                    
                    # Test peak hour fare if enhanced system
                    response_peak = self.session.get(
                        f"{self.base_url}/api/fare",
                        params={'from': origin_id, 'to': dest_id, 'peak': 'true'}
                    )
                    
                    if response_peak.status_code == 200:
                        peak_data = response_peak.json()
                        if 'is_peak_hour' in peak_data:
                            print(f"   ✅ Peak fare {origin_id}→{dest_id}: RM {peak_data.get('fare', 'N/A')}")
                    
                else:
                    print(f"   ❌ Fare error {origin_id}→{dest_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Fare exception {origin_id}→{dest_id}: {e}")
    
    def test_routes(self, stations):
        """Test route planning endpoint"""
        test_routes = [
            (stations[0]['station_id'], stations[-1]['station_id']),
            (stations[1]['station_id'], stations[3]['station_id']),
        ]
        
        for origin_id, dest_id in test_routes:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/route",
                    params={'from': origin_id, 'to': dest_id}
                )
                
                if response.status_code == 200:
                    route_data = response.json()
                    path = route_data.get('path', [])
                    total_fare = route_data.get('total_fare', 0)
                    hops = route_data.get('total_hops', 0)
                    
                    print(f"   ✅ Route {origin_id}→{dest_id}:")
                    print(f"      Path: {' → '.join(map(str, path))}")
                    print(f"      Fare: RM {total_fare}, Hops: {hops}")
                    
                else:
                    print(f"   ❌ Route error {origin_id}→{dest_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Route exception {origin_id}→{dest_id}: {e}")

class MetroWebSocketClient:
    """
    WebSocket test client (inspired by real-time communication concepts)
    Tests WebSocket functionality with comprehensive event handling
    """
    
    def __init__(self, server_url='http://localhost:5000'):
        self.server_url = server_url
        self.connected = False
        self.message_count = 0
        self.train_updates = 0
        
    def test_websocket_connection(self, duration=30):
        """Test WebSocket connection for specified duration"""
        print(f"\n🔌 WEBSOCKET TEST CLIENT")
        print("="*50)
        print(f"Testing WebSocket connection for {duration} seconds...")
        
        try:
            import socketio
            
            # Create Socket.IO client
            sio = socketio.Client()
            
            @sio.event
            def connect():
                self.connected = True
                print("   ✅ WebSocket connected successfully")
            
            @sio.event
            def disconnect():
                self.connected = False
                print("   🔌 WebSocket disconnected")
            
            @sio.on('initial_trains')
            def on_initial_trains(data):
                print(f"   📊 Received initial train data: {len(data)} trains")
                
            @sio.on('train_update')
            def on_train_update(data):
                self.train_updates += 1
                train_id = data.get('train_id', 'N/A')
                station_name = data.get('station_name', 'Unknown')
                print(f"   🚇 Train {train_id} update: {station_name}")
            
            @sio.on('status')
            def on_status(data):
                self.message_count += 1
                print(f"   📢 Status: {data.get('msg', 'No message')}")
            
            @sio.on('system_alert')
            def on_system_alert(data):
                alert_type = data.get('type', 'UNKNOWN')
                message = data.get('message', 'No message')
                print(f"   🚨 System Alert [{alert_type}]: {message}")
            
            # Connect to server
            sio.connect(self.server_url)
            
            # Send test messages
            time.sleep(2)
            print("   📤 Sending test ping...")
            sio.emit('ping')
            
            time.sleep(2)
            print("   📤 Requesting train data...")
            sio.emit('request_trains')
            
            # Test zone subscription if available
            time.sleep(2)
            print("   📤 Testing zone subscription...")
            sio.emit('subscribe_zone', {'zone': 'Central'})
            
            # Wait for specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)
                
                # Print periodic updates
                if int(time.time() - start_time) % 10 == 0:
                    print(f"   ⏱️ Running for {int(time.time() - start_time)}s, "
                          f"received {self.train_updates} train updates")
            
            # Disconnect
            sio.disconnect()
            
            print(f"\n📈 WebSocket Test Results:")
            print(f"   Total Messages: {self.message_count}")
            print(f"   Train Updates: {self.train_updates}")
            print(f"   Test Duration: {duration}s")
            
        except ImportError:
            print("   ❌ python-socketio not installed. Install with: pip install python-socketio[client]")
        except Exception as e:
            print(f"   ❌ WebSocket test error: {e}")

class MetroTCPClient:
    """
    Raw TCP client (inspired by MyWorkspace ex1_client.py concepts)
    Tests low-level TCP connectivity to the Flask server
    """
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        
    def test_tcp_connection(self):
        """Test raw TCP connection to server"""
        print(f"\n🔧 TCP CONNECTION TEST")
        print("="*50)
        
        try:
            # Create socket (similar to MyWorkspace examples)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            
            print(f"Connecting to {self.host}:{self.port}...")
            
            # Connect to server
            client_socket.connect((self.host, self.port))
            print("   ✅ TCP connection established")
            
            # Send HTTP request manually
            http_request = (
                f"GET /api/stations HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )
            
            client_socket.send(http_request.encode())
            print("   📤 HTTP request sent")
            
            # Receive response
            response = b""
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    response += data
                except socket.timeout:
                    break
            
            if response:
                response_str = response.decode('utf-8', errors='ignore')
                lines = response_str.split('\r\n')
                status_line = lines[0] if lines else "No response"
                print(f"   📥 Response: {status_line}")
                
                # Check if it's a valid HTTP response
                if "200 OK" in status_line:
                    print("   ✅ Server responding correctly")
                else:
                    print("   ⚠️ Unexpected response")
            else:
                print("   ❌ No response received")
                
            client_socket.close()
            
        except socket.timeout:
            print("   ❌ Connection timeout")
        except ConnectionRefusedError:
            print("   ❌ Connection refused - is the server running?")
        except Exception as e:
            print(f"   ❌ TCP test error: {e}")

class MetroLoadTester:
    """
    Load testing client (inspired by concurrent connection concepts)
    Tests system performance under load
    """
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.results = []
        
    def run_load_test(self, concurrent_clients=5, requests_per_client=10):
        """Run load test with multiple concurrent clients"""
        print(f"\n⚡ LOAD TEST")
        print("="*50)
        print(f"Testing with {concurrent_clients} concurrent clients")
        print(f"Each client making {requests_per_client} requests")
        
        threads = []
        start_time = time.time()
        
        # Start concurrent client threads
        for i in range(concurrent_clients):
            thread = threading.Thread(
                target=self.client_worker,
                args=(i, requests_per_client)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = len([r for r in self.results if r['success']])
        total_requests = len(self.results)
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"\n📊 Load Test Results:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {successful_requests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Requests/sec: {total_requests/total_time:.2f}")
        
        if self.results:
            avg_response_time = sum(r['response_time'] for r in self.results) / len(self.results)
            print(f"   Avg Response Time: {avg_response_time:.3f}s")
    
    def client_worker(self, client_id, num_requests):
        """Worker function for each load test client"""
        session = requests.Session()
        session.timeout = 5
        
        for i in range(num_requests):
            start_time = time.time()
            success = False
            
            try:
                response = session.get(f"{self.base_url}/api/stations")
                success = response.status_code == 200
                
            except Exception as e:
                pass
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.results.append({
                'client_id': client_id,
                'request_id': i,
                'success': success,
                'response_time': response_time
            })

def main():
    """Main test function"""
    print("🚇 REAL-TIME METRO TRACKING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("Incorporating concepts from Lab exercises and practical examples")
    print("="*70)
    
    # Test API endpoints
    api_client = MetroAPITestClient()
    api_client.test_all_endpoints()
    
    # Test WebSocket functionality
    ws_client = MetroWebSocketClient()
    ws_client.test_websocket_connection(duration=15)
    
    # Test raw TCP connection
    tcp_client = MetroTCPClient()
    tcp_client.test_tcp_connection()
    
    # Run load test
    load_tester = MetroLoadTester()
    load_tester.run_load_test(concurrent_clients=3, requests_per_client=5)
    
    print("\n🎉 All tests completed!")
    print("Check the results above for any issues that need attention.")

if __name__ == '__main__':
    main()

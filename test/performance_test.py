#!/usr/bin/env python3
"""
REAL Performance Test Suite for KL Metro Tracking System (NO MOCKING)

This script tests ACTUAL server performance:
- Real Socket.IO latency via round-trip time measurement
- Actual database query execution times
- Real API response times with high-precision timing
- Actual system resource usage monitoring
- Real concurrent connection handling

Usage: python performance_test.py [--concurrent-clients N] [--test-duration S]
"""

import asyncio
import socketio
import json
import time
import sqlite3
import requests
import psutil
import threading
import statistics
from datetime import datetime
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

# Configure logging with timestamp and comprehensive format
log_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'performance_test_{log_timestamp}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log test start information
logger.info("=" * 80)
logger.info("REAL PERFORMANCE TEST SUITE STARTING")
logger.info("=" * 80)
logger.info(f"Log file: {log_filename}")
logger.info(f"Test timestamp: {datetime.now().isoformat()}")
logger.info("All measurements are REAL - no mocked values")

class PerformanceTest:
    def __init__(self, base_url="http://localhost:5000", socketio_url="http://localhost:5000", 
                 db_path="../metro_tracking_enhanced.db"):
        self.base_url = base_url
        self.socketio_url = socketio_url  # Socket.IO server URL
        self.db_path = db_path
        self.results = {
            'socketio_tests': [],
            'database_tests': [],
            'api_tests': [],
            'system_metrics': [],
            'summary': {}
        }
        
    def log_system_metrics(self):
        """Log current system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / (1024 * 1024),
            'memory_available_mb': memory.available / (1024 * 1024)
        }
        
        self.results['system_metrics'].append(metrics)
        return metrics

    def calculate_percentile(self, data, percentile):
        """Calculate percentile for a list of values"""
        if not data:
            return 0
        sorted_data = sorted(data)
        k = (percentile / 100.0) * (len(sorted_data) - 1)
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def test_socketio_client(self, client_id, duration=30):
        """Test individual Socket.IO client with REAL latency measurements"""
        client_stats = {
            'client_id': client_id,
            'connected': False,
            'events_received': {},
            'train_updates_count': 0,
            'connection_time': None,
            'ping_responses': {},
            'latencies': [],
            'errors': []
        }
        
        # Create Socket.IO client
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        @sio.event
        def connect():
            """Handle successful connection"""
            client_stats['connected'] = True
            client_stats['connection_time'] = time.perf_counter()
            logger.debug(f"Client {client_id}: Connected to Socket.IO server")
            
        @sio.event
        def disconnect():
            """Handle disconnection"""
            logger.debug(f"Client {client_id}: Disconnected from Socket.IO server")
            
        @sio.event
        def connect_error(data):
            """Handle connection errors"""
            error_msg = f"Connection error: {data}"
            client_stats['errors'].append(error_msg)
            logger.warning(f"Client {client_id}: {error_msg}")
            
        @sio.event
        def initial_trains(data):
            """Handle initial train data"""
            client_stats['events_received']['initial_trains'] = client_stats['events_received'].get('initial_trains', 0) + 1
            logger.debug(f"Client {client_id}: Received initial trains data")
            
        @sio.event
        def train_update(data):
            """Handle real-time train updates"""
            client_stats['events_received']['train_update'] = client_stats['events_received'].get('train_update', 0) + 1
            client_stats['train_updates_count'] += 1
            
            # Check for latency measurement if timestamp is available
            if isinstance(data, dict) and 'timestamp' in data:
                receive_time = time.perf_counter() * 1000
                send_time = data['timestamp']
                if isinstance(send_time, (int, float)):
                    latency = receive_time - send_time
                    if 0 < latency < 10000:  # Sanity check (less than 10 seconds)
                        client_stats['latencies'].append(latency)
            
        @sio.event
        def pong(data):
            """Handle pong response for latency measurement"""
            if 'ping_id' in data:
                ping_id = data['ping_id']
                if ping_id in client_stats['ping_responses']:
                    send_time = client_stats['ping_responses'][ping_id]
                    receive_time = time.perf_counter() * 1000
                    latency = receive_time - send_time
                    client_stats['latencies'].append(latency)
                    del client_stats['ping_responses'][ping_id]
                    logger.debug(f"Client {client_id}: Ping latency {latency:.2f}ms")
            
        @sio.event
        def status(data):
            """Handle status messages"""
            client_stats['events_received']['status'] = client_stats['events_received'].get('status', 0) + 1
            
        try:
            # Measure connection time
            connect_start = time.perf_counter()
            sio.connect(self.socketio_url)
            
            if client_stats['connected']:
                connect_time = (time.perf_counter() - connect_start) * 1000
                
                # Test duration
                start_time = time.perf_counter()
                last_ping_time = start_time
                
                while (time.perf_counter() - start_time) < duration:
                    try:
                        # Send ping every 2 seconds to measure latency
                        current_time = time.perf_counter()
                        if current_time - last_ping_time >= 2.0:
                            ping_id = str(uuid.uuid4())
                            ping_timestamp = current_time * 1000
                            
                            sio.emit('ping', {
                                'ping_id': ping_id,
                                'timestamp': ping_timestamp
                            })
                            
                            client_stats['ping_responses'][ping_id] = ping_timestamp
                            last_ping_time = current_time
                        
                        # Keep connection alive
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.warning(f"Client {client_id}: Event error - {e}")
                        break
                        
                session_duration = time.perf_counter() - start_time
                
                result = {
                    'client_id': client_id,
                    'connection_time_ms': connect_time,
                    'duration': session_duration,
                    'events_received': dict(client_stats['events_received']),
                    'train_updates_count': client_stats['train_updates_count'],
                    'latencies': client_stats['latencies'],
                    'avg_latency_ms': statistics.mean(client_stats['latencies']) if client_stats['latencies'] else None,
                    'min_latency_ms': min(client_stats['latencies']) if client_stats['latencies'] else None,
                    'max_latency_ms': max(client_stats['latencies']) if client_stats['latencies'] else None,
                    'median_latency_ms': statistics.median(client_stats['latencies']) if client_stats['latencies'] else None,
                    'success_rate': 1.0 if client_stats['train_updates_count'] > 0 or any(client_stats['events_received'].values()) else 0.0,
                    'errors': client_stats['errors']
                }
                
                logger.debug(f"Client {client_id}: Session completed - "
                           f"{sum(client_stats['events_received'].values())} events received")
                
                return result
            else:
                logger.error(f"Client {client_id}: Failed to connect")
                return None
                
        except Exception as e:
            error_msg = f"Client {client_id} error: {e}"
            logger.error(error_msg)
            return None
            
        finally:
            try:
                sio.disconnect()
            except:
                pass

    def test_concurrent_socketio(self, num_clients=50, duration=30):
        """Test concurrent Socket.IO connections with REAL performance measurement"""
        logger.info(f"Starting REAL Socket.IO test with {num_clients} concurrent clients for {duration}s")
        
        start_time = time.perf_counter()
        
        # Use ThreadPoolExecutor for concurrent Socket.IO clients
        successful_results = []
        failed_count = 0
        
        def run_client(client_id):
            return self.test_socketio_client(client_id, duration)
        
        with ThreadPoolExecutor(max_workers=min(num_clients, 100)) as executor:
            # Submit all client tasks
            futures = [executor.submit(run_client, i) for i in range(num_clients)]
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if result is not None:
                        successful_results.append(result)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Client task failed: {e}")
                    failed_count += 1
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{num_clients} Socket.IO clients")
        
        total_time = time.perf_counter() - start_time
        
        if successful_results:
            # Aggregate Socket.IO performance data
            all_latencies = []
            total_events = 0
            total_train_updates = 0
            connection_times = []
            
            for result in successful_results:
                if result['latencies']:
                    all_latencies.extend(result['latencies'])
                total_events += sum(result['events_received'].values())
                total_train_updates += result['train_updates_count']
                if result['connection_time_ms']:
                    connection_times.append(result['connection_time_ms'])
            
            summary = {
                'test_type': 'real_concurrent_socketio',
                'num_clients': num_clients,
                'successful_clients': len(successful_results),
                'failed_clients': failed_count,
                'success_rate': len(successful_results) / num_clients,
                'total_duration': total_time,
                'total_events': total_events,
                'total_train_updates': total_train_updates,
                'events_per_second': total_events / total_time if total_time > 0 else 0,
                'connection_stats': {
                    'avg_connection_time_ms': statistics.mean(connection_times) if connection_times else None,
                    'min_connection_time_ms': min(connection_times) if connection_times else None,
                    'max_connection_time_ms': max(connection_times) if connection_times else None
                }
            }
            
            # Add Socket.IO latency statistics if available
            if all_latencies:
                summary['avg_latency_ms'] = statistics.mean(all_latencies)
                summary['min_latency_ms'] = min(all_latencies)
                summary['max_latency_ms'] = max(all_latencies)
                summary['median_latency_ms'] = statistics.median(all_latencies)
                summary['p95_latency_ms'] = self.calculate_percentile(all_latencies, 95)
                summary['p99_latency_ms'] = self.calculate_percentile(all_latencies, 99)
                summary['latency_samples'] = len(all_latencies)
            else:
                summary['avg_latency_ms'] = None
                summary['latency_note'] = "No latency data available (server may not support ping/pong)"
            
            self.results['socketio_tests'].append(summary)
            
            logger.info(f"REAL Socket.IO test completed: {len(successful_results)}/{num_clients} clients successful")
            if all_latencies:
                logger.info(f"REAL Average latency: {summary['avg_latency_ms']:.2f}ms (from {len(all_latencies)} samples)")
                logger.info(f"REAL P95 latency: {summary['p95_latency_ms']:.2f}ms")
            else:
                logger.info("No real latency measurements available")
            logger.info(f"Event rate: {summary['events_per_second']:.2f} events/s")
            logger.info(f"Train updates: {total_train_updates}")
            
        return successful_results

    def test_database_performance(self, num_queries=1000):
        """Test REAL database query performance with actual SQLite operations"""
        logger.info(f"Starting REAL database performance test with {num_queries} queries")
        
        # REAL queries that match the actual database structure
        real_queries = [
            "SELECT * FROM trains LIMIT 10",
            "SELECT * FROM stations WHERE name LIKE '%KL%'", 
            "SELECT t.*, s.name as current_station FROM trains t JOIN stations s ON t.current_station_id = s.station_id LIMIT 5",
            "SELECT COUNT(*) FROM train_movements WHERE created_at > datetime('now', '-1 hour')",
            "SELECT line, COUNT(*) as train_count FROM trains GROUP BY line",
            "SELECT COUNT(*) FROM trains WHERE status = 'active'",
            "SELECT s.name, s.line FROM stations s WHERE s.line = 'Kelana Jaya Line'",
            "SELECT COUNT(*) FROM stations",
            "SELECT * FROM fares LIMIT 5",
            "SELECT COUNT(*) FROM system_events",
            "SELECT * FROM trains WHERE last_updated > datetime('now', '-1 hour')",
            "SELECT AVG(travel_duration) as avg_duration FROM train_movements WHERE travel_duration IS NOT NULL",
        ]
        
        query_times = []
        successful_queries = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for i in range(num_queries):
                query = real_queries[i % len(real_queries)]
                
                # Use high-precision timing for REAL measurement
                start_time = time.perf_counter()
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    end_time = time.perf_counter()
                    
                    query_time = (end_time - start_time) * 1000  # Convert to ms
                    query_times.append(query_time)
                    successful_queries += 1
                    
                except Exception as e:
                    logger.warning(f"Query failed: {e}")
                    continue
                
                if i % 100 == 0:
                    logger.info(f"Completed {i}/{num_queries} REAL database queries")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database test error: {e}")
            return None
        
        if query_times:
            db_result = {
                'test_type': 'real_database_performance',
                'num_queries': num_queries,
                'successful_queries': successful_queries,
                'success_rate': successful_queries / num_queries,
                'avg_query_time_ms': statistics.mean(query_times),
                'min_query_time_ms': min(query_times),
                'max_query_time_ms': max(query_times),
                'median_query_time_ms': statistics.median(query_times),
                'p95_query_time_ms': self.calculate_percentile(query_times, 95),
                'total_time_ms': sum(query_times),
                'queries_per_second': successful_queries / (sum(query_times) / 1000) if sum(query_times) > 0 else 0
            }
            
            self.results['database_tests'].append(db_result)
            logger.info(f"REAL Database test completed: {successful_queries}/{num_queries} successful")
            logger.info(f"REAL Average query time: {db_result['avg_query_time_ms']:.2f}ms")
            logger.info(f"REAL P95 query time: {db_result['p95_query_time_ms']:.2f}ms")
            logger.info(f"REAL Queries per second: {db_result['queries_per_second']:.1f}")
            
            return db_result
        
        return None

    def test_api_performance(self, num_requests=500):
        """Test REAL REST API performance with actual HTTP requests"""
        logger.info(f"Starting REAL API performance test with {num_requests} requests")
        
        # REAL API endpoints from the metro system (corrected)
        api_endpoints = [
            '/api/stations',
            '/api/fare?from=1&to=10',
            '/api/route?from=1&to=10',
            '/api/fare?from=5&to=15&peak=true',
            '/api/route?from=2&to=8',
            '/api/stations',  # Test stations endpoint multiple times
            '/',  # Main page
        ]
        
        response_times = []
        successful_requests = 0
        error_count = 0
        
        def make_real_request(endpoint):
            """Make REAL HTTP request and measure actual response time"""
            try:
                # Use high-precision timing for REAL measurement
                start_time = time.perf_counter()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.perf_counter()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    return response_time, True
                else:
                    logger.warning(f"API {endpoint} returned status {response.status_code}")
                    return response_time, False
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API {endpoint} timed out")
                return None, False
            except Exception as e:
                logger.warning(f"API request failed for {endpoint}: {e}")
                return None, False
        
        # Use ThreadPoolExecutor for REAL concurrent API requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            for i in range(num_requests):
                endpoint = api_endpoints[i % len(api_endpoints)]
                future = executor.submit(make_real_request, endpoint)
                futures.append(future)
            
            for i, future in enumerate(as_completed(futures)):
                response_time, success = future.result()
                
                if response_time is not None:
                    response_times.append(response_time)
                else:
                    error_count += 1
                    
                if success:
                    successful_requests += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Completed {i + 1}/{num_requests} REAL API requests")
        
        if response_times:
            api_result = {
                'test_type': 'real_api_performance',
                'num_requests': num_requests,
                'successful_requests': successful_requests,
                'error_count': error_count,
                'success_rate': successful_requests / num_requests,
                'avg_response_time_ms': statistics.mean(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'median_response_time_ms': statistics.median(response_times),
                'p95_response_time_ms': self.calculate_percentile(response_times, 95),
                'p99_response_time_ms': self.calculate_percentile(response_times, 99),
                'requests_per_second': successful_requests / (sum(response_times) / 1000) if sum(response_times) > 0 else 0
            }
            
            self.results['api_tests'].append(api_result)
            logger.info(f"REAL API test completed: {successful_requests}/{num_requests} successful")
            logger.info(f"REAL Average response time: {api_result['avg_response_time_ms']:.2f}ms")
            logger.info(f"REAL P95 response time: {api_result['p95_response_time_ms']:.2f}ms")
            logger.info(f"REAL Requests per second: {api_result['requests_per_second']:.1f}")
            
            return api_result
        
        return None

    def monitor_system_resources(self, duration=60):
        """Monitor system resources during testing"""
        logger.info(f"Starting system resource monitoring for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            self.log_system_metrics()
            time.sleep(5)  # Log every 5 seconds

    async def run_comprehensive_test(self, concurrent_clients=100, test_duration=60):
        """Run comprehensive performance test suite"""
        logger.info("Starting comprehensive performance test suite")
        logger.info(f"Target: {concurrent_clients} concurrent clients, {test_duration}s duration")
        
        overall_start = time.time()
        
        # Start system monitoring in background
        monitor_thread = threading.Thread(
            target=self.monitor_system_resources,
            args=(test_duration + 30,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Run tests sequentially to avoid interference
        try:
            # 1. Database performance test
            logger.info("\n=== Database Performance Test ===")
            self.test_database_performance(1000)
            
            # 2. API performance test
            logger.info("\n=== API Performance Test ===")
            self.test_api_performance(500)
            
            # 3. Socket.IO concurrent test
            logger.info("\n=== Socket.IO Concurrent Test ===")
            self.test_concurrent_socketio(concurrent_clients, test_duration)
            
        except Exception as e:
            logger.error(f"Test execution error: {e}")
        
        overall_time = time.time() - overall_start
        
        # Generate summary
        self.generate_summary(overall_time)
        
        # Save results
        self.save_results()
        
        logger.info("Comprehensive test suite completed")

    def generate_summary(self, total_duration):
        """Generate test summary"""
        summary = {
            'test_timestamp': datetime.now().isoformat(),
            'total_duration': total_duration,
            'tests_completed': 0,
            'performance_targets': {
                'concurrent_clients_target': 100,
                'latency_target_ms': 100,
                'db_query_target_ms': 50,
                'cpu_usage_target': 40
            },
            'results_summary': {}
        }
        
        # Socket.IO results
        if self.results['socketio_tests']:
            socketio_test = self.results['socketio_tests'][-1]
            summary['tests_completed'] += 1
            summary['results_summary']['socketio'] = {
                'concurrent_clients_achieved': socketio_test['successful_clients'],
                'avg_latency_ms': socketio_test['avg_latency_ms'],
                'success_rate': socketio_test['success_rate'],
                'total_events': socketio_test['total_events'],
                'total_train_updates': socketio_test['total_train_updates'],
                'events_per_second': socketio_test['events_per_second'],
                'meets_latency_target': socketio_test['avg_latency_ms'] <= 100 if socketio_test['avg_latency_ms'] else False,
                'meets_concurrency_target': socketio_test['successful_clients'] >= 100
            }
        
        # Database results
        if self.results['database_tests']:
            db_test = self.results['database_tests'][-1]
            summary['tests_completed'] += 1
            summary['results_summary']['database'] = {
                'avg_query_time_ms': db_test['avg_query_time_ms'],
                'queries_completed': db_test['num_queries'],
                'meets_query_target': db_test['avg_query_time_ms'] <= 50
            }
        
        # API results
        if self.results['api_tests']:
            api_test = self.results['api_tests'][-1]
            summary['tests_completed'] += 1
            summary['results_summary']['api'] = {
                'avg_response_time_ms': api_test['avg_response_time_ms'],
                'success_rate': api_test['success_rate'],
                'requests_completed': api_test['num_requests']
            }
        
        # System metrics summary
        if self.results['system_metrics']:
            cpu_values = [m['cpu_percent'] for m in self.results['system_metrics']]
            memory_values = [m['memory_percent'] for m in self.results['system_metrics']]
            
            summary['results_summary']['system'] = {
                'avg_cpu_percent': statistics.mean(cpu_values),
                'max_cpu_percent': max(cpu_values),
                'avg_memory_percent': statistics.mean(memory_values),
                'max_memory_percent': max(memory_values),
                'meets_cpu_target': statistics.mean(cpu_values) <= 40
            }
        
        self.results['summary'] = summary

    def save_results(self):
        """Save test results to file with comprehensive logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"performance_results_{timestamp}.json"
        
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Detailed test results saved to: {json_filename}")
            
            # Also save a summary report
            self.save_summary_report(timestamp)
            
            # Log completion summary
            logger.info("=" * 60)
            logger.info("TEST FILES GENERATED:")
            logger.info(f"- Detailed Results (JSON): {json_filename}")
            logger.info(f"- Summary Report (TXT): performance_report_{timestamp}.txt")
            logger.info(f"- Log File: {log_filename}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            logger.error(f"Failed to create output files - check permissions")

    def save_summary_report(self, timestamp):
        """Save human-readable summary report"""
        filename = f"performance_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== KL Metro Tracking System Performance Test Report ===\n\n")
                f.write(f"Test Date: {self.results['summary']['test_timestamp']}\n")
                f.write(f"Total Duration: {self.results['summary']['total_duration']:.2f} seconds\n\n")
                
                if 'socketio' in self.results['summary']['results_summary']:
                    socketio_result = self.results['summary']['results_summary']['socketio']
                    f.write("Socket.IO Performance:\n")
                    f.write(f"  - Concurrent Clients: {socketio_result['concurrent_clients_achieved']}\n")
                    f.write(f"  - Average Latency: {socketio_result['avg_latency_ms']:.2f}ms\n" if socketio_result['avg_latency_ms'] else "  - Average Latency: N/A (no ping/pong data)\n")
                    f.write(f"  - Success Rate: {socketio_result['success_rate']:.2%}\n")
                    f.write(f"  - Total Events: {socketio_result['total_events']}\n")
                    f.write(f"  - Train Updates: {socketio_result['total_train_updates']}\n")
                    f.write(f"  - Events/Second: {socketio_result['events_per_second']:.1f}\n")
                    f.write(f"  - Meets Targets: Latency={'PASS' if socketio_result['meets_latency_target'] else 'FAIL'}, Concurrency={'PASS' if socketio_result['meets_concurrency_target'] else 'FAIL'}\n\n")
                
                if 'database' in self.results['summary']['results_summary']:
                    db = self.results['summary']['results_summary']['database']
                    f.write("Database Performance:\n")
                    f.write(f"  - Average Query Time: {db['avg_query_time_ms']:.2f}ms\n")
                    f.write(f"  - Queries Completed: {db['queries_completed']}\n")
                    f.write(f"  - Meets Target: {'PASS' if db['meets_query_target'] else 'FAIL'}\n\n")
                
                if 'api' in self.results['summary']['results_summary']:
                    api = self.results['summary']['results_summary']['api']
                    f.write("API Performance:\n")
                    f.write(f"  - Average Response Time: {api['avg_response_time_ms']:.2f}ms\n")
                    f.write(f"  - Success Rate: {api['success_rate']:.2%}\n")
                    f.write(f"  - Requests Completed: {api['requests_completed']}\n\n")
                
                if 'system' in self.results['summary']['results_summary']:
                    sys = self.results['summary']['results_summary']['system']
                    f.write("System Resource Usage:\n")
                    f.write(f"  - Average CPU: {sys['avg_cpu_percent']:.1f}%\n")
                    f.write(f"  - Maximum CPU: {sys['max_cpu_percent']:.1f}%\n")
                    f.write(f"  - Average Memory: {sys['avg_memory_percent']:.1f}%\n")
                    f.write(f"  - Meets CPU Target: {'PASS' if sys['meets_cpu_target'] else 'FAIL'}\n\n")
                
                f.write("Performance Targets:\n")
                f.write("  - 100 concurrent clients: " + 
                       ("PASS" if self.results['summary']['results_summary'].get('socketio', {}).get('meets_concurrency_target', False) else "FAIL") + "\n")
                f.write("  - <100ms latency: " + 
                       ("PASS" if self.results['summary']['results_summary'].get('socketio', {}).get('meets_latency_target', False) else "FAIL") + "\n")
                f.write("  - <50ms DB queries: " + 
                       ("PASS" if self.results['summary']['results_summary'].get('database', {}).get('meets_query_target', False) else "FAIL") + "\n")
                f.write("  - <40% CPU usage: " + 
                       ("PASS" if self.results['summary']['results_summary'].get('system', {}).get('meets_cpu_target', False) else "FAIL") + "\n")
            
            logger.info(f"Summary report saved to: performance_report_{timestamp}.txt")
            
            # Add log file reference to the summary report
            with open(f"performance_report_{timestamp}.txt", 'a', encoding='utf-8') as f:
                f.write(f"\nTest Artifacts:\n")
                f.write(f"  - Detailed JSON Results: performance_results_{timestamp}.json\n")
                f.write(f"  - Log File: {log_filename}\n")
                f.write(f"  - Generated at: {datetime.now().isoformat()}\n")
            
        except Exception as e:
            logger.error(f"Error saving summary report: {e}")

async def main():
    parser = argparse.ArgumentParser(description='KL Metro Tracking System Performance Test')
    parser.add_argument('--concurrent-clients', type=int, default=100,
                       help='Number of concurrent Socket.IO clients (default: 100)')
    parser.add_argument('--test-duration', type=int, default=60,
                       help='Test duration in seconds (default: 60)')
    parser.add_argument('--base-url', default='http://localhost:5000',
                       help='Base URL for the application (default: http://localhost:5000)')
    parser.add_argument('--socketio-url', default='http://localhost:5000',
                       help='Socket.IO server URL (default: http://localhost:5000)')
    
    args = parser.parse_args()
    
    # Create test instance
    test = PerformanceTest(
        base_url=args.base_url,
        socketio_url=args.socketio_url
    )
    
    # Run comprehensive test
    await test.run_comprehensive_test(
        concurrent_clients=args.concurrent_clients,
        test_duration=args.test_duration
    )

if __name__ == "__main__":
    asyncio.run(main())

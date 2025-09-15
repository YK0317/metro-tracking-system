#!/usr/bin/env python3
"""
REAL Performance Test Suite for KL Metro Tracking System (NO MOCKING)

This script tests ACTUAL server performance:
- Real WebSocket latency via round-trip time measurement
- Actual database query execution times
- Real API response times with high-precision timing
- Actual system resource usage monitoring
- Real concurrent connection handling

Usage: python performance_test.py [--concurrent-clients N] [--test-duration S]
"""

import asyncio
import websockets
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
    def __init__(self, base_url="http://localhost:5000", ws_url="ws://localhost:8765", 
                 db_path="../metro_tracking_enhanced.db"):
        self.base_url = base_url
        self.ws_url = ws_url  # Pure WebSocket server on port 8765
        self.db_path = db_path
        self.results = {
            'websocket_tests': [],
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

    async def test_websocket_client(self, client_id, duration=30):
        """Test individual WebSocket client with REAL latency measurements"""
        ping_responses = {}  # Track ping-pong for real latency measurement
        messages_received = 0
        connection_start_time = None
        connection_time = None
        latencies = []
        
        try:
            # Measure ACTUAL connection time
            connection_start_time = time.perf_counter()
            async with websockets.connect(self.ws_url) as websocket:
                connection_end_time = time.perf_counter()
                connection_time = (connection_end_time - connection_start_time) * 1000
                
                logger.debug(f"Client {client_id}: Connected in {connection_time:.2f}ms")
                
                # Send initial subscription
                subscribe_msg = {
                    "type": "subscribe",
                    "data": {"route": "all"}
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                start_time = time.perf_counter()
                last_ping_time = start_time
                
                while (time.perf_counter() - start_time) < duration:
                    try:
                        # Send ping every 2 seconds to measure REAL latency
                        current_time = time.perf_counter()
                        if current_time - last_ping_time >= 2.0:
                            ping_id = str(uuid.uuid4())
                            ping_timestamp = time.perf_counter() * 1000  # High precision timestamp
                            
                            ping_msg = {
                                "type": "ping",
                                "ping_id": ping_id,
                                "timestamp": ping_timestamp
                            }
                            
                            await websocket.send(json.dumps(ping_msg))
                            ping_responses[ping_id] = ping_timestamp
                            last_ping_time = current_time
                        
                        # Listen for messages with timeout
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            receive_time = time.perf_counter() * 1000
                            messages_received += 1
                            
                            # Try to parse message and check for ping response
                            try:
                                data = json.loads(message)
                                
                                # Check if this is a pong response for REAL latency
                                if data.get('type') == 'pong' and 'ping_id' in data:
                                    ping_id = data['ping_id']
                                    if ping_id in ping_responses:
                                        send_time = ping_responses[ping_id]
                                        real_latency = receive_time - send_time
                                        latencies.append(real_latency)
                                        del ping_responses[ping_id]
                                        logger.debug(f"Client {client_id}: REAL ping latency {real_latency:.2f}ms")
                                
                                # Also check for server timestamps for additional latency measurement
                                elif 'server_timestamp' in data:
                                    server_time = data['server_timestamp']
                                    # Calculate approximate latency (half round-trip)
                                    estimated_latency = (receive_time - server_time) / 2
                                    if 0 < estimated_latency < 1000:  # Sanity check
                                        latencies.append(estimated_latency)
                                        
                            except json.JSONDecodeError:
                                pass  # Not JSON, just count as received message
                            
                        except asyncio.TimeoutError:
                            # No message received, continue
                            continue
                            
                    except Exception as e:
                        logger.warning(f"Client {client_id}: Message error - {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Client {client_id}: Connection error - {e}")
            return None
            
        if latencies or messages_received > 0:
            session_duration = time.perf_counter() - start_time
            
            result = {
                'client_id': client_id,
                'connection_time_ms': connection_time,
                'duration': session_duration,
                'messages_received': messages_received,
                'real_latencies': latencies,
                'avg_latency_ms': statistics.mean(latencies) if latencies else None,
                'min_latency_ms': min(latencies) if latencies else None,
                'max_latency_ms': max(latencies) if latencies else None,
                'median_latency_ms': statistics.median(latencies) if latencies else None,
                'success_rate': 1.0 if messages_received > 0 else 0.0,
                'message_rate': messages_received / session_duration if session_duration > 0 else 0
            }
            
            if latencies:
                logger.info(f"Client {client_id}: REAL avg latency: {result['avg_latency_ms']:.2f}ms, "
                           f"Messages: {messages_received}")
            else:
                logger.info(f"Client {client_id}: No latency data (no ping responses), Messages: {messages_received}")
            return result
        
        return None

    async def test_concurrent_websockets(self, num_clients=50, duration=30):
        """Test concurrent WebSocket connections with REAL performance measurement"""
        logger.info(f"Starting REAL WebSocket test with {num_clients} concurrent clients for {duration}s")
        
        start_time = time.perf_counter()
        
        # Create tasks for all clients
        tasks = [
            self.test_websocket_client(i, duration)
            for i in range(num_clients)
        ]
        
        # Run all clients concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        failed_count = len([r for r in results if isinstance(r, Exception)])
        
        total_time = time.perf_counter() - start_time
        
        if successful_results:
            # Aggregate REAL latency data
            all_latencies = []
            total_messages = 0
            connection_times = []
            
            for result in successful_results:
                if result['real_latencies']:
                    all_latencies.extend(result['real_latencies'])
                total_messages += result['messages_received']
                if result['connection_time_ms']:
                    connection_times.append(result['connection_time_ms'])
            
            summary = {
                'test_type': 'real_concurrent_websockets',
                'num_clients': num_clients,
                'successful_clients': len(successful_results),
                'failed_clients': failed_count,
                'success_rate': len(successful_results) / num_clients,
                'total_duration': total_time,
                'total_messages': total_messages,
                'messages_per_second': total_messages / total_time if total_time > 0 else 0,
                'connection_stats': {
                    'avg_connection_time_ms': statistics.mean(connection_times) if connection_times else None,
                    'min_connection_time_ms': min(connection_times) if connection_times else None,
                    'max_connection_time_ms': max(connection_times) if connection_times else None
                }
            }
            
            # Add REAL latency statistics if available
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
            
            self.results['websocket_tests'].append(summary)
            
            logger.info(f"REAL WebSocket test completed: {len(successful_results)}/{num_clients} clients successful")
            if all_latencies:
                logger.info(f"REAL Average latency: {summary['avg_latency_ms']:.2f}ms (from {len(all_latencies)} samples)")
                logger.info(f"REAL P95 latency: {summary['p95_latency_ms']:.2f}ms")
            else:
                logger.info("No real latency measurements available")
            logger.info(f"Message rate: {summary['messages_per_second']:.2f} msg/s")
            
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
            
            # 3. WebSocket concurrent test
            logger.info("\n=== WebSocket Concurrent Test ===")
            await self.test_concurrent_websockets(concurrent_clients, test_duration)
            
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
        
        # WebSocket results
        if self.results['websocket_tests']:
            ws_test = self.results['websocket_tests'][-1]
            summary['tests_completed'] += 1
            summary['results_summary']['websocket'] = {
                'concurrent_clients_achieved': ws_test['successful_clients'],
                'avg_latency_ms': ws_test['avg_latency_ms'],
                'success_rate': ws_test['success_rate'],
                'meets_latency_target': ws_test['avg_latency_ms'] <= 100,
                'meets_concurrency_target': ws_test['successful_clients'] >= 100
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
                
                if 'websocket' in self.results['summary']['results_summary']:
                    ws = self.results['summary']['results_summary']['websocket']
                    f.write("WebSocket Performance:\n")
                    f.write(f"  - Concurrent Clients: {ws['concurrent_clients_achieved']}\n")
                    f.write(f"  - Average Latency: {ws['avg_latency_ms']:.2f}ms\n")
                    f.write(f"  - Success Rate: {ws['success_rate']:.2%}\n")
                    f.write(f"  - Meets Targets: Latency={'PASS' if ws['meets_latency_target'] else 'FAIL'}, Concurrency={'PASS' if ws['meets_concurrency_target'] else 'FAIL'}\n\n")
                
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
                       ("PASS" if self.results['summary']['results_summary'].get('websocket', {}).get('meets_concurrency_target', False) else "FAIL") + "\n")
                f.write("  - <100ms latency: " + 
                       ("PASS" if self.results['summary']['results_summary'].get('websocket', {}).get('meets_latency_target', False) else "FAIL") + "\n")
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
                       help='Number of concurrent WebSocket clients (default: 100)')
    parser.add_argument('--test-duration', type=int, default=60,
                       help='Test duration in seconds (default: 60)')
    parser.add_argument('--base-url', default='http://localhost:5000',
                       help='Base URL for the application (default: http://localhost:5000)')
    parser.add_argument('--ws-url', default='ws://localhost:5000/ws',
                       help='WebSocket URL (default: ws://localhost:5000/ws)')
    
    args = parser.parse_args()
    
    # Create test instance
    test = PerformanceTest(
        base_url=args.base_url,
        ws_url=args.ws_url
    )
    
    # Run comprehensive test
    await test.run_comprehensive_test(
        concurrent_clients=args.concurrent_clients,
        test_duration=args.test_duration
    )

if __name__ == "__main__":
    asyncio.run(main())

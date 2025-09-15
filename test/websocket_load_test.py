#!/usr/bin/env python3
"""
WebSocket Load Testing Script for KL Metro Tracking System

Specifically tests WebSocket connection handling and real-time message broadcasting
under various load conditions.

Usage: python websocket_load_test.py [--clients N] [--duration S] [--ramp-up S]
"""

import asyncio
import websockets
import json
import time
import statistics
import argparse
import logging
from datetime import datetime
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketLoadTest:
    def __init__(self, ws_url="ws://localhost:5000/ws"):
        self.ws_url = ws_url
        self.active_clients = []
        self.test_results = {
            'connections': [],
            'messages': [],
            'errors': [],
            'summary': {}
        }
        self.running = True
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("Received shutdown signal, stopping test...")
        self.running = False

    async def create_websocket_client(self, client_id, test_duration, message_interval=1.0):
        """Create a single WebSocket client that sends/receives messages"""
        client_stats = {
            'client_id': client_id,
            'connected_at': None,
            'disconnected_at': None,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'latencies': [],
            'connection_time': None
        }
        
        try:
            # Measure connection time
            connect_start = time.time()
            websocket = await websockets.connect(self.ws_url)
            connect_end = time.time()
            
            client_stats['connected_at'] = connect_start
            client_stats['connection_time'] = (connect_end - connect_start) * 1000  # ms
            
            logger.debug(f"Client {client_id}: Connected in {client_stats['connection_time']:.2f}ms")
            
            # Subscribe to train updates
            subscribe_msg = {
                "type": "subscribe",
                "data": {"route": "all"}
            }
            await websocket.send(json.dumps(subscribe_msg))
            client_stats['messages_sent'] += 1
            
            start_time = time.time()
            last_message_time = start_time
            
            # Main message loop
            while self.running and (time.time() - start_time) < test_duration:
                try:
                    # Send periodic ping/status requests
                    if time.time() - last_message_time >= message_interval:
                        message_start = time.time()
                        
                        status_msg = {
                            "type": "get_status",
                            "timestamp": message_start,
                            "client_id": client_id
                        }
                        
                        await websocket.send(json.dumps(status_msg))
                        client_stats['messages_sent'] += 1
                        last_message_time = time.time()
                    
                    # Listen for incoming messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        message_end = time.time()
                        
                        try:
                            data = json.loads(message)
                            # Calculate latency if timestamp is available
                            if 'timestamp' in data:
                                latency = (message_end - data['timestamp']) * 1000
                                client_stats['latencies'].append(latency)
                        except json.JSONDecodeError:
                            pass
                        
                        client_stats['messages_received'] += 1
                        
                    except asyncio.TimeoutError:
                        # No message received, continue
                        continue
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning(f"Client {client_id}: Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Client {client_id}: Message error - {e}")
                    client_stats['errors'] += 1
                    
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
            
            await websocket.close()
            client_stats['disconnected_at'] = time.time()
            
        except Exception as e:
            logger.error(f"Client {client_id}: Connection error - {e}")
            client_stats['errors'] += 1
            client_stats['disconnected_at'] = time.time()
        
        # Calculate final stats
        if client_stats['connected_at'] and client_stats['disconnected_at']:
            client_stats['session_duration'] = client_stats['disconnected_at'] - client_stats['connected_at']
        
        if client_stats['latencies']:
            client_stats['avg_latency'] = statistics.mean(client_stats['latencies'])
            client_stats['min_latency'] = min(client_stats['latencies'])
            client_stats['max_latency'] = max(client_stats['latencies'])
        
        self.test_results['connections'].append(client_stats)
        return client_stats

    async def ramp_up_test(self, total_clients, ramp_up_duration, test_duration):
        """Gradually ramp up clients over time to test scaling"""
        logger.info(f"Starting ramp-up test: {total_clients} clients over {ramp_up_duration}s")
        
        clients_per_second = total_clients / ramp_up_duration
        client_tasks = []
        
        start_time = time.time()
        clients_started = 0
        
        while clients_started < total_clients and self.running:
            # Calculate how many clients should be started by now
            elapsed = time.time() - start_time
            target_clients = min(int(elapsed * clients_per_second), total_clients)
            
            # Start new clients
            while clients_started < target_clients:
                task = asyncio.create_task(
                    self.create_websocket_client(
                        client_id=clients_started,
                        test_duration=test_duration,
                        message_interval=2.0
                    )
                )
                client_tasks.append(task)
                clients_started += 1
                
                logger.info(f"Started client {clients_started}/{total_clients}")
            
            await asyncio.sleep(0.1)  # Check every 100ms
        
        logger.info(f"All {total_clients} clients started, waiting for test completion...")
        
        # Wait for all clients to complete
        completed_clients = await asyncio.gather(*client_tasks, return_exceptions=True)
        
        successful_clients = [c for c in completed_clients if isinstance(c, dict)]
        logger.info(f"Ramp-up test completed: {len(successful_clients)}/{total_clients} successful")
        
        return successful_clients

    async def burst_test(self, num_clients, test_duration):
        """Start all clients simultaneously to test burst capacity"""
        logger.info(f"Starting burst test: {num_clients} clients simultaneously")
        
        # Create all client tasks at once
        client_tasks = [
            self.create_websocket_client(
                client_id=i,
                test_duration=test_duration,
                message_interval=1.5
            )
            for i in range(num_clients)
        ]
        
        # Start all clients simultaneously
        start_time = time.time()
        completed_clients = await asyncio.gather(*client_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_clients = [c for c in completed_clients if isinstance(c, dict)]
        logger.info(f"Burst test completed in {total_time:.2f}s: {len(successful_clients)}/{num_clients} successful")
        
        return successful_clients

    async def endurance_test(self, num_clients, test_duration):
        """Long-running test to check for memory leaks and stability"""
        logger.info(f"Starting endurance test: {num_clients} clients for {test_duration}s")
        
        # Use fewer clients but longer duration and more messages
        client_tasks = [
            self.create_websocket_client(
                client_id=i,
                test_duration=test_duration,
                message_interval=0.5  # More frequent messages
            )
            for i in range(num_clients)
        ]
        
        completed_clients = await asyncio.gather(*client_tasks, return_exceptions=True)
        successful_clients = [c for c in completed_clients if isinstance(c, dict)]
        
        logger.info(f"Endurance test completed: {len(successful_clients)}/{num_clients} successful")
        
        return successful_clients

    def analyze_results(self, test_type, test_params):
        """Analyze test results and generate summary"""
        connections = self.test_results['connections']
        
        if not connections:
            logger.error("No connection data available for analysis")
            return
        
        successful_connections = [c for c in connections if c.get('connected_at') is not None]
        
        # Connection statistics
        connection_times = [c['connection_time'] for c in successful_connections if c.get('connection_time')]
        total_messages_sent = sum(c['messages_sent'] for c in connections)
        total_messages_received = sum(c['messages_received'] for c in connections)
        total_errors = sum(c['errors'] for c in connections)
        
        # Latency statistics
        all_latencies = []
        for c in successful_connections:
            if c.get('latencies'):
                all_latencies.extend(c['latencies'])
        
        # Session duration statistics
        session_durations = [c['session_duration'] for c in successful_connections 
                           if c.get('session_duration')]
        
        summary = {
            'test_type': test_type,
            'test_params': test_params,
            'timestamp': datetime.now().isoformat(),
            'total_clients': len(connections),
            'successful_connections': len(successful_connections),
            'connection_success_rate': len(successful_connections) / len(connections) if connections else 0,
            'total_messages_sent': total_messages_sent,
            'total_messages_received': total_messages_received,
            'total_errors': total_errors,
            'message_loss_rate': 1 - (total_messages_received / total_messages_sent) if total_messages_sent > 0 else 0
        }
        
        if connection_times:
            summary['connection_stats'] = {
                'avg_connection_time_ms': statistics.mean(connection_times),
                'min_connection_time_ms': min(connection_times),
                'max_connection_time_ms': max(connection_times),
                'median_connection_time_ms': statistics.median(connection_times)
            }
        
        if all_latencies:
            summary['latency_stats'] = {
                'avg_latency_ms': statistics.mean(all_latencies),
                'min_latency_ms': min(all_latencies),
                'max_latency_ms': max(all_latencies),
                'median_latency_ms': statistics.median(all_latencies),
                'p95_latency_ms': statistics.quantiles(all_latencies, n=20)[18],  # 95th percentile
                'p99_latency_ms': statistics.quantiles(all_latencies, n=100)[98]  # 99th percentile
            }
        
        if session_durations:
            summary['session_stats'] = {
                'avg_session_duration_s': statistics.mean(session_durations),
                'min_session_duration_s': min(session_durations),
                'max_session_duration_s': max(session_durations)
            }
        
        self.test_results['summary'] = summary
        
        # Log key results
        logger.info(f"\n=== {test_type.upper()} TEST RESULTS ===")
        logger.info(f"Successful Connections: {summary['successful_connections']}/{summary['total_clients']} "
                   f"({summary['connection_success_rate']:.1%})")
        logger.info(f"Messages: Sent={summary['total_messages_sent']}, "
                   f"Received={summary['total_messages_received']}, "
                   f"Loss Rate={summary['message_loss_rate']:.1%}")
        
        if 'latency_stats' in summary:
            lat = summary['latency_stats']
            logger.info(f"Latency: Avg={lat['avg_latency_ms']:.2f}ms, "
                       f"P95={lat['p95_latency_ms']:.2f}ms, "
                       f"P99={lat['p99_latency_ms']:.2f}ms")
        
        if 'connection_stats' in summary:
            conn = summary['connection_stats']
            logger.info(f"Connection Time: Avg={conn['avg_connection_time_ms']:.2f}ms")

    def save_results(self, test_type):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"websocket_load_test_{test_type}_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"Test results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main():
    parser = argparse.ArgumentParser(description='WebSocket Load Test for KL Metro Tracking System')
    parser.add_argument('--ws-url', default='ws://localhost:5000/ws',
                       help='WebSocket URL (default: ws://localhost:5000/ws)')
    parser.add_argument('--test-type', choices=['burst', 'ramp', 'endurance'], 
                       default='burst', help='Type of test to run')
    parser.add_argument('--clients', type=int, default=50,
                       help='Number of concurrent clients (default: 50)')
    parser.add_argument('--duration', type=int, default=30,
                       help='Test duration in seconds (default: 30)')
    parser.add_argument('--ramp-up', type=int, default=10,
                       help='Ramp-up duration in seconds for ramp test (default: 10)')
    
    args = parser.parse_args()
    
    # Create test instance
    test = WebSocketLoadTest(ws_url=args.ws_url)
    
    test_params = {
        'clients': args.clients,
        'duration': args.duration,
        'ramp_up': args.ramp_up if args.test_type == 'ramp' else None
    }
    
    try:
        logger.info(f"Starting {args.test_type} test with {args.clients} clients for {args.duration}s")
        
        if args.test_type == 'burst':
            await test.burst_test(args.clients, args.duration)
        elif args.test_type == 'ramp':
            await test.ramp_up_test(args.clients, args.ramp_up, args.duration)
        elif args.test_type == 'endurance':
            await test.endurance_test(args.clients, args.duration)
        
        # Analyze and save results
        test.analyze_results(args.test_type, test_params)
        test.save_results(args.test_type)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test execution error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

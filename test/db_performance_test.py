#!/usr/bin/env python3
"""
Database Performance Testing Script for KL Metro Tracking System

Tests SQLite database performance under various load conditions including:
- Query response times
- Concurrent access
- Transaction throughput
- Index performance

Usage: python db_performance_test.py [--db-path PATH] [--queries N] [--threads N]
"""

import sqlite3
import time
import statistics
import threading
import argparse
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabasePerformanceTest:
    def __init__(self, db_path="../metro_tracking_enhanced.db"):
        self.db_path = db_path
        self.test_results = {
            'query_tests': [],
            'concurrent_tests': [],
            'transaction_tests': [],
            'summary': {}
        }
        
        # Define test queries with different complexity levels
        self.test_queries = {
            'simple_select': [
                "SELECT COUNT(*) FROM trains",
                "SELECT COUNT(*) FROM stations",
                "SELECT COUNT(*) FROM routes",
                "SELECT station_id, station_name FROM stations LIMIT 10"
            ],
            'medium_select': [
                "SELECT t.train_id, t.route_id, s.station_name FROM trains t JOIN stations s ON t.current_station_id = s.station_id",
                "SELECT route_id, COUNT(*) as train_count FROM trains GROUP BY route_id",
                "SELECT * FROM stations WHERE station_name LIKE '%KL%'",
                "SELECT t.*, r.route_name FROM trains t JOIN routes r ON t.route_id = r.route_id LIMIT 20"
            ],
            'complex_select': [
                """SELECT r.route_name, COUNT(t.train_id) as train_count, 
                   AVG(CASE WHEN t.status = 'active' THEN 1 ELSE 0 END) as active_ratio
                   FROM routes r LEFT JOIN trains t ON r.route_id = t.route_id 
                   GROUP BY r.route_id, r.route_name""",
                """SELECT mh.train_id, COUNT(*) as movement_count, 
                   MAX(mh.timestamp) as last_movement
                   FROM movement_history mh 
                   WHERE mh.timestamp > datetime('now', '-1 hour')
                   GROUP BY mh.train_id
                   ORDER BY movement_count DESC LIMIT 10""",
                """SELECT s1.station_name as from_station, s2.station_name as to_station,
                   COUNT(*) as trip_count
                   FROM movement_history mh1
                   JOIN movement_history mh2 ON mh1.train_id = mh2.train_id
                   JOIN stations s1 ON mh1.station_id = s1.station_id
                   JOIN stations s2 ON mh2.station_id = s2.station_id
                   WHERE mh2.timestamp > mh1.timestamp
                   GROUP BY s1.station_id, s2.station_id
                   ORDER BY trip_count DESC LIMIT 15"""
            ]
        }

    def test_connection_performance(self, num_connections=100):
        """Test database connection establishment performance"""
        logger.info(f"Testing connection performance with {num_connections} connections")
        
        connection_times = []
        
        for i in range(num_connections):
            start_time = time.time()
            try:
                conn = sqlite3.connect(self.db_path)
                conn.close()
                end_time = time.time()
                
                connection_time = (end_time - start_time) * 1000  # Convert to ms
                connection_times.append(connection_time)
                
            except Exception as e:
                logger.error(f"Connection {i} failed: {e}")
        
        if connection_times:
            result = {
                'test_type': 'connection_performance',
                'num_connections': num_connections,
                'successful_connections': len(connection_times),
                'avg_connection_time_ms': statistics.mean(connection_times),
                'min_connection_time_ms': min(connection_times),
                'max_connection_time_ms': max(connection_times),
                'median_connection_time_ms': statistics.median(connection_times)
            }
            
            logger.info(f"Connection test completed: Avg={result['avg_connection_time_ms']:.2f}ms")
            return result
        
        return None

    def test_query_performance(self, num_iterations=1000):
        """Test query performance across different complexity levels"""
        logger.info(f"Testing query performance with {num_iterations} iterations per query type")
        
        results = {}
        
        for complexity, queries in self.test_queries.items():
            logger.info(f"Testing {complexity} queries...")
            
            query_times = []
            successful_queries = 0
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for i in range(num_iterations):
                    query = queries[i % len(queries)]
                    
                    start_time = time.time()
                    try:
                        cursor.execute(query)
                        results_data = cursor.fetchall()
                        end_time = time.time()
                        
                        query_time = (end_time - start_time) * 1000  # Convert to ms
                        query_times.append(query_time)
                        successful_queries += 1
                        
                    except Exception as e:
                        logger.error(f"Query failed: {query} - {e}")
                    
                    if i % 100 == 0:
                        logger.debug(f"Completed {i}/{num_iterations} {complexity} queries")
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Database connection error for {complexity}: {e}")
                continue
            
            if query_times:
                result = {
                    'complexity': complexity,
                    'num_queries': num_iterations,
                    'successful_queries': successful_queries,
                    'success_rate': successful_queries / num_iterations,
                    'avg_query_time_ms': statistics.mean(query_times),
                    'min_query_time_ms': min(query_times),
                    'max_query_time_ms': max(query_times),
                    'median_query_time_ms': statistics.median(query_times),
                    'p95_query_time_ms': statistics.quantiles(query_times, n=20)[18] if len(query_times) >= 20 else max(query_times),
                    'queries_per_second': successful_queries / (sum(query_times) / 1000) if sum(query_times) > 0 else 0
                }
                
                results[complexity] = result
                logger.info(f"{complexity}: Avg={result['avg_query_time_ms']:.2f}ms, "
                           f"QPS={result['queries_per_second']:.1f}")
        
        self.test_results['query_tests'].append(results)
        return results

    def concurrent_query_worker(self, worker_id, queries_per_worker, query_type='mixed'):
        """Worker function for concurrent query testing"""
        worker_stats = {
            'worker_id': worker_id,
            'queries_executed': 0,
            'successful_queries': 0,
            'query_times': [],
            'errors': []
        }
        
        try:
            # Each worker gets its own connection
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Select queries based on type
            if query_type == 'simple':
                queries = self.test_queries['simple_select']
            elif query_type == 'complex':
                queries = self.test_queries['complex_select']
            else:  # mixed
                all_queries = []
                for q_list in self.test_queries.values():
                    all_queries.extend(q_list)
                queries = all_queries
            
            for i in range(queries_per_worker):
                query = queries[i % len(queries)]
                
                start_time = time.time()
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    end_time = time.time()
                    
                    query_time = (end_time - start_time) * 1000
                    worker_stats['query_times'].append(query_time)
                    worker_stats['successful_queries'] += 1
                    
                except Exception as e:
                    worker_stats['errors'].append(str(e))
                
                worker_stats['queries_executed'] += 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.001)
            
            conn.close()
            
        except Exception as e:
            worker_stats['errors'].append(f"Connection error: {e}")
        
        return worker_stats

    def test_concurrent_access(self, num_threads=20, queries_per_thread=50):
        """Test concurrent database access performance"""
        logger.info(f"Testing concurrent access with {num_threads} threads, "
                   f"{queries_per_thread} queries per thread")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all worker tasks
            futures = [
                executor.submit(self.concurrent_query_worker, i, queries_per_thread, 'mixed')
                for i in range(num_threads)
            ]
            
            # Collect results
            worker_results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    worker_results.append(result)
                except Exception as e:
                    logger.error(f"Worker failed: {e}")
        
        total_time = time.time() - start_time
        
        # Aggregate results
        total_queries = sum(w['queries_executed'] for w in worker_results)
        successful_queries = sum(w['successful_queries'] for w in worker_results)
        all_query_times = []
        total_errors = 0
        
        for worker in worker_results:
            all_query_times.extend(worker['query_times'])
            total_errors += len(worker['errors'])
        
        if all_query_times:
            result = {
                'test_type': 'concurrent_access',
                'num_threads': num_threads,
                'queries_per_thread': queries_per_thread,
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': successful_queries / total_queries if total_queries > 0 else 0,
                'total_errors': total_errors,
                'total_time_s': total_time,
                'queries_per_second': successful_queries / total_time if total_time > 0 else 0,
                'avg_query_time_ms': statistics.mean(all_query_times),
                'min_query_time_ms': min(all_query_times),
                'max_query_time_ms': max(all_query_times),
                'median_query_time_ms': statistics.median(all_query_times),
                'p95_query_time_ms': statistics.quantiles(all_query_times, n=20)[18] if len(all_query_times) >= 20 else max(all_query_times)
            }
            
            self.test_results['concurrent_tests'].append(result)
            logger.info(f"Concurrent test completed: {successful_queries}/{total_queries} successful, "
                       f"QPS={result['queries_per_second']:.1f}, "
                       f"Avg latency={result['avg_query_time_ms']:.2f}ms")
            
            return result
        
        return None

    def test_transaction_performance(self, num_transactions=100):
        """Test transaction performance with batch operations"""
        logger.info(f"Testing transaction performance with {num_transactions} transactions")
        
        transaction_times = []
        successful_transactions = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for i in range(num_transactions):
                start_time = time.time()
                
                try:
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Simulate some work within transaction
                    # Insert some test data and then rollback
                    conn.execute("""
                        INSERT INTO movement_history (train_id, station_id, timestamp, direction)
                        VALUES (?, ?, datetime('now'), 'test')
                    """, (999, 1))
                    
                    conn.execute("""
                        UPDATE trains SET last_updated = datetime('now')
                        WHERE train_id = ?
                    """, (1,))
                    
                    # Query within transaction
                    cursor = conn.execute("SELECT COUNT(*) FROM movement_history WHERE train_id = 999")
                    result = cursor.fetchone()
                    
                    # Rollback to not affect actual data
                    conn.execute("ROLLBACK")
                    
                    end_time = time.time()
                    transaction_time = (end_time - start_time) * 1000
                    transaction_times.append(transaction_time)
                    successful_transactions += 1
                    
                except Exception as e:
                    logger.error(f"Transaction {i} failed: {e}")
                    try:
                        conn.execute("ROLLBACK")
                    except:
                        pass
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
        
        if transaction_times:
            result = {
                'test_type': 'transaction_performance',
                'num_transactions': num_transactions,
                'successful_transactions': successful_transactions,
                'success_rate': successful_transactions / num_transactions,
                'avg_transaction_time_ms': statistics.mean(transaction_times),
                'min_transaction_time_ms': min(transaction_times),
                'max_transaction_time_ms': max(transaction_times),
                'median_transaction_time_ms': statistics.median(transaction_times),
                'transactions_per_second': successful_transactions / (sum(transaction_times) / 1000) if sum(transaction_times) > 0 else 0
            }
            
            self.test_results['transaction_tests'].append(result)
            logger.info(f"Transaction test completed: {successful_transactions}/{num_transactions} successful, "
                       f"TPS={result['transactions_per_second']:.1f}, "
                       f"Avg time={result['avg_transaction_time_ms']:.2f}ms")
            
            return result
        
        return None

    def test_index_performance(self):
        """Test query performance with and without indexes"""
        logger.info("Testing index performance...")
        
        results = {}
        
        # Test queries that should benefit from indexes
        index_test_queries = [
            ("SELECT * FROM trains WHERE route_id = 1", "route_id index"),
            ("SELECT * FROM stations WHERE station_name = 'KL Sentral'", "station_name index"),
            ("SELECT * FROM movement_history WHERE train_id = 1 ORDER BY timestamp DESC LIMIT 10", "train_id + timestamp index"),
            ("SELECT COUNT(*) FROM movement_history WHERE timestamp > datetime('now', '-1 hour')", "timestamp index")
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for query, index_name in index_test_queries:
                query_times = []
                
                # Run query multiple times
                for _ in range(100):
                    start_time = time.time()
                    cursor = conn.execute(query)
                    results_data = cursor.fetchall()
                    end_time = time.time()
                    
                    query_time = (end_time - start_time) * 1000
                    query_times.append(query_time)
                
                if query_times:
                    results[index_name] = {
                        'query': query,
                        'avg_time_ms': statistics.mean(query_times),
                        'min_time_ms': min(query_times),
                        'max_time_ms': max(query_times),
                        'median_time_ms': statistics.median(query_times)
                    }
                    
                    logger.info(f"{index_name}: Avg={results[index_name]['avg_time_ms']:.2f}ms")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Index performance test error: {e}")
            return None
        
        return results

    def generate_summary(self):
        """Generate comprehensive test summary"""
        summary = {
            'test_timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'performance_summary': {}
        }
        
        # Query performance summary
        if self.test_results['query_tests']:
            latest_query_test = self.test_results['query_tests'][-1]
            query_summary = {}
            
            for complexity, data in latest_query_test.items():
                query_summary[complexity] = {
                    'avg_time_ms': data['avg_query_time_ms'],
                    'qps': data['queries_per_second'],
                    'success_rate': data['success_rate']
                }
            
            summary['performance_summary']['query_performance'] = query_summary
        
        # Concurrent access summary
        if self.test_results['concurrent_tests']:
            latest_concurrent = self.test_results['concurrent_tests'][-1]
            summary['performance_summary']['concurrent_access'] = {
                'total_qps': latest_concurrent['queries_per_second'],
                'avg_latency_ms': latest_concurrent['avg_query_time_ms'],
                'success_rate': latest_concurrent['success_rate'],
                'max_threads_tested': latest_concurrent['num_threads']
            }
        
        # Transaction performance summary
        if self.test_results['transaction_tests']:
            latest_transaction = self.test_results['transaction_tests'][-1]
            summary['performance_summary']['transaction_performance'] = {
                'tps': latest_transaction['transactions_per_second'],
                'avg_time_ms': latest_transaction['avg_transaction_time_ms'],
                'success_rate': latest_transaction['success_rate']
            }
        
        # Performance targets evaluation
        targets = {
            'query_time_target_ms': 50,
            'concurrent_qps_target': 100,
            'transaction_time_target_ms': 100
        }
        
        summary['target_evaluation'] = {}
        
        if 'query_performance' in summary['performance_summary']:
            simple_avg = summary['performance_summary']['query_performance'].get('simple_select', {}).get('avg_time_ms', 0)
            summary['target_evaluation']['meets_query_target'] = simple_avg <= targets['query_time_target_ms']
        
        if 'concurrent_access' in summary['performance_summary']:
            concurrent_qps = summary['performance_summary']['concurrent_access']['total_qps']
            summary['target_evaluation']['meets_concurrent_target'] = concurrent_qps >= targets['concurrent_qps_target']
        
        if 'transaction_performance' in summary['performance_summary']:
            tx_time = summary['performance_summary']['transaction_performance']['avg_time_ms']
            summary['target_evaluation']['meets_transaction_target'] = tx_time <= targets['transaction_time_target_ms']
        
        self.test_results['summary'] = summary
        
        # Log summary
        logger.info("\n=== DATABASE PERFORMANCE TEST SUMMARY ===")
        if 'query_performance' in summary['performance_summary']:
            for complexity, data in summary['performance_summary']['query_performance'].items():
                logger.info(f"{complexity}: {data['avg_time_ms']:.2f}ms avg, {data['qps']:.1f} QPS")
        
        if 'concurrent_access' in summary['performance_summary']:
            conc = summary['performance_summary']['concurrent_access']
            logger.info(f"Concurrent: {conc['total_qps']:.1f} QPS, {conc['avg_latency_ms']:.2f}ms avg latency")
        
        logger.info("Target Evaluation:")
        for target, met in summary['target_evaluation'].items():
            logger.info(f"  {target}: {'✓' if met else '✗'}")

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_performance_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"Database test results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    async def run_comprehensive_test(self):
        """Run all database performance tests"""
        logger.info("Starting comprehensive database performance test")
        
        try:
            # 1. Connection performance
            logger.info("\n=== Connection Performance Test ===")
            self.test_connection_performance(100)
            
            # 2. Query performance
            logger.info("\n=== Query Performance Test ===")
            self.test_query_performance(500)
            
            # 3. Concurrent access
            logger.info("\n=== Concurrent Access Test ===")
            self.test_concurrent_access(20, 50)
            
            # 4. Transaction performance
            logger.info("\n=== Transaction Performance Test ===")
            self.test_transaction_performance(100)
            
            # 5. Index performance
            logger.info("\n=== Index Performance Test ===")
            index_results = self.test_index_performance()
            
            # Generate summary
            self.generate_summary()
            
            # Save results
            self.save_results()
            
            logger.info("Comprehensive database test completed")
            
        except Exception as e:
            logger.error(f"Test execution error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Database Performance Test for KL Metro Tracking System')
    parser.add_argument('--db-path', default='../metro_tracking_enhanced.db',
                       help='Path to the SQLite database file')
    parser.add_argument('--queries', type=int, default=500,
                       help='Number of queries per test type (default: 500)')
    parser.add_argument('--threads', type=int, default=20,
                       help='Number of concurrent threads (default: 20)')
    parser.add_argument('--test-type', choices=['all', 'query', 'concurrent', 'transaction'],
                       default='all', help='Type of test to run')
    
    args = parser.parse_args()
    
    # Create test instance
    test = DatabasePerformanceTest(db_path=args.db_path)
    
    try:
        if args.test_type == 'all':
            import asyncio
            asyncio.run(test.run_comprehensive_test())
        elif args.test_type == 'query':
            test.test_query_performance(args.queries)
            test.generate_summary()
            test.save_results()
        elif args.test_type == 'concurrent':
            test.test_concurrent_access(args.threads, args.queries // args.threads)
            test.generate_summary()
            test.save_results()
        elif args.test_type == 'transaction':
            test.test_transaction_performance(args.queries)
            test.generate_summary()
            test.save_results()
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test execution error: {e}")

if __name__ == "__main__":
    main()

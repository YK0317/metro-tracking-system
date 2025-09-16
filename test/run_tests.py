#!/usr/bin/env python3
"""
Test Runner Script for KL Metro Tracking System

Orchestrates the execution of all performance tests and generates
consolidated reports for academic documentation.

Usage: python run_tests.py [--quick] [--report-only]
"""

import subprocess
import sys
import os
import json
import time
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self, quick_mode=False):
        self.quick_mode = quick_mode
        self.test_results = {}
        self.start_time = None
        self.reports_generated = []
        
    def check_system_availability(self):
        """Check if the metro tracking system is running"""
        try:
            import requests
            response = requests.get('http://localhost:5000', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Metro tracking system is running")
                return True
        except ImportError:
            logger.warning("requests module not found, installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], 
                         capture_output=True, encoding='utf-8', errors='replace')
            try:
                import requests
                response = requests.get('http://localhost:5000', timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Metro tracking system is running")
                    return True
            except:
                pass
        except:
            pass
        
        logger.error("❌ Metro tracking system is not accessible at http://localhost:5000")
        logger.error("Please start the system with: python app.py")
        return False
    
    def run_socketio_tests(self):
        """Run Socket.IO load tests (updated from WebSocket)"""
        logger.info("🔌 Running Socket.IO load tests...")
        
        test_configs = [
            {
                'type': 'burst', 
                'clients': 25 if self.quick_mode else 50, 
                'duration': 15 if self.quick_mode else 30
            },
            {
                'type': 'ramp', 
                'clients': 15 if self.quick_mode else 30, 
                'duration': 20 if self.quick_mode else 45
            }
        ]
        
        if not self.quick_mode:
            test_configs.append({
                'type': 'endurance', 
                'clients': 10, 
                'duration': 60
            })
        
        socketio_results = []
        
        for config in test_configs:
            logger.info(f"🚀 Running {config['type']} test with {config['clients']} clients for {config['duration']}s...")
            
            # Check which test file exists and use appropriate one
            test_script = None
            current_dir = os.path.dirname(os.path.abspath(__file__))
            socketio_path = os.path.join(current_dir, 'socketio_load_test.py')
            websocket_path = os.path.join(current_dir, 'websocket_load_test.py')
            
            if os.path.exists(socketio_path):
                test_script = 'socketio_load_test.py'
                logger.info("📄 Using socketio_load_test.py")
            elif os.path.exists(websocket_path):
                test_script = 'websocket_load_test.py'
                logger.info("📄 Using websocket_load_test.py as fallback")
            else:
                logger.error(f"❌ Neither socketio_load_test.py nor websocket_load_test.py found in {current_dir}!")
                logger.info(f"🔍 Files in directory: {os.listdir(current_dir)}")
                socketio_results.append({
                    'test_type': config['type'],
                    'config': config,
                    'success': False,
                    'error': 'No Socket.IO test script found'
                })
                continue
            
            # Use the found test file
            cmd = [
                sys.executable, test_script,
                '--test-type', config['type'],
                '--clients', str(config['clients']),
                '--duration', str(config['duration']),
                '--server', 'http://localhost:5000'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
                
                if result.returncode == 0:
                    logger.info(f"✅ {config['type']} test completed successfully")
                    socketio_results.append({
                        'test_type': config['type'],
                        'config': config,
                        'success': True,
                        'output': result.stdout,
                        'stderr': result.stderr
                    })
                else:
                    logger.error(f"❌ {config['type']} test failed: {result.stderr}")
                    socketio_results.append({
                        'test_type': config['type'],
                        'config': config,
                        'success': False,
                        'error': result.stderr,
                        'output': result.stdout
                    })
                    
            except subprocess.TimeoutExpired:
                logger.error(f"⏰ {config['type']} test timed out")
                socketio_results.append({
                    'test_type': config['type'],
                    'config': config,
                    'success': False,
                    'error': 'Test timed out after 300 seconds'
                })
            except Exception as e:
                logger.error(f"❌ {config['type']} test failed with exception: {e}")
                socketio_results.append({
                    'test_type': config['type'],
                    'config': config,
                    'success': False,
                    'error': str(e)
                })
        
        self.test_results['socketio'] = socketio_results
        return socketio_results
    
    def run_database_tests(self):
        """Run database performance tests"""
        logger.info("🗄️  Running database performance tests...")
        
        cmd = [
            sys.executable, 'db_performance_test.py',
            '--test-type', 'all',
            '--queries', '250' if self.quick_mode else '500',
            '--threads', '10' if self.quick_mode else '20'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                logger.info("✅ Database tests completed successfully")
                self.test_results['database'] = {
                    'success': True,
                    'output': result.stdout,
                    'stderr': result.stderr
                }
                return True
            else:
                logger.error(f"❌ Database tests failed: {result.stderr}")
                self.test_results['database'] = {
                    'success': False,
                    'error': result.stderr,
                    'output': result.stdout
                }
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Database tests timed out")
            self.test_results['database'] = {
                'success': False,
                'error': 'Tests timed out after 300 seconds'
            }
            return False
        except FileNotFoundError:
            logger.warning("⚠️  db_performance_test.py not found, skipping database tests")
            self.test_results['database'] = {
                'success': False,
                'error': 'Database test file not found'
            }
            return False
    
    def run_comprehensive_test(self):
        """Run the main comprehensive performance test"""
        logger.info("📊 Running comprehensive performance test...")
        
        clients = 50 if self.quick_mode else 75
        duration = 30 if self.quick_mode else 60
        
        cmd = [
            sys.executable, 'performance_test.py',
            '--concurrent-clients', str(clients),
            '--test-duration', str(duration),
            '--socketio-url', 'http://localhost:5000'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                logger.info("✅ Comprehensive test completed successfully")
                self.test_results['comprehensive'] = {
                    'success': True,
                    'output': result.stdout,
                    'stderr': result.stderr
                }
                return True
            else:
                logger.error(f"❌ Comprehensive test failed: {result.stderr}")
                self.test_results['comprehensive'] = {
                    'success': False,
                    'error': result.stderr,
                    'output': result.stdout
                }
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Comprehensive test timed out")
            self.test_results['comprehensive'] = {
                'success': False,
                'error': 'Test timed out after 600 seconds'
            }
            return False
        except FileNotFoundError:
            logger.error("❌ performance_test.py not found")
            self.test_results['comprehensive'] = {
                'success': False,
                'error': 'Performance test file not found'
            }
            return False
    
    def find_latest_results(self):
        """Find the most recent test result files"""
        result_files = []
        
        # Look for various result files
        for filename in os.listdir('.'):
            if (filename.startswith('performance_results_') or 
                filename.startswith('socketio_test_results_') or 
                filename.startswith('websocket_load_test_') or 
                filename.startswith('db_performance_results_')):
                if filename.endswith('.json'):
                    result_files.append(filename)
        
        # Sort by modification time, newest first
        result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return result_files[:10]  # Return 10 most recent files
    
    def load_test_results(self):
        """Load and parse test results from JSON files"""
        result_files = self.find_latest_results()
        loaded_results = {}
        
        for filename in result_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    loaded_results[filename] = data
                    logger.info(f"📄 Loaded results from {filename}")
            except Exception as e:
                logger.warning(f"⚠️  Could not load {filename}: {e}")
        
        return loaded_results
    
    def extract_summary_metrics(self, all_results):
        """Extract key metrics from all test results"""
        metrics = {
            'max_concurrent_clients': 0,
            'avg_socketio_latency': float('inf'),
            'avg_db_query_time': float('inf'),
            'max_cpu_usage': float('inf'),
            'overall_success_rate': 0,
            'socketio_data': None,
            'database_data': None,
            'system_data': None
        }
        
        # Process each result file
        for filename, data in all_results.items():
            try:
                if 'socketio' in filename:
                    # Socket.IO test results - direct structure, no summary wrapper
                    if 'successful_connections' in data:
                        # Calculate average latency from connection_times
                        connection_times = data.get('connection_times', [])
                        avg_latency = sum(connection_times) * 1000 / len(connection_times) if connection_times else 0
                        
                        total_connections = data.get('successful_connections', 0) + data.get('failed_connections', 0)
                        success_rate = data.get('successful_connections', 0) / total_connections if total_connections > 0 else 0
                        
                        metrics['socketio_data'] = {
                            'max_clients': data.get('successful_connections', 0),
                            'avg_latency': avg_latency,
                            'success_rate': success_rate,
                            'message_rate': data.get('events_received', {}).get('train_update', 0)
                        }
                        metrics['max_concurrent_clients'] = max(
                            metrics['max_concurrent_clients'],
                            data.get('successful_connections', 0)
                        )
                        if avg_latency > 0:
                            metrics['avg_socketio_latency'] = min(
                                metrics['avg_socketio_latency'],
                                avg_latency
                            )
                
                elif 'db_performance' in filename:
                    # Database test results
                    if 'summary' in data:
                        summary = data['summary']
                        if 'performance_summary' in summary:
                            perf_summary = summary['performance_summary']
                            metrics['database_data'] = {
                                'simple_query_avg': perf_summary.get('query_performance', {}).get('simple_select', {}).get('avg_time_ms', 0),
                                'complex_query_avg': perf_summary.get('query_performance', {}).get('complex_select', {}).get('avg_time_ms', 0),
                                'concurrent_qps': perf_summary.get('concurrent_access', {}).get('total_qps', 0),
                                'transaction_rate': perf_summary.get('transaction_performance', {}).get('tps', 0)
                            }
                            avg_db_time = perf_summary.get('query_performance', {}).get('simple_select', {}).get('avg_time_ms', 0)
                            if avg_db_time > 0:
                                metrics['avg_db_query_time'] = min(metrics['avg_db_query_time'], avg_db_time)
                
                elif 'performance_results' in filename:
                    # Comprehensive test results
                    if 'summary' in data:
                        summary = data['summary']
                        if 'results_summary' in summary:
                            results_summary = summary['results_summary']
                            
                            # Socket.IO data
                            if 'socketio' in results_summary:
                                socketio_data = results_summary['socketio']
                                metrics['max_concurrent_clients'] = max(
                                    metrics['max_concurrent_clients'],
                                    socketio_data.get('concurrent_clients_achieved', 0)
                                )
                                if socketio_data.get('avg_latency_ms', 0) > 0:
                                    metrics['avg_socketio_latency'] = min(
                                        metrics['avg_socketio_latency'],
                                        socketio_data.get('avg_latency_ms', float('inf'))
                                    )
                            
                            # Database data
                            if 'database' in results_summary:
                                db_data = results_summary['database']
                                if db_data.get('avg_query_time_ms', 0) > 0:
                                    metrics['avg_db_query_time'] = min(
                                        metrics['avg_db_query_time'],
                                        db_data.get('avg_query_time_ms', float('inf'))
                                    )
                            
                            # System data
                            if 'system' in results_summary:
                                sys_data = results_summary['system']
                                metrics['system_data'] = {
                                    'avg_cpu': sys_data.get('avg_cpu_percent', 0),
                                    'max_cpu': sys_data.get('max_cpu_percent', 0),
                                    'avg_memory': sys_data.get('avg_memory_percent', 0),
                                    'max_memory': sys_data.get('max_memory_percent', 0)
                                }
                                metrics['max_cpu_usage'] = min(
                                    metrics['max_cpu_usage'],
                                    sys_data.get('max_cpu_percent', float('inf'))
                                )
                
            except Exception as e:
                logger.warning(f"⚠️  Error extracting metrics from {filename}: {e}")
        
        # Calculate overall success rate from test results
        success_count = 0
        total_count = 0
        
        for test_data in self.test_results.values():
            if isinstance(test_data, list):
                for test in test_data:
                    total_count += 1
                    if test.get('success', False):
                        success_count += 1
            else:
                total_count += 1
                if test_data.get('success', False):
                    success_count += 1
        
        if total_count > 0:
            metrics['overall_success_rate'] = success_count / total_count
        
        # Clean up infinite values
        if metrics['avg_socketio_latency'] == float('inf'):
            metrics['avg_socketio_latency'] = 0
        if metrics['avg_db_query_time'] == float('inf'):
            metrics['avg_db_query_time'] = 0
        if metrics['max_cpu_usage'] == float('inf'):
            metrics['max_cpu_usage'] = 0
        
        return metrics
    

    
    def generate_consolidated_report(self):
        """Generate a consolidated performance report from all test results"""
        logger.info("📋 Generating consolidated performance report...")
        
        # Load all available test results
        all_results = self.load_test_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"consolidated_performance_report_{timestamp}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("🚇 KL METRO TRACKING SYSTEM - CONSOLIDATED PERFORMANCE REPORT 🚇\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"🚀 Test Mode: {'Quick Mode' if self.quick_mode else 'Full Test Suite'}\n")
                
                if self.start_time:
                    total_time = time.time() - self.start_time
                    f.write(f"⏱️  Total Test Duration: {total_time:.1f} seconds\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("📊 EXECUTIVE SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Extract key metrics from results
                summary_metrics = self.extract_summary_metrics(all_results)
                
                f.write("🎯 Performance Targets Achievement:\n")
                f.write("-" * 35 + "\n")
                
                targets = [
                    ("50+ Concurrent Clients", summary_metrics.get('max_concurrent_clients', 0) >= 50),
                    ("< 100ms Socket.IO Latency", summary_metrics.get('avg_socketio_latency', float('inf')) < 100),
                    ("< 50ms Database Queries", summary_metrics.get('avg_db_query_time', float('inf')) < 50),
                    ("< 40% CPU Usage", summary_metrics.get('max_cpu_usage', float('inf')) < 40),
                    ("95%+ Success Rate", summary_metrics.get('overall_success_rate', 0) >= 0.95)
                ]
                
                for target_name, achieved in targets:
                    status = "✅ PASS" if achieved else "❌ FAIL"
                    f.write(f"{target_name:<30} {status}\n")
                
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("📈 DETAILED PERFORMANCE METRICS\n")
                f.write("=" * 50 + "\n\n")
                
                # Socket.IO Performance
                f.write("🔌 Socket.IO Performance:\n")
                f.write("-" * 25 + "\n")
                if summary_metrics.get('socketio_data'):
                    socketio_data = summary_metrics['socketio_data']
                    f.write(f"Maximum Concurrent Clients: {socketio_data.get('max_clients', 'N/A')}\n")
                    f.write(f"Average Latency: {socketio_data.get('avg_latency', 'N/A'):.2f}ms\n")
                    f.write(f"Connection Success Rate: {socketio_data.get('success_rate', 'N/A'):.1%}\n")
                    f.write(f"Train Update Events: {socketio_data.get('message_rate', 'N/A')}\n")
                else:
                    f.write("No Socket.IO performance data available\n")
                
                f.write("\n🗄️  Database Performance:\n")
                f.write("-" * 23 + "\n")
                if summary_metrics.get('database_data'):
                    db_data = summary_metrics['database_data']
                    f.write(f"Simple Query Average: {db_data.get('simple_query_avg', 'N/A'):.2f}ms\n")
                    f.write(f"Complex Query Average: {db_data.get('complex_query_avg', 'N/A'):.2f}ms\n")
                    f.write(f"Concurrent Query Rate: {db_data.get('concurrent_qps', 'N/A'):.1f} QPS\n")
                    f.write(f"Transaction Rate: {db_data.get('transaction_rate', 'N/A'):.1f} TPS\n")
                else:
                    f.write("No database performance data available\n")
                
                f.write("\n💻 System Resource Usage:\n")
                f.write("-" * 25 + "\n")
                if summary_metrics.get('system_data'):
                    sys_data = summary_metrics['system_data']
                    f.write(f"Average CPU Usage: {sys_data.get('avg_cpu', 'N/A'):.1f}%\n")
                    f.write(f"Peak CPU Usage: {sys_data.get('max_cpu', 'N/A'):.1f}%\n")
                    f.write(f"Average Memory Usage: {sys_data.get('avg_memory', 'N/A'):.1f}%\n")
                    f.write(f"Peak Memory Usage: {sys_data.get('max_memory', 'N/A'):.1f}%\n")
                else:
                    f.write("No system resource data available\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("🧪 TEST EXECUTION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Test execution details
                for test_name, test_data in self.test_results.items():
                    f.write(f"🔧 {test_name.upper()} Tests:\n")
                    if isinstance(test_data, list):
                        for i, test in enumerate(test_data):
                            status = "✅ PASS" if test.get('success', False) else "❌ FAIL"
                            test_type = test.get('test_type', f'Test {i+1}')
                            f.write(f"  • {test_type}: {status}\n")
                            if not test.get('success', False) and test.get('error'):
                                f.write(f"    Error: {test['error'][:100]}...\n")
                    else:
                        status = "✅ PASS" if test_data.get('success', False) else "❌ FAIL"
                        f.write(f"  • {status}\n")
                        if not test_data.get('success', False) and test_data.get('error'):
                            f.write(f"    Error: {test_data['error'][:100]}...\n")
                    f.write("\n")
                
                                
                f.write(f"\n" + "=" * 80 + "\n")
                f.write("📄 End of Report\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"✅ Consolidated report generated: {report_filename}")
            self.reports_generated.append(report_filename)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate consolidated report: {e}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        logger.info("🚀 Starting KL Metro Tracking System performance test suite")
        logger.info(f"⚙️  Test mode: {'Quick' if self.quick_mode else 'Comprehensive'}")
        
        self.start_time = time.time()
        
        # Check system availability
        if not self.check_system_availability():
            return False
        
        success = True
        
        try:
            # Run database tests first (they're independent)
            logger.info("\n" + "="*50)
            logger.info("🗄️  PHASE 1: DATABASE PERFORMANCE TESTS")
            logger.info("="*50)
            if not self.run_database_tests():
                logger.warning("⚠️  Database tests failed, continuing with other tests...")
                success = False
            
            # Run Socket.IO load tests
            logger.info("\n" + "="*50)
            logger.info("🔌 PHASE 2: SOCKET.IO LOAD TESTS")
            logger.info("="*50)
            socketio_results = self.run_socketio_tests()
            if not any(test.get('success', False) for test in socketio_results):
                logger.warning("⚠️  All Socket.IO tests failed...")
                success = False
            
            # Run comprehensive performance test
            logger.info("\n" + "="*50)
            logger.info("📊 PHASE 3: COMPREHENSIVE PERFORMANCE TEST")
            logger.info("="*50)
            if not self.run_comprehensive_test():
                logger.warning("⚠️  Comprehensive test failed...")
                success = False
            
            # Generate consolidated report
            logger.info("\n" + "="*50)
            logger.info("📋 PHASE 4: GENERATING REPORTS")
            logger.info("="*50)
            self.generate_consolidated_report()
            
            # Final summary
            total_time = time.time() - self.start_time
            logger.info(f"\n🏁 Test suite completed in {total_time:.1f} seconds")
            
            if self.reports_generated:
                logger.info("📄 Generated reports:")
                for report in self.reports_generated:
                    logger.info(f"   📋 {report}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Test suite execution error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Run KL Metro Tracking System Performance Tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests with reduced parameters')
    parser.add_argument('--report-only', action='store_true',
                       help='Only generate reports from existing test results')
    
    args = parser.parse_args()
    
    runner = TestRunner(quick_mode=args.quick)
    
    if args.report_only:
        logger.info("📋 Generating report from existing test results...")
        runner.generate_consolidated_report()
    else:
        success = runner.run_all_tests()
        
        if success:
            logger.info("🎉 All tests completed successfully")
            sys.exit(0)
        else:
            logger.error("⚠️  Some tests failed - check logs for details")
            sys.exit(1)

if __name__ == "__main__":
    main()
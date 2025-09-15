#!/usr/bin/env python3
"""
Test Runner Script for KL Metro Tracking System

Orchestrates the execution of all performance tests and generates
consolidated reports for academic documentation.

Usage: python run_tests.py [--quick] [--report-only]
"""

import asyncio
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
        import requests
        
        try:
            response = requests.get('http://localhost:5000', timeout=5)
            if response.status_code == 200:
                logger.info("Metro tracking system is running")
                return True
        except:
            pass
        
        logger.error("Metro tracking system is not accessible at http://localhost:5000")
        logger.error("Please start the system with: python app.py")
        return False
    
    def run_websocket_tests(self):
        """Run WebSocket load tests"""
        logger.info("Running WebSocket load tests...")
        
        test_configs = [
            {'type': 'burst', 'clients': 50 if self.quick_mode else 100, 'duration': 30 if self.quick_mode else 60},
            {'type': 'ramp', 'clients': 30 if self.quick_mode else 75, 'duration': 30 if self.quick_mode else 60, 'ramp_up': 10}
        ]
        
        if not self.quick_mode:
            test_configs.append({'type': 'endurance', 'clients': 20, 'duration': 180})
        
        websocket_results = []
        
        for config in test_configs:
            logger.info(f"Running {config['type']} test with {config['clients']} clients...")
            
            cmd = [
                sys.executable, 'websocket_load_test.py',
                '--test-type', config['type'],
                '--clients', str(config['clients']),
                '--duration', str(config['duration'])
            ]
            
            if 'ramp_up' in config:
                cmd.extend(['--ramp-up', str(config['ramp_up'])])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"{config['type']} test completed successfully")
                    websocket_results.append({
                        'test_type': config['type'],
                        'config': config,
                        'success': True,
                        'output': result.stdout
                    })
                else:
                    logger.error(f"{config['type']} test failed: {result.stderr}")
                    websocket_results.append({
                        'test_type': config['type'],
                        'config': config,
                        'success': False,
                        'error': result.stderr
                    })
                    
            except subprocess.TimeoutExpired:
                logger.error(f"{config['type']} test timed out")
                websocket_results.append({
                    'test_type': config['type'],
                    'config': config,
                    'success': False,
                    'error': 'Test timed out'
                })
        
        self.test_results['websocket'] = websocket_results
        return websocket_results
    
    def run_database_tests(self):
        """Run database performance tests"""
        logger.info("Running database performance tests...")
        
        cmd = [
            sys.executable, 'db_performance_test.py',
            '--test-type', 'all',
            '--queries', '500' if self.quick_mode else '1000',
            '--threads', '15' if self.quick_mode else '25'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Database tests completed successfully")
                self.test_results['database'] = {
                    'success': True,
                    'output': result.stdout
                }
                return True
            else:
                logger.error(f"Database tests failed: {result.stderr}")
                self.test_results['database'] = {
                    'success': False,
                    'error': result.stderr
                }
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Database tests timed out")
            self.test_results['database'] = {
                'success': False,
                'error': 'Tests timed out'
            }
            return False
    
    def run_comprehensive_test(self):
        """Run the main comprehensive performance test"""
        logger.info("Running comprehensive performance test...")
        
        clients = 75 if self.quick_mode else 100
        duration = 45 if self.quick_mode else 90
        
        cmd = [
            sys.executable, 'performance_test.py',
            '--concurrent-clients', str(clients),
            '--test-duration', str(duration)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("Comprehensive test completed successfully")
                self.test_results['comprehensive'] = {
                    'success': True,
                    'output': result.stdout
                }
                return True
            else:
                logger.error(f"Comprehensive test failed: {result.stderr}")
                self.test_results['comprehensive'] = {
                    'success': False,
                    'error': result.stderr
                }
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Comprehensive test timed out")
            self.test_results['comprehensive'] = {
                'success': False,
                'error': 'Test timed out'
            }
            return False
    
    def find_latest_results(self):
        """Find the most recent test result files"""
        result_files = []
        
        # Look for various result files
        for filename in os.listdir('.'):
            if (filename.startswith('performance_results_') or 
                filename.startswith('websocket_load_test_') or 
                filename.startswith('db_performance_results_')):
                if filename.endswith('.json'):
                    result_files.append(filename)
        
        # Sort by modification time, newest first
        result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return result_files[:5]  # Return 5 most recent files
    
    def load_test_results(self):
        """Load and parse test results from JSON files"""
        result_files = self.find_latest_results()
        loaded_results = {}
        
        for filename in result_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    loaded_results[filename] = data
                    logger.info(f"Loaded results from {filename}")
            except Exception as e:
                logger.warning(f"Could not load {filename}: {e}")
        
        return loaded_results
    
    def generate_consolidated_report(self):
        """Generate a consolidated performance report from all test results"""
        logger.info("Generating consolidated performance report...")
        
        # Load all available test results
        all_results = self.load_test_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"consolidated_performance_report_{timestamp}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("KL METRO TRACKING SYSTEM - CONSOLIDATED PERFORMANCE REPORT\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Test Mode: {'Quick Mode' if self.quick_mode else 'Full Test Suite'}\n")
                
                if self.start_time:
                    total_time = time.time() - self.start_time
                    f.write(f"Total Test Duration: {total_time:.1f} seconds\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("EXECUTIVE SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Extract key metrics from results
                summary_metrics = self.extract_summary_metrics(all_results)
                
                f.write("Performance Targets Achievement:\n")
                f.write("-" * 35 + "\n")
                
                targets = [
                    ("100+ Concurrent Clients", summary_metrics.get('max_concurrent_clients', 0) >= 100),
                    ("< 100ms WebSocket Latency", summary_metrics.get('avg_websocket_latency', float('inf')) < 100),
                    ("< 50ms Database Queries", summary_metrics.get('avg_db_query_time', float('inf')) < 50),
                    ("< 40% CPU Usage", summary_metrics.get('max_cpu_usage', float('inf')) < 40),
                    ("95%+ Success Rate", summary_metrics.get('overall_success_rate', 0) >= 0.95)
                ]
                
                for target_name, achieved in targets:
                    status = "PASS" if achieved else "FAIL"
                    f.write(f"{target_name:<30} {status}\n")
                
                f.write(f"\nOverall System Grade: {self.calculate_grade(targets)}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("DETAILED PERFORMANCE METRICS\n")
                f.write("=" * 50 + "\n\n")
                
                # WebSocket Performance
                f.write("WebSocket Performance:\n")
                f.write("-" * 25 + "\n")
                if summary_metrics.get('websocket_data'):
                    ws_data = summary_metrics['websocket_data']
                    f.write(f"Maximum Concurrent Clients: {ws_data.get('max_clients', 'N/A')}\n")
                    f.write(f"Average Latency: {ws_data.get('avg_latency', 'N/A'):.2f}ms\n")
                    f.write(f"95th Percentile Latency: {ws_data.get('p95_latency', 'N/A'):.2f}ms\n")
                    f.write(f"Connection Success Rate: {ws_data.get('success_rate', 'N/A'):.1%}\n")
                    f.write(f"Message Throughput: {ws_data.get('message_rate', 'N/A'):.1f} msg/sec\n")
                else:
                    f.write("No WebSocket performance data available\n")
                
                f.write("\nDatabase Performance:\n")
                f.write("-" * 23 + "\n")
                if summary_metrics.get('database_data'):
                    db_data = summary_metrics['database_data']
                    f.write(f"Simple Query Average: {db_data.get('simple_query_avg', 'N/A'):.2f}ms\n")
                    f.write(f"Complex Query Average: {db_data.get('complex_query_avg', 'N/A'):.2f}ms\n")
                    f.write(f"Concurrent Query Rate: {db_data.get('concurrent_qps', 'N/A'):.1f} QPS\n")
                    f.write(f"Transaction Rate: {db_data.get('transaction_rate', 'N/A'):.1f} TPS\n")
                else:
                    f.write("No database performance data available\n")
                
                f.write("\nSystem Resource Usage:\n")
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
                f.write("TEST EXECUTION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Test execution details
                for test_name, test_data in self.test_results.items():
                    f.write(f"{test_name.upper()} Tests:\n")
                    if isinstance(test_data, list):
                        for i, test in enumerate(test_data):
                            status = "PASS" if test.get('success', False) else "FAIL"
                            test_type = test.get('test_type', f'Test {i+1}')
                            f.write(f"  {test_type}: {status}\n")
                    else:
                        status = "PASS" if test_data.get('success', False) else "FAIL"
                        f.write(f"  {status}\n")
                    f.write("\n")
                
                f.write("=" * 50 + "\n")
                f.write("RECOMMENDATIONS\n")
                f.write("=" * 50 + "\n\n")
                
                recommendations = self.generate_recommendations(summary_metrics, targets)
                for rec in recommendations:
                    f.write(f"- {rec}\n")
                
                f.write(f"\n" + "=" * 80 + "\n")
                f.write("End of Report\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"Consolidated report generated: {report_filename}")
            self.reports_generated.append(report_filename)
            
        except Exception as e:
            logger.error(f"Failed to generate consolidated report: {e}")
    
    def extract_summary_metrics(self, all_results):
        """Extract key metrics from all test results"""
        metrics = {}
        
        # Process each result file
        for filename, data in all_results.items():
            try:
                if 'websocket' in filename:
                    # WebSocket test results
                    if 'summary' in data:
                        summary = data['summary']
                        metrics['websocket_data'] = {
                            'max_clients': summary.get('successful_clients', 0),
                            'avg_latency': summary.get('avg_latency_ms', 0),
                            'p95_latency': summary.get('latency_stats', {}).get('p95_latency_ms', 0),
                            'success_rate': summary.get('connection_success_rate', 0),
                            'message_rate': summary.get('total_messages_received', 0) / summary.get('total_time_s', 1) if summary.get('total_time_s', 0) > 0 else 0
                        }
                
                elif 'db_performance' in filename:
                    # Database test results
                    if 'summary' in data and 'performance_summary' in data['summary']:
                        perf_summary = data['summary']['performance_summary']
                        metrics['database_data'] = {
                            'simple_query_avg': perf_summary.get('query_performance', {}).get('simple_select', {}).get('avg_time_ms', 0),
                            'complex_query_avg': perf_summary.get('query_performance', {}).get('complex_select', {}).get('avg_time_ms', 0),
                            'concurrent_qps': perf_summary.get('concurrent_access', {}).get('total_qps', 0),
                            'transaction_rate': perf_summary.get('transaction_performance', {}).get('tps', 0)
                        }
                
                elif 'performance_results' in filename:
                    # Comprehensive test results
                    if 'summary' in data and 'results_summary' in data['summary']:
                        results_summary = data['summary']['results_summary']
                        
                        # WebSocket data
                        if 'websocket' in results_summary:
                            ws_data = results_summary['websocket']
                            metrics['max_concurrent_clients'] = ws_data.get('concurrent_clients_achieved', 0)
                            metrics['avg_websocket_latency'] = ws_data.get('avg_latency_ms', 0)
                        
                        # Database data
                        if 'database' in results_summary:
                            db_data = results_summary['database']
                            metrics['avg_db_query_time'] = db_data.get('avg_query_time_ms', 0)
                        
                        # System data
                        if 'system' in results_summary:
                            sys_data = results_summary['system']
                            metrics['system_data'] = {
                                'avg_cpu': sys_data.get('avg_cpu_percent', 0),
                                'max_cpu': sys_data.get('max_cpu_percent', 0),
                                'avg_memory': sys_data.get('avg_memory_percent', 0),
                                'max_memory': sys_data.get('max_memory_percent', 0)
                            }
                            metrics['max_cpu_usage'] = sys_data.get('max_cpu_percent', 0)
                
            except Exception as e:
                logger.warning(f"Error extracting metrics from {filename}: {e}")
        
        # Calculate overall success rate
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
        
        return metrics
    
    def calculate_grade(self, targets):
        """Calculate overall system performance grade"""
        passed = sum(1 for _, achieved in targets if achieved)
        total = len(targets)
        
        percentage = (passed / total) * 100
        
        if percentage >= 90:
            return "A (Excellent)"
        elif percentage >= 80:
            return "B (Good)"
        elif percentage >= 70:
            return "C (Satisfactory)"
        elif percentage >= 60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"
    
    def generate_recommendations(self, metrics, targets):
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check each target and provide recommendations
        if metrics.get('max_concurrent_clients', 0) < 100:
            recommendations.append("Optimize WebSocket connection handling to support more concurrent clients")
        
        if metrics.get('avg_websocket_latency', float('inf')) >= 100:
            recommendations.append("Reduce WebSocket message processing latency through code optimization")
        
        if metrics.get('avg_db_query_time', float('inf')) >= 50:
            recommendations.append("Add database indexes and optimize SQL queries for better performance")
        
        if metrics.get('max_cpu_usage', float('inf')) >= 40:
            recommendations.append("Optimize CPU-intensive operations and consider code profiling")
        
        if metrics.get('overall_success_rate', 1) < 0.95:
            recommendations.append("Improve error handling and system stability")
        
        # Add general recommendations
        recommendations.extend([
            "Consider implementing connection pooling for database access",
            "Monitor system performance in production environment",
            "Implement caching mechanisms for frequently accessed data",
            "Consider horizontal scaling for higher load requirements"
        ])
        
        return recommendations
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        logger.info("Starting KL Metro Tracking System performance test suite")
        logger.info(f"Test mode: {'Quick' if self.quick_mode else 'Comprehensive'}")
        
        self.start_time = time.time()
        
        # Check system availability
        if not self.check_system_availability():
            return False
        
        success = True
        
        try:
            # Run database tests first (they're independent)
            if not self.run_database_tests():
                success = False
            
            # Run WebSocket load tests
            self.run_websocket_tests()
            
            # Run comprehensive performance test
            if not self.run_comprehensive_test():
                success = False
            
            # Generate consolidated report
            self.generate_consolidated_report()
            
            # Final summary
            total_time = time.time() - self.start_time
            logger.info(f"\nTest suite completed in {total_time:.1f} seconds")
            
            if self.reports_generated:
                logger.info("Generated reports:")
                for report in self.reports_generated:
                    logger.info(f"  - {report}")
            
            return success
            
        except Exception as e:
            logger.error(f"Test suite execution error: {e}")
            return False

async def main():
    parser = argparse.ArgumentParser(description='Run KL Metro Tracking System Performance Tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests with reduced parameters')
    parser.add_argument('--report-only', action='store_true',
                       help='Only generate reports from existing test results')
    
    args = parser.parse_args()
    
    runner = TestRunner(quick_mode=args.quick)
    
    if args.report_only:
        logger.info("Generating report from existing test results...")
        runner.generate_consolidated_report()
    else:
        success = await runner.run_all_tests()
        
        if success:
            logger.info("All tests completed successfully")
            sys.exit(0)
        else:
            logger.error("Some tests failed")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

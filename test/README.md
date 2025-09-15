# Test Suite for KL Metro Tracking System

This directory contains comprehensive performance testing scripts for the KL Metro Tracking System.

## Test Scripts

### 1. `performance_test.py` - Comprehensive Performance Test
Main test script that runs all performance tests including WebSocket load testing, database performance, API testing, and system resource monitoring.

**Features:**
- WebSocket concurrent connection testing (up to 100+ clients)
- Database query performance measurement
- REST API response time testing
- Real-time system resource monitoring
- Automated performance target evaluation

**Usage:**
```bash
# Run with default settings (100 concurrent clients, 60 seconds)
python performance_test.py

# Custom test parameters
python performance_test.py --concurrent-clients 150 --test-duration 120

# Different server endpoints
python performance_test.py --base-url http://localhost:8000 --ws-url ws://localhost:8000/ws
```

**Performance Targets:**
- 100+ concurrent WebSocket clients
- <100ms average latency
- <50ms database query time
- <40% CPU usage under load

### 2. `websocket_load_test.py` - WebSocket Load Testing
Specialized WebSocket testing with different load patterns.

**Test Types:**
- **Burst Test**: Start all clients simultaneously
- **Ramp Test**: Gradually increase client connections
- **Endurance Test**: Long-running stability test

**Usage:**
```bash
# Burst test with 50 clients for 30 seconds
python websocket_load_test.py --test-type burst --clients 50 --duration 30

# Ramp-up test (10 second ramp-up period)
python websocket_load_test.py --test-type ramp --clients 100 --duration 60 --ramp-up 10

# Endurance test for stability
python websocket_load_test.py --test-type endurance --clients 25 --duration 300
```

**Metrics Measured:**
- Connection establishment time
- Message latency (P95, P99 percentiles)
- Message loss rate
- Connection success rate
- Session duration statistics

### 3. `db_performance_test.py` - Database Performance Testing
Comprehensive SQLite database performance testing.

**Test Categories:**
- **Query Performance**: Simple, medium, and complex SELECT queries
- **Concurrent Access**: Multiple threads accessing database simultaneously
- **Transaction Performance**: Batch operations and transaction throughput
- **Index Performance**: Query optimization validation

**Usage:**
```bash
# Run all database tests
python db_performance_test.py --test-type all

# Test only query performance
python db_performance_test.py --test-type query --queries 1000

# Test concurrent access
python db_performance_test.py --test-type concurrent --threads 30

# Custom database path
python db_performance_test.py --db-path /path/to/your/database.db
```

**Query Types Tested:**
- Simple: Basic SELECT, COUNT operations
- Medium: JOINs, GROUP BY, filtering
- Complex: Multi-table JOINs, subqueries, aggregations

## Running Tests

### Prerequisites
Make sure the KL Metro Tracking System is running before executing tests:

```bash
# Start the metro tracking system
cd metro-tracking-system
python app.py
```

### Quick Start
Run the comprehensive test suite:

```bash
cd test
python performance_test.py
```

### Test Environment Setup
Install required dependencies:

```bash
pip install websockets psutil requests
```

## Test Results

### Output Files
Tests generate several output files:

1. **JSON Results**: `performance_results_YYYYMMDD_HHMMSS.json`
   - Raw test data and detailed metrics
   - Machine-readable format for analysis

2. **Summary Reports**: `performance_report_YYYYMMDD_HHMMSS.txt`
   - Human-readable performance summary
   - Target evaluation (✓/✗ indicators)
   - Key performance indicators

3. **Log Files**: `performance_test.log`
   - Detailed execution logs
   - Error messages and debugging information

### Sample Output
```
=== KL Metro Tracking System Performance Test Report ===

Test Date: 2024-01-15T14:30:25.123456
Total Duration: 125.67 seconds

WebSocket Performance:
  - Concurrent Clients: 105
  - Average Latency: 85.23ms
  - Success Rate: 98.1%
  - Meets Targets: Latency=✓, Concurrency=✓

Database Performance:
  - Average Query Time: 42.15ms
  - Queries Completed: 1000
  - Meets Target: ✓

Performance Targets:
  - 100 concurrent clients: ✓
  - <100ms latency: ✓
  - <50ms DB queries: ✓
  - <40% CPU usage: ✓
```

## Performance Targets

The test suite evaluates against these performance targets:

| Metric | Target | Purpose |
|--------|--------|---------|
| Concurrent Clients | 100+ | Real-time user capacity |
| WebSocket Latency | <100ms | Real-time responsiveness |
| Database Queries | <50ms | System responsiveness |
| CPU Usage | <40% | Resource efficiency |
| Memory Usage | <2GB | Resource efficiency |

## Interpreting Results

### WebSocket Performance
- **Connection Success Rate**: Should be >95% for reliable service
- **Average Latency**: <100ms for good user experience
- **P95/P99 Latency**: Shows performance consistency
- **Message Loss Rate**: Should be <1% for reliable communication

### Database Performance
- **Query Time**: Different complexity levels should meet targets
- **Queries Per Second (QPS)**: Higher is better for throughput
- **Concurrent Access**: Tests database locking and concurrency
- **Transaction Performance**: Measures batch operation efficiency

### System Resources
- **CPU Usage**: Should remain reasonable under load
- **Memory Usage**: Should not show memory leaks
- **Resource Trends**: Monitor for performance degradation over time

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Ensure the metro tracking system is running
   - Check if ports 5000 is available
   - Verify WebSocket endpoint accessibility

2. **Database Errors**
   - Check database file path and permissions
   - Ensure database is not locked by another process
   - Verify database schema is properly initialized

3. **Performance Issues**
   - High CPU usage may indicate system bottlenecks
   - High memory usage could suggest memory leaks
   - Network latency affects WebSocket performance

### Debug Mode
Enable debug logging for detailed troubleshooting:

```bash
# Set logging level to DEBUG
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python performance_test.py
```

## Integration with Academic Reports

The test results provide data for academic report sections:

### Performance Analysis Section
- Use WebSocket latency statistics for real-time performance claims
- Include concurrent client capacity for scalability analysis
- Database performance metrics for system efficiency evaluation

### System Architecture Section
- Connection establishment times validate architecture decisions
- Resource usage patterns support design choices
- Scalability test results demonstrate system capabilities

### Technical Implementation Section
- Query performance validates database design
- Transaction performance shows data consistency approach
- Error rates demonstrate system reliability

## Continuous Testing

For ongoing development, consider:

1. **Automated Testing**: Integrate tests into CI/CD pipeline
2. **Performance Regression**: Compare results over time
3. **Load Profiles**: Test with realistic usage patterns
4. **Stress Testing**: Find system breaking points

## Advanced Usage

### Custom Test Scenarios
Modify test scripts for specific scenarios:

```python
# Custom WebSocket test
test = WebSocketLoadTest()
await test.burst_test(clients=200, duration=300)

# Custom database test
db_test = DatabasePerformanceTest()
db_test.test_concurrent_access(threads=50, queries_per_thread=100)
```

### Performance Monitoring
Set up continuous monitoring:

```bash
# Monitor system during tests
python performance_test.py --concurrent-clients 100 --test-duration 600
```

This comprehensive test suite provides all the performance data needed for academic reports and system validation.

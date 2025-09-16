"""
Metro Tracking System - Multicast Client Demo
Demonstrates various multicast client implementations for receiving real-time train updates

This demo showcases different client types:
1. Basic Train Monitor - Receives all train updates
2. Line-Specific Monitor - Filters trains by metro line
3. Alert Monitor - Focuses on system alerts and disruptions
4. Performance Monitor - Measures latency and connection quality
"""

import socket
import struct
import pickle
import threading
import time
import json
from datetime import datetime
import signal
import sys

# Multicast configuration (matches metro system)
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 9001

class MetroMulticastClient:
    """
    Base class for metro multicast clients
    Inspired by Lab2/Multicast examples with enhanced features
    """
    
    def __init__(self, client_name="Metro Client", zone_filter="all"):
        self.client_name = client_name
        self.zone_filter = zone_filter
        self.socket = None
        self.running = False
        self.received_count = 0
        self.start_time = None
        
    def setup_socket(self):
        """Setup multicast socket for receiving updates"""
        try:
            # Create UDP socket for multicast
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to multicast port
            self.socket.bind(('', MULTICAST_PORT))
            
            # Join multicast group
            mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            print(f"🔌 {self.client_name} connected to multicast group {MULTICAST_GROUP}:{MULTICAST_PORT}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up socket for {self.client_name}: {e}")
            return False
    
    def start_listening(self):
        """Start listening for multicast messages"""
        if not self.setup_socket():
            return
            
        print(f"👂 {self.client_name} listening for updates (filter: {self.zone_filter})")
        print("   Press Ctrl+C to stop...")
        
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                try:
                    # Receive multicast data
                    data, addr = self.socket.recvfrom(1024)
                    self.received_count += 1
                    
                    # Deserialize message
                    message = pickle.loads(data)
                    
                    # Apply filtering and process
                    if self.should_process(message):
                        self.process_message(message)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"⚠️  Error receiving data: {e}")
                        
        except KeyboardInterrupt:
            print(f"\n🛑 {self.client_name} stopping...")
        finally:
            self.stop()
    
    def should_process(self, message):
        """Check if message should be processed based on filters"""
        # Basic zone/line filtering
        if self.zone_filter == "all":
            return True
            
        # Check zone match
        msg_zone = message.get('zone', '')
        if msg_zone == self.zone_filter:
            return True
            
        # Check line match for train updates
        if message.get('type') == 'TRAIN_UPDATE':
            # This would need enhancement with actual line data from database
            return True
            
        return False
    
    def process_message(self, message):
        """Process received message - override in subclasses"""
        msg_type = message.get('type', 'UNKNOWN')
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        print(f"[{timestamp}] {self.client_name}: {msg_type} - {message}")
    
    def stop(self):
        """Stop listening and cleanup"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Show statistics
        if self.start_time:
            duration = time.time() - self.start_time
            rate = self.received_count / duration if duration > 0 else 0
            print(f"📊 {self.client_name} Statistics:")
            print(f"   Total messages: {self.received_count}")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Rate: {rate:.2f} msg/sec")

class BasicTrainMonitor(MetroMulticastClient):
    """
    Basic train position monitor
    Shows all train movements in a clean format
    """
    
    def __init__(self):
        super().__init__("Basic Train Monitor", "all")
        self.train_positions = {}
    
    def process_message(self, message):
        """Process train updates with enhanced display"""
        if message.get('type') == 'TRAIN_UPDATE':
            train_id = message.get('train_id')
            station_name = message.get('station_name')
            timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
            
            # Track previous position for movement detection
            prev_station = self.train_positions.get(train_id, {}).get('station_name')
            self.train_positions[train_id] = message
            
            # Display with movement indication
            movement = "" if prev_station == station_name else f" (from {prev_station})" if prev_station else ""
            print(f"🚊 [{timestamp}] Train {train_id} at {station_name}{movement}")
            
        elif message.get('type') == 'SYSTEM':
            timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
            severity = message.get('severity', 1)
            severity_icon = "🔴" if severity >= 4 else "🟡" if severity >= 2 else "🟢"
            print(f"{severity_icon} [{timestamp}] ALERT: {message.get('message', 'System alert')}")

class LineSpecificMonitor(MetroMulticastClient):
    """
    Monitor trains on specific metro lines (KJL, SBK, etc.)
    Demonstrates zone-based filtering like Lab2 examples
    """
    
    def __init__(self, line_filter="KJL"):
        super().__init__(f"Line {line_filter} Monitor", line_filter)
        self.line_filter = line_filter
        self.line_trains = set()
    
    def should_process(self, message):
        """Enhanced filtering for specific metro lines"""
        if message.get('type') == 'TRAIN_UPDATE':
            station_name = message.get('station_name', '')
            # Simple line detection - could be enhanced with database lookup
            if self.line_filter == "KJL" and ("KJL" in station_name or any(kw in station_name for kw in ["Kelana", "Subang", "Bangsar", "Sentral"])):
                return True
            elif self.line_filter == "SBK" and ("SBK" in station_name or any(kw in station_name for kw in ["Kajang", "Sungai", "Bandar"])):
                return True
                
        return message.get('type') != 'TRAIN_UPDATE'  # Show all non-train messages
    
    def process_message(self, message):
        """Process line-specific updates"""
        if message.get('type') == 'TRAIN_UPDATE':
            train_id = message.get('train_id')
            station_name = message.get('station_name')
            timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
            
            self.line_trains.add(train_id)
            print(f"🚇 [{timestamp}] {self.line_filter} Line - Train {train_id} → {station_name}")
            print(f"   Active trains on {self.line_filter}: {sorted(self.line_trains)}")
        else:
            super().process_message(message)

class AlertMonitor(MetroMulticastClient):
    """
    Specialized monitor for system alerts and disruptions
    Similar to Lab2 alert filtering with severity levels
    """
    
    def __init__(self, min_severity=1):
        super().__init__(f"Alert Monitor (≥{min_severity})", "all")
        self.min_severity = min_severity
        self.alert_count = 0
    
    def should_process(self, message):
        """Filter by alert type and severity"""
        if message.get('type') in ['SYSTEM', 'ALERT', 'MAINTENANCE']:
            return message.get('severity', 1) >= self.min_severity
        return False
    
    def process_message(self, message):
        """Process alerts with detailed information"""
        self.alert_count += 1
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        severity = message.get('severity', 1)
        msg_text = message.get('message', 'Alert')
        zone = message.get('zone', 'all')
        
        # Severity visualization
        severity_map = {5: "🔴 CRITICAL", 4: "🟠 HIGH", 3: "🟡 MEDIUM", 2: "🔵 LOW", 1: "🟢 INFO"}
        severity_str = severity_map.get(severity, f"⚪ LEVEL-{severity}")
        
        print(f"{severity_str} [{timestamp}] Zone: {zone}")
        print(f"  📢 {msg_text}")
        print(f"  📊 Alert #{self.alert_count} (Total alerts received)")

class PerformanceMonitor(MetroMulticastClient):
    """
    Monitor for measuring multicast performance and latency
    Useful for system diagnostics and optimization
    """
    
    def __init__(self):
        super().__init__("Performance Monitor", "all")
        self.latencies = []
        self.message_types = {}
    
    def process_message(self, message):
        """Analyze message performance metrics"""
        current_time = time.time()
        msg_timestamp = message.get('timestamp', current_time)
        msg_type = message.get('type', 'UNKNOWN')
        
        # Calculate latency (if message timestamp is recent)
        latency = current_time - msg_timestamp
        if latency < 60:  # Only track latencies under 1 minute
            self.latencies.append(latency)
        
        # Count message types
        self.message_types[msg_type] = self.message_types.get(msg_type, 0) + 1
        
        # Periodic performance report
        if self.received_count % 10 == 0:
            self.show_performance_stats()
    
    def show_performance_stats(self):
        """Display current performance statistics"""
        if not self.latencies:
            return
            
        avg_latency = sum(self.latencies) / len(self.latencies)
        max_latency = max(self.latencies)
        min_latency = min(self.latencies)
        
        print(f"\n📈 Performance Stats (after {self.received_count} messages):")
        print(f"   Latency: avg={avg_latency*1000:.1f}ms, min={min_latency*1000:.1f}ms, max={max_latency*1000:.1f}ms")
        print(f"   Message types: {dict(self.message_types)}")
        print()

def demo_menu():
    """Interactive demo menu for selecting client type"""
    print("🚇 Metro Tracking System - Multicast Client Demo")
    print("=" * 50)
    print("Choose a demo client:")
    print("1. Basic Train Monitor - See all train movements")
    print("2. KJL Line Monitor - Only Kelana Jaya Line trains")
    print("3. SBK Line Monitor - Only Sungai Buloh-Kajang Line trains") 
    print("4. Alert Monitor - System alerts and disruptions")
    print("5. Performance Monitor - Latency and performance stats")
    print("6. Multi-Client Demo - Run multiple clients in parallel")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-6): ").strip()
        return choice
    except KeyboardInterrupt:
        return "0"

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n👋 Demo interrupted by user")
    sys.exit(0)

def run_multi_client_demo():
    """Run multiple clients in parallel threads"""
    print("🔄 Starting Multi-Client Demo...")
    print("   This runs multiple client types simultaneously")
    
    clients = [
        BasicTrainMonitor(),
        LineSpecificMonitor("KJL"),
        AlertMonitor(2)  # Medium severity and above
    ]
    
    threads = []
    
    try:
        # Start each client in its own thread
        for client in clients:
            thread = threading.Thread(target=client.start_listening, daemon=True)
            thread.start()
            threads.append(thread)
            time.sleep(0.5)  # Stagger startup
        
        print("\n✅ All clients started. Press Ctrl+C to stop all clients...")
        
        # Wait for keyboard interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all clients...")
        for client in clients:
            client.stop()
        
def main():
    """Main demo function"""
    # Setup signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        choice = demo_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            BasicTrainMonitor().start_listening()
        elif choice == "2":
            LineSpecificMonitor("KJL").start_listening()
        elif choice == "3":
            LineSpecificMonitor("SBK").start_listening()
        elif choice == "4":
            severity = input("Enter minimum alert severity (1-5, default=1): ").strip()
            try:
                severity = int(severity) if severity else 1
                AlertMonitor(severity).start_listening()
            except ValueError:
                AlertMonitor(1).start_listening()
        elif choice == "5":
            PerformanceMonitor().start_listening()
        elif choice == "6":
            run_multi_client_demo()
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    print("📡 Starting Metro Multicast Client Demo...")
    print("💡 Make sure the metro tracking system is running for live data!")
    print("   (Start with: python app.py in the metro-tracking-system folder)")
    print()
    
    main()
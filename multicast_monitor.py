"""
Multicast Client for Real-Time Metro Tracking System
Inspired by Lab2/Multicast exercises - demonstrates external system integration
"""

import socket
import struct
import pickle
import time
import threading
from datetime import datetime

# Multicast configuration (must match server settings)
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 9001

class MetroMulticastMonitor:
    """
    Multicast monitor client (inspired by Lab2/Multicast/Q1Client1.py)
    Demonstrates how external systems can monitor metro updates
    """
    
    def __init__(self, zone_filter='all', train_filter=None):
        self.zone_filter = zone_filter
        self.train_filter = train_filter  # Filter specific train IDs
        self.socket = None
        self.running = False
        self.stats = {
            'messages_received': 0,
            'train_updates': 0,
            'system_alerts': 0,
            'start_time': None
        }
        
    def start_monitoring(self):
        """Start monitoring multicast train updates"""
        print("="*60)
        print("METRO MULTICAST MONITOR")
        print("="*60)
        print(f"Monitoring Group: {MULTICAST_GROUP}:{MULTICAST_PORT}")
        print(f"Zone Filter: {self.zone_filter}")
        print(f"Train Filter: {self.train_filter or 'All trains'}")
        print("="*60)
        
        try:
            # Create and configure socket (similar to Lab2 client)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', MULTICAST_PORT))
            
            # Join multicast group
            mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            print("✅ Successfully joined multicast group")
            print("📡 Listening for metro updates...\n")
            
            self.running = True
            self.stats['start_time'] = time.time()
            
            # Start statistics thread
            stats_thread = threading.Thread(target=self.print_periodic_stats, daemon=True)
            stats_thread.start()
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(4096)
                    self.stats['messages_received'] += 1
                    
                    # Deserialize message
                    message = pickle.loads(data)
                    
                    # Apply filters and process
                    if self.should_process_message(message):
                        self.process_message(message)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving data: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"❌ Error starting multicast monitor: {e}")
            
    def should_process_message(self, message):
        """Check if message should be processed based on filters"""
        # Zone filter
        if self.zone_filter != 'all':
            message_zone = message.get('zone', 'unknown')
            if message_zone != self.zone_filter:
                return False
        
        # Train filter
        if self.train_filter is not None:
            if message.get('type') == 'TRAIN_UPDATE':
                train_id = message.get('train_id')
                if train_id not in self.train_filter:
                    return False
        
        return True
    
    def process_message(self, message):
        """Process received metro update message"""
        msg_type = message.get('type', 'UNKNOWN')
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time()))
        
        if msg_type == 'TRAIN_UPDATE':
            self.stats['train_updates'] += 1
            self.process_train_update(message, timestamp)
            
        elif msg_type in ['SYSTEM', 'SYSTEM_WARNING', 'MAINTENANCE', 'TRAFFIC', 'INFO']:
            self.stats['system_alerts'] += 1
            self.process_system_alert(message, timestamp)
            
        else:
            print(f"🔍 [UNKNOWN] {msg_type}: {message}")
    
    def process_train_update(self, message, timestamp):
        """Process train position update"""
        train_id = message.get('train_id', 'N/A')
        station_id = message.get('station_id', 'N/A')
        station_name = message.get('station_name', 'Unknown Station')
        latitude = message.get('latitude', 0)
        longitude = message.get('longitude', 0)
        
        print(f"🚇 [TRAIN UPDATE] {timestamp.strftime('%H:%M:%S')}")
        print(f"   Train {train_id} arrived at {station_name} (Station {station_id})")
        print(f"   Location: {latitude:.4f}, {longitude:.4f}")
        
        # Additional data if available
        if 'line' in message:
            print(f"   Line: {message['line']}")
        if 'previous_station_id' in message:
            print(f"   From Station: {message['previous_station_id']}")
        
        print()
    
    def process_system_alert(self, message, timestamp):
        """Process system alert message"""
        severity = message.get('severity', 1)
        alert_message = message.get('message', 'No message')
        zone = message.get('zone', 'system')
        
        # Choose icon based on severity
        icon = "ℹ️" if severity == 1 else "⚠️" if severity == 2 else "🚨"
        
        print(f"{icon} [SYSTEM ALERT] {timestamp.strftime('%H:%M:%S')}")
        print(f"   Severity: {severity}/3")
        print(f"   Zone: {zone}")
        print(f"   Message: {alert_message}")
        print()
    
    def print_periodic_stats(self):
        """Print statistics periodically"""
        while self.running:
            time.sleep(30)  # Print stats every 30 seconds
            if self.running:
                self.print_stats()
    
    def print_stats(self):
        """Print current monitoring statistics"""
        if self.stats['start_time']:
            runtime = time.time() - self.stats['start_time']
            rate = self.stats['messages_received'] / runtime if runtime > 0 else 0
            
            print("📊 MONITORING STATISTICS")
            print(f"   Runtime: {runtime:.0f} seconds")
            print(f"   Total Messages: {self.stats['messages_received']}")
            print(f"   Train Updates: {self.stats['train_updates']}")
            print(f"   System Alerts: {self.stats['system_alerts']}")
            print(f"   Message Rate: {rate:.2f} msg/sec")
            print("-" * 40)
    
    def stop_monitoring(self):
        """Stop monitoring gracefully"""
        print("\n🛑 Stopping multicast monitor...")
        self.running = False
        
        if self.socket:
            try:
                # Leave multicast group
                mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
                self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
                self.socket.close()
            except:
                pass
        
        self.print_stats()
        print("✅ Monitor stopped successfully")

class ZoneSpecificMonitor(MetroMulticastMonitor):
    """
    Zone-specific monitor (inspired by Lab2 zone filtering)
    Example of specialized monitoring for specific areas
    """
    
    def __init__(self, zone='North'):
        super().__init__(zone_filter=zone)
        self.zone_trains = set()
        
    def process_train_update(self, message, timestamp):
        """Enhanced processing for zone-specific monitoring"""
        train_id = message.get('train_id')
        self.zone_trains.add(train_id)
        
        # Call parent method
        super().process_train_update(message, timestamp)
        
        # Additional zone-specific logic
        print(f"   📍 Zone '{self.zone_filter}' now tracking {len(self.zone_trains)} trains")
        print()

def main():
    """Main function to demonstrate multicast monitoring"""
    import sys
    import signal
    
    print("Real-Time Metro Multicast Monitor")
    print("Inspired by Lab2 Multicast exercises")
    print()
    
    # Parse command line arguments
    zone_filter = 'all'
    train_filter = None
    
    if len(sys.argv) > 1:
        zone_filter = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            train_filter = [int(x) for x in sys.argv[2].split(',')]
        except ValueError:
            print("Invalid train filter format. Use comma-separated integers.")
            return
    
    # Create monitor
    if zone_filter in ['North', 'South', 'East', 'West', 'Central']:
        monitor = ZoneSpecificMonitor(zone_filter)
    else:
        monitor = MetroMulticastMonitor(zone_filter, train_filter)
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        monitor.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()

if __name__ == '__main__':
    main()

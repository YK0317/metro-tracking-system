"""
Enhanced Real-time Module with Multicast Support
Incorporates concepts from Lab2 multicast exercises for efficient broadcasting
"""

from flask_socketio import emit, disconnect
from database import get_all_trains_enhanced
import socket
import struct
import threading
import json
import time
import pickle

# Multicast configuration (inspired by Lab2/Multicast)
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 9001

class EnhancedRealtime:
    def __init__(self):
        self.multicast_socket = None
        self.websocket_clients = []
        self.broadcast_modes = ['websocket', 'multicast']
        self.init_multicast()
    
    def init_multicast(self):
        """Initialize multicast socket for efficient train updates broadcasting"""
        try:
            self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            print("Multicast socket initialized successfully")
        except Exception as e:
            print(f"Failed to initialize multicast socket: {e}")
            self.multicast_socket = None

def init_realtime(socketio):
    """Initialize WebSocket event handlers with enhanced features"""
    enhanced_rt = EnhancedRealtime()
    
    @socketio.on('connect')
    def handle_connect():
        """Enhanced connection handler with client tracking"""
        client_id = getattr(socketio, 'client_id', 'unknown')
        print(f'Client {client_id} connected to WebSocket')
        
        # Track connected clients (concept from Lab2 client management)
        enhanced_rt.websocket_clients.append(client_id)
        
        # Send initial train positions with error handling
        try:
            trains = get_all_trains_enhanced()
            emit('initial_trains', trains)
            emit('status', {
                'msg': 'Connected to Enhanced Real-Time KL Metro Tracking System', 
                'status': 'success',
                'client_count': len(enhanced_rt.websocket_clients),
                'features': ['websocket', 'multicast', 'enhanced_error_handling']
            })
        except Exception as e:
            print(f"Error sending initial data to client {client_id}: {e}")
            emit('status', {'msg': f'Error loading initial data: {str(e)}', 'status': 'error'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Enhanced disconnection handler with cleanup"""
        client_id = getattr(socketio, 'client_id', 'unknown')
        print(f'Client {client_id} disconnected from WebSocket')
        
        # Remove from client tracking
        if client_id in enhanced_rt.websocket_clients:
            enhanced_rt.websocket_clients.remove(client_id)
    
    @socketio.on('request_trains')
    def handle_request_trains():
        """Handle client request for current train positions with validation"""
        try:
            trains = get_all_trains_enhanced()
            emit('trains_data', {
                'trains': trains,
                'timestamp': time.time(),
                'source': 'database_query'
            })
        except Exception as e:
            print(f"Error fetching trains data: {e}")
            emit('error', {'msg': 'Failed to fetch train data', 'error_type': 'database_error'})
    
    @socketio.on('subscribe_zone')
    def handle_zone_subscription(data):
        """
        Zone-based subscription feature (inspired by Lab2 multicast zone filtering)
        Allows clients to subscribe to specific metro lines or zones
        """
        try:
            zone = data.get('zone', 'all')
            client_id = getattr(socketio, 'client_id', 'unknown')
            
            print(f"Client {client_id} subscribed to zone: {zone}")
            
            # Filter trains by zone/line if specified
            trains = get_all_trains_enhanced()
            if zone != 'all':
                # This would be enhanced with actual line/zone data
                filtered_trains = [t for t in trains if zone.lower() in str(t.get('line', '')).lower()]
                trains = filtered_trains
            
            emit('zone_trains', {
                'zone': zone,
                'trains': trains,
                'subscription_confirmed': True
            })
            
        except Exception as e:
            emit('error', {'msg': f'Zone subscription failed: {str(e)}', 'error_type': 'subscription_error'})
    
    @socketio.on('ping')
    def handle_ping(data=None):
        """Enhanced ping with system metrics and latency measurement support"""
        response = {
            'timestamp': time.time(),
            'server_status': 'healthy',
            'connected_clients': len(enhanced_rt.websocket_clients),
            'multicast_enabled': enhanced_rt.multicast_socket is not None
        }
        
        # Echo back ping_id if provided for latency measurement
        if data and isinstance(data, dict) and 'ping_id' in data:
            response['ping_id'] = data['ping_id']
            
        # Echo back client timestamp if provided for latency calculation
        if data and isinstance(data, dict) and 'timestamp' in data:
            response['client_timestamp'] = data['timestamp']
            response['server_timestamp'] = time.time()
            
        emit('pong', response)
    
    # Store enhanced realtime instance for use in data generator
    socketio.enhanced_realtime = enhanced_rt

def broadcast_train_update_enhanced(socketio, train_data):
    """
    Enhanced train update broadcasting with multiple delivery methods
    Combines WebSocket and Multicast approaches from practical exercises
    """
    enhanced_rt = getattr(socketio, 'enhanced_realtime', None)
    
    try:
        # Method 1: WebSocket broadcast (existing method)
        socketio.emit('train_update', train_data)
        
        # Method 2: Multicast broadcast (inspired by Lab2/Multicast)
        if enhanced_rt and enhanced_rt.multicast_socket:
            broadcast_multicast_update(enhanced_rt.multicast_socket, train_data)
        
        # Enhanced logging with more details
        print(f"Enhanced broadcast: Train {train_data.get('train_id')} -> Station {train_data.get('station_id')} "
              f"(WebSocket: ✓, Multicast: {'✓' if enhanced_rt and enhanced_rt.multicast_socket else '✗'})")
        
    except Exception as e:
        print(f"Error in enhanced broadcast: {e}")
        # Fallback to basic WebSocket broadcast
        socketio.emit('train_update', train_data)

def broadcast_multicast_update(multicast_socket, train_data):
    """
    Multicast broadcast implementation (inspired by Lab2/Multicast/Q1Server.py)
    Efficient for multiple clients monitoring train updates
    """
    try:
        # Create structured message similar to Lab2 alert system
        message = {
            'type': 'TRAIN_UPDATE',
            'train_id': train_data.get('train_id'),
            'station_id': train_data.get('station_id'),
            'station_name': train_data.get('station_name'),
            'latitude': train_data.get('latitude'),
            'longitude': train_data.get('longitude'),
            'timestamp': train_data.get('timestamp', time.time()),
            'zone': 'metro_kl'  # Could be enhanced with actual zone data
        }
        
        # Serialize message (using pickle like in video streaming examples)
        serialized_data = pickle.dumps(message)
        
        # Send via multicast
        multicast_socket.sendto(serialized_data, (MULTICAST_GROUP, MULTICAST_PORT))
        print(f"Multicast sent: Train {message['train_id']} update")
        
    except Exception as e:
        print(f"Multicast broadcast error: {e}")

def broadcast_system_alert(socketio, alert_data):
    """
    System alert broadcasting (inspired by Lab2 alert system)
    For service disruptions, maintenance, etc.
    """
    enhanced_rt = getattr(socketio, 'enhanced_realtime', None)
    
    try:
        # Structure alert similar to Lab2 format
        alert_message = {
            'type': alert_data.get('type', 'SYSTEM'),
            'zone': alert_data.get('zone', 'all'),
            'severity': alert_data.get('severity', 1),
            'message': alert_data.get('message', 'System alert'),
            'timestamp': time.time()
        }
        
        # Broadcast via WebSocket
        socketio.emit('system_alert', alert_message)
        
        # Broadcast via Multicast if available
        if enhanced_rt and enhanced_rt.multicast_socket:
            serialized_alert = pickle.dumps(alert_message)
            enhanced_rt.multicast_socket.sendto(serialized_alert, (MULTICAST_GROUP, MULTICAST_PORT))
        
        print(f"System alert broadcasted: {alert_message['message']}")
        
    except Exception as e:
        print(f"Error broadcasting system alert: {e}")

def get_connected_clients_count(socketio):
    """Enhanced client count with additional metrics"""
    enhanced_rt = getattr(socketio, 'enhanced_realtime', None)
    
    if enhanced_rt:
        return {
            'websocket_clients': len(enhanced_rt.websocket_clients),
            'multicast_enabled': enhanced_rt.multicast_socket is not None,
            'broadcast_methods': enhanced_rt.broadcast_modes
        }
    
    return {'websocket_clients': 0, 'multicast_enabled': False, 'broadcast_methods': ['websocket']}

class MulticastClient:
    """
    Multicast client for receiving train updates (inspired by Lab2/Multicast/Q1Client1.py)
    Can be used by external applications to monitor train updates
    """
    
    def __init__(self, zone_filter='all'):
        self.zone_filter = zone_filter
        self.socket = None
        self.running = False
        
    def start_listening(self):
        """Start listening for multicast train updates"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', MULTICAST_PORT))
            
            # Join multicast group
            mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            print(f"Multicast client listening for updates (zone filter: {self.zone_filter})")
            self.running = True
            
            while self.running:
                try:
                    data, _ = self.socket.recvfrom(1024)
                    message = pickle.loads(data)
                    
                    # Apply zone filter
                    if self.zone_filter == 'all' or message.get('zone') == self.zone_filter:
                        self.process_update(message)
                        
                except Exception as e:
                    print(f"Error receiving multicast data: {e}")
                    
        except Exception as e:
            print(f"Error starting multicast client: {e}")
    
    def process_update(self, message):
        """Process received train update"""
        if message.get('type') == 'TRAIN_UPDATE':
            print(f"[MULTICAST UPDATE] Train {message['train_id']} at {message['station_name']}")
        elif message.get('type') == 'SYSTEM':
            print(f"[SYSTEM ALERT] {message['message']} (Severity: {message['severity']})")
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.socket:
            self.socket.close()

# Legacy functions for backward compatibility
def broadcast_train_update(socketio, train_data):
    """Backward compatible function that uses enhanced broadcasting"""
    broadcast_train_update_enhanced(socketio, train_data)

def broadcast_system_status(socketio, status_data):
    """Enhanced system status broadcasting"""
    broadcast_system_alert(socketio, {
        'type': 'SYSTEM_STATUS',
        'message': status_data.get('message', 'System status update'),
        'severity': 1,
        'zone': 'all'
    })

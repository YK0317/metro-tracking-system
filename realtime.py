"""
Real-time Module for Real-Time KL Metro Tracking System
Handles WebSocket connections and real-time train update broadcasting
"""

from flask_socketio import emit, disconnect
from database import get_all_trains
import json

def init_realtime(socketio):
    """Initialize WebSocket event handlers - FR4"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection - FR4.1"""
        print('Client connected to WebSocket')
        
        # Send initial train positions to newly connected client
        try:
            trains = get_all_trains()
            emit('initial_trains', trains)
            emit('status', {'msg': 'Connected to Real-Time KL Metro Tracking System', 'status': 'success'})
        except Exception as e:
            print(f"Error sending initial data: {e}")
            emit('status', {'msg': 'Error loading initial data', 'status': 'error'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection - FR4.1"""
        print('Client disconnected from WebSocket')
    
    @socketio.on('request_trains')
    def handle_request_trains():
        """Handle client request for current train positions"""
        try:
            trains = get_all_trains()
            emit('trains_data', trains)
        except Exception as e:
            print(f"Error fetching trains data: {e}")
            emit('error', {'msg': 'Failed to fetch train data'})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping from client for connection testing"""
        emit('pong', {'timestamp': __import__('time').time()})
    
    # Store socketio instance for use in data generator
    socketio.metro_socketio = socketio

def broadcast_train_update(socketio, train_data):
    """
    Broadcast train update to all connected clients - FR4.2
    
    Args:
        socketio: SocketIO instance
        train_data: Dictionary containing train update information
    """
    try:
        # Emit train update to all connected clients
        socketio.emit('train_update', train_data)
        print(f"Broadcasted train update: Train {train_data.get('train_id')} -> Station {train_data.get('station_id')}")
        
    except Exception as e:
        print(f"Error broadcasting train update: {e}")

def broadcast_system_status(socketio, status_data):
    """
    Broadcast system status updates to all connected clients
    
    Args:
        socketio: SocketIO instance  
        status_data: Dictionary containing status information
    """
    try:
        socketio.emit('system_status', status_data)
        print(f"Broadcasted system status: {status_data}")
        
    except Exception as e:
        print(f"Error broadcasting system status: {e}")

def get_connected_clients_count(socketio):
    """Get the number of currently connected WebSocket clients"""
    try:
        # This is a simplified way to get client count
        # In production, you might want to track this more precisely
        return len(socketio.server.manager.get_participants('/', '/'))
    except:
        return 0

"""
Real-Time KL Metro Tracking and Routing System
Main Flask Application Entry Point
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Initialize SocketIO with threading mode for Windows compatibility
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)

# Import modules
from database import init_db, get_db_connection
from realtime import init_realtime
from data_generator import start_data_generator
print("Using train movement system with line-based movement")

from routes import init_routes

def create_app():
    """Create and configure the Flask application"""
    print("Initializing Real-Time KL Metro Tracking System...")
    
    # Initialize database
    print("Setting up database...")
    init_db()
    
    # Initialize routes
    print("Setting up routes...")
    init_routes(app)
    
    # Initialize real-time messaging
    print("Setting up real-time messaging...")
    init_realtime(socketio)
    
    # Start background data generator
    print("Starting train data generator...")
    generator_thread = threading.Thread(target=start_data_generator, args=(socketio,))
    generator_thread.daemon = True
    generator_thread.start()
    
    print("System initialization complete!")
    return app

@app.route('/')
def index():
    """Serve the main kiosk interface"""
    return render_template('index.html')

if __name__ == '__main__':
    create_app()
    print("Starting Flask-SocketIO server...")
    print("Access the application at: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

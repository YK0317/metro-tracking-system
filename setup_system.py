"""
Automated Setup Script for KL Metro Tracking System
This script will set up the entire system with seeded data for new collaborators
"""

import subprocess
import sys
import os
import time

def print_banner():
    """Print setup banner"""
    print("🚇" * 30)
    print("  KL METRO TRACKING SYSTEM")
    print("     AUTOMATED SETUP")
    print("🚇" * 30)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing Dependencies...")
    print("-" * 40)
    
    try:
        # Check if requirements.txt exists
        if not os.path.exists('requirements.txt'):
            print("⚠️  requirements.txt not found. Installing essential packages...")
            essential_packages = [
                'flask', 'flask-socketio', 'sqlite3'
            ]
            for package in essential_packages:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        else:
            print("Installing from requirements.txt...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_database():
    """Set up the database with stations and fare data"""
    print("\n🗄️  Initializing Database...")
    print("-" * 40)
    
    try:
        result = subprocess.run([sys.executable, 'initialize_database.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Database initialized with stations and fare data")
            # Print key output lines
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Loaded' in line or 'stations' in line or 'fare' in line:
                    print(f"   {line}")
            return True
        else:
            print(f"❌ Database initialization failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Database initialization timed out")
        return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def load_trains():
    """Load trains from CSV configuration"""
    print("\n🚂 Loading Trains...")
    print("-" * 40)
    
    try:
        result = subprocess.run([sys.executable, 'add_trains_direct.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Trains loaded successfully")
            # Extract key information
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Successfully added' in line or 'Total active trains' in line:
                    print(f"   {line}")
            return True
        else:
            print(f"❌ Train loading failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Train loading timed out")
        return False
    except Exception as e:
        print(f"❌ Error loading trains: {e}")
        return False

def verify_setup():
    """Verify the setup is complete"""
    print("\n🔍 Verifying Setup...")
    print("-" * 40)
    
    try:
        # Check database exists
        if os.path.exists('metro_tracking_enhanced.db'):
            print("✅ Database file exists")
        else:
            print("❌ Database file not found")
            return False
        
        # Check data files exist
        data_files = ['data/Stations.csv', 'data/Trains.csv', 'data/Fare.csv']
        for file in data_files:
            if os.path.exists(file):
                print(f"✅ {file} exists")
            else:
                print(f"❌ {file} not found")
                return False
        
        # Quick database check
        import sqlite3
        conn = sqlite3.connect('metro_tracking_enhanced.db')
        
        station_count = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
        train_count = conn.execute("SELECT COUNT(*) FROM trains").fetchone()[0]
        fare_count = conn.execute("SELECT COUNT(*) FROM fares").fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database contains:")
        print(f"   📍 {station_count} stations")
        print(f"   🚂 {train_count} trains")
        print(f"   💰 {fare_count} fare records")
        
        if station_count > 0 and train_count > 0 and fare_count > 0:
            return True
        else:
            print("❌ Database appears to be empty")
            return False
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_next_steps():
    """Show what to do next"""
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    print()
    print("🚀 To start the server:")
    print("   python app.py")
    print()
    print("🌐 Then visit:")
    print("   http://localhost:5000")
    print()
    print("📊 Additional tools:")
    print("   python generate_train_routes.py  # Generate route predictions")
    print("   python route_summary.py         # View route summary")
    print()
    print("🛠️  If you need to reset:")
    print("   python initialize_database.py   # Reset database")
    print("   python add_trains_direct.py     # Reload trains")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return False
    
    # Initialize database
    if not initialize_database():
        print("\n❌ Setup failed: Database initialization failed")
        return False
    
    # Load trains
    if not load_trains():
        print("\n❌ Setup failed: Train loading failed")
        return False
    
    # Verify everything is working
    if not verify_setup():
        print("\n❌ Setup failed: Verification failed")
        return False
    
    # Show next steps
    show_next_steps()
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n💡 Try running individual setup steps manually:")
            print("   1. python initialize_database.py")
            print("   2. python add_trains_direct.py")
            print("   3. python app.py")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)

# KL Metro Tracking System - Setup Guide

## 🚀 Quick Start for Collaborators

### Step 1: Clone the repository
```bash
git clone https://github.com/YK0317/metro-tracking-system.git
cd metro-tracking-system
```

### Step 2: Install dependencies
```bash
pip install flask flask-socketio
```

### Step 3: Run these files in order
```bash
python initialize_database.py
python add_trains_direct.py
python app.py
```

### Step 4: Open browser
Go to: http://localhost:5000

That's it! The system will be running with all data loaded.

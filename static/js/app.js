/**
 * Real-Time KL Metro Tracking System - Frontend Application
 * Handles map visualization, real-time updates, and route planning
 */

class MetroTrackingApp {
    constructor() {
        // Initialize application state
        this.map = null;
        this.socket = null;
        this.stations = [];
        this.trains = new Map();
        this.stationMarkers = new Map();
        this.trainMarkers = new Map();
        this.routePolyline = null;
        this.isConnected = false;
        
        // Initialize the application
        this.init();
    }
    
    async init() {
        console.log('Initializing Metro Tracking App...');
        
        try {
            // Initialize map
            this.initializeMap();
            
            // Initialize WebSocket connection
            this.initializeWebSocket();
            
            // Load initial data
            await this.loadStations();
            
            // Setup event listeners
            this.setupEventListeners();
            
            console.log('App initialization complete!');
            
        } catch (error) {
            console.error('Error initializing app:', error);
            this.showError('Failed to initialize application');
        }
    }
    
    initializeMap() {
        console.log('Initializing map...');
        
        // Create map centered on Kuala Lumpur
        this.map = L.map('map').setView([3.1548, 101.7147], 12);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        // Add custom controls
        this.addMapControls();
        
        console.log('Map initialized successfully');
    }
    
    addMapControls() {
        // Add legend control
        const legend = L.control({position: 'bottomright'});
        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'legend');
            div.style.background = 'white';
            div.style.padding = '10px';
            div.style.borderRadius = '5px';
            div.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            div.innerHTML = `
                <h4 style="margin: 0 0 10px 0;">Legend</h4>
                <div><span style="color: #3388ff;">🏢</span> Metro Stations</div>
                <div><span style="color: #ff3333;">🚇</span> Active Trains</div>
                <div><span style="color: #33ff33;">━━</span> Planned Route</div>
            `;
            return div;
        };
        legend.addTo(this.map);
    }
    
    initializeWebSocket() {
        console.log('Connecting to WebSocket...');
        
        // Connect to Socket.IO server
        this.socket = io();
        
        // Connection event handlers
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        // Data event handlers
        this.socket.on('initial_trains', (trains) => {
            console.log('Received initial train data:', trains);
            this.updateTrainPositions(trains);
        });
        
        this.socket.on('train_update', (trainData) => {
            console.log('Received train update:', trainData);
            this.updateSingleTrain(trainData);
        });
        
        this.socket.on('status', (statusData) => {
            console.log('Status update:', statusData);
            if (statusData.status === 'error') {
                this.showError(statusData.msg);
            }
        });
        
        this.socket.on('error', (errorData) => {
            console.error('Socket error:', errorData);
            this.showError(errorData.msg || 'WebSocket connection error');
        });
    }
    
    async loadStations() {
        console.log('Loading stations...');
        
        try {
            const response = await fetch('/api/stations');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.stations = await response.json();
            console.log(`Loaded ${this.stations.length} stations`);
            
            // Add station markers to map
            this.addStationMarkers();
            
            // Populate dropdown menus
            this.populateStationSelects();
            
        } catch (error) {
            console.error('Error loading stations:', error);
            this.showError('Failed to load station data');
        }
    }
    
    addStationMarkers() {
        console.log('Adding station markers to map...');
        
        this.stations.forEach(station => {
            // Create station marker
            const marker = L.marker([station.latitude, station.longitude], {
                icon: this.createStationIcon()
            }).addTo(this.map);
            
            // Add popup with station info
            marker.bindPopup(`
                <div style="text-align: center;">
                    <h4 style="margin: 0 0 5px 0;">${station.name}</h4>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">
                        Station ID: ${station.station_id}<br>
                        Lat: ${station.latitude.toFixed(4)}, Lng: ${station.longitude.toFixed(4)}
                    </p>
                </div>
            `);
            
            // Store marker reference
            this.stationMarkers.set(station.station_id, marker);
        });
        
        console.log(`Added ${this.stationMarkers.size} station markers`);
    }
    
    createStationIcon() {
        return L.divIcon({
            html: '🏢',
            iconSize: [20, 20],
            className: 'station-icon'
        });
    }
    
    createTrainIcon() {
        return L.divIcon({
            html: '🚇',
            iconSize: [25, 25],
            className: 'train-icon'
        });
    }
    
    populateStationSelects() {
        const originSelect = document.getElementById('origin-select');
        const destinationSelect = document.getElementById('destination-select');
        
        // Clear existing options
        originSelect.innerHTML = '<option value="">Select origin station...</option>';
        destinationSelect.innerHTML = '<option value="">Select destination station...</option>';
        
        // Add station options
        this.stations.forEach(station => {
            const originOption = new Option(station.name, station.station_id);
            const destinationOption = new Option(station.name, station.station_id);
            
            originSelect.add(originOption);
            destinationSelect.add(destinationOption);
        });
        
        console.log('Station select menus populated');
    }
    
    updateTrainPositions(trains) {
        console.log('Updating train positions...');
        
        // Clear existing train markers
        this.trainMarkers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.trainMarkers.clear();
        
        // Add new train markers
        trains.forEach(train => {
            this.addTrainMarker(train);
        });
        
        // Update train list in sidebar
        this.updateTrainList(trains);
    }
    
    updateSingleTrain(trainData) {
        // Remove existing marker for this train
        if (this.trainMarkers.has(trainData.train_id)) {
            this.map.removeLayer(this.trainMarkers.get(trainData.train_id));
        }
        
        // Add updated marker
        this.addTrainMarker(trainData);
        
        // Update train in sidebar list
        this.updateTrainInList(trainData);
    }
    
    addTrainMarker(trainData) {
        if (!trainData.latitude || !trainData.longitude) {
            console.warn('Invalid train position data:', trainData);
            return;
        }
        
        const marker = L.marker([trainData.latitude, trainData.longitude], {
            icon: this.createTrainIcon()
        }).addTo(this.map);
        
        // Add popup with train info
        const stationName = trainData.station_name || 'Unknown Station';
        marker.bindPopup(`
            <div style="text-align: center;">
                <h4 style="margin: 0 0 5px 0;">🚇 Train ${trainData.train_id}</h4>
                <p style="margin: 0; color: #666; font-size: 0.9em;">
                    Current: ${stationName}<br>
                    Station ID: ${trainData.current_station_id || trainData.station_id}<br>
                    Last Updated: ${new Date(trainData.last_updated || Date.now()).toLocaleTimeString()}
                </p>
            </div>
        `);
        
        // Store marker reference
        this.trainMarkers.set(trainData.train_id, marker);
    }
    
    updateTrainList(trains) {
        const trainListElement = document.getElementById('train-list');
        
        if (trains.length === 0) {
            trainListElement.innerHTML = '<div class="loading">No active trains</div>';
            return;
        }
        
        const trainListHTML = trains.map(train => {
            const stationName = train.station_name || 'Unknown Station';
            return `
                <div class="train-item" data-train-id="${train.train_id}">
                    <div class="train-id">Train ${train.train_id}</div>
                    <div class="train-location">${stationName}</div>
                </div>
            `;
        }).join('');
        
        trainListElement.innerHTML = trainListHTML;
    }
    
    updateTrainInList(trainData) {
        const trainItem = document.querySelector(`[data-train-id="${trainData.train_id}"]`);
        if (trainItem) {
            const locationElement = trainItem.querySelector('.train-location');
            const stationName = trainData.station_name || 'Unknown Station';
            locationElement.textContent = stationName;
            
            // Add visual feedback for update
            trainItem.style.backgroundColor = '#e8f5e8';
            setTimeout(() => {
                trainItem.style.backgroundColor = 'white';
            }, 1000);
        }
    }
    
    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Route planning button
        const planRouteBtn = document.getElementById('plan-route-btn');
        const originSelect = document.getElementById('origin-select');
        const destinationSelect = document.getElementById('destination-select');
        
        // Enable/disable plan route button based on selection
        const checkSelections = () => {
            const hasOrigin = originSelect.value !== '';
            const hasDestination = destinationSelect.value !== '';
            planRouteBtn.disabled = !hasOrigin || !hasDestination || !this.isConnected;
        };
        
        originSelect.addEventListener('change', checkSelections);
        destinationSelect.addEventListener('change', checkSelections);
        
        // Plan route button click
        planRouteBtn.addEventListener('click', () => {
            this.planRoute();
        });
        
        console.log('Event listeners setup complete');
    }
    
    async planRoute() {
        const originId = document.getElementById('origin-select').value;
        const destinationId = document.getElementById('destination-select').value;
        const resultElement = document.getElementById('route-result');
        
        if (!originId || !destinationId) {
            this.showError('Please select both origin and destination stations');
            return;
        }
        
        try {
            console.log(`Planning route from ${originId} to ${destinationId}`);
            resultElement.innerHTML = '<div class="loading">Calculating route...</div>';
            
            // Fetch route data
            const response = await fetch(`/api/route?from=${originId}&to=${destinationId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const routeData = await response.json();
            
            if (routeData.error) {
                throw new Error(routeData.error);
            }
            
            console.log('Route calculated:', routeData);
            
            // Display route result
            this.displayRouteResult(routeData);
            
            // Draw route on map
            this.drawRouteOnMap(routeData.path);
            
        } catch (error) {
            console.error('Error planning route:', error);
            resultElement.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    }
    
    displayRouteResult(routeData) {
        const resultElement = document.getElementById('route-result');
        
        // Get station names for the path
        const pathWithNames = routeData.path.map(stationId => {
            const station = this.stations.find(s => s.station_id === stationId);
            return station ? station.name : `Station ${stationId}`;
        });
        
        const routeHTML = `
            <div class="route-result">
                <h4>📍 Route Found</h4>
                <div class="route-path">
                    <strong>Path:</strong><br>
                    ${pathWithNames.join(' → ')}
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                    <span><strong>Total Fare:</strong> RM ${routeData.total_fare.toFixed(2)}</span>
                    <span><strong>Stops:</strong> ${routeData.total_hops}</span>
                </div>
            </div>
        `;
        
        resultElement.innerHTML = routeHTML;
    }
    
    drawRouteOnMap(path) {
        // Remove existing route
        if (this.routePolyline) {
            this.map.removeLayer(this.routePolyline);
        }
        
        // Get coordinates for path stations
        const pathCoordinates = path.map(stationId => {
            const station = this.stations.find(s => s.station_id === stationId);
            return station ? [station.latitude, station.longitude] : null;
        }).filter(coord => coord !== null);
        
        if (pathCoordinates.length > 1) {
            // Draw polyline for route
            this.routePolyline = L.polyline(pathCoordinates, {
                color: '#33ff33',
                weight: 4,
                opacity: 0.8
            }).addTo(this.map);
            
            // Fit map to show entire route
            this.map.fitBounds(this.routePolyline.getBounds(), {padding: [20, 20]});
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const planRouteBtn = document.getElementById('plan-route-btn');
        
        if (connected) {
            statusElement.className = 'status connected';
            statusElement.innerHTML = '✅ Connected to server';
        } else {
            statusElement.className = 'status disconnected';
            statusElement.innerHTML = '❌ Disconnected from server';
        }
        
        // Update button state
        const originSelect = document.getElementById('origin-select');
        const destinationSelect = document.getElementById('destination-select');
        const hasSelections = originSelect.value !== '' && destinationSelect.value !== '';
        planRouteBtn.disabled = !connected || !hasSelections;
    }
    
    showError(message) {
        console.error('Application error:', message);
        
        // You could implement a toast notification system here
        // For now, we'll use browser alert as fallback
        if (message.includes('Failed to')) {
            alert(`Error: ${message}`);
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, starting Metro Tracking App...');
    window.metroApp = new MetroTrackingApp();
});

// Export for potential debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MetroTrackingApp;
}

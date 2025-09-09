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
            
            // Draw static metro lines
            this.drawStaticMetroLines();
            
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
                <div><span style="color: #1f77b4;">━━</span> KJL Line</div>
                <div><span style="color: #ff7f0e;">━━</span> SBK Line</div>
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
    
    drawStaticMetroLines() {
        console.log('Drawing static metro lines...');
        
        // Clear any existing metro lines first
        this.clearMetroLines();
        
        // Define the metro line sequences with exact station connections
        const metroLines = {
            'KJL': {
                name: 'Kelana Jaya Line',
                color: '#1f77b4',
                // Corrected sequence based on real KJL line geography
                stations: [
                    "Gombak", "Taman Melati", "Wangsa Maju", "Sri Rampai", 
                    "Setiawangsa", "Jelatek", "Dato' Keramat", "Damai",
                    "Ampang Park", "KLCC", "Kampung Baru", "Dang Wangi",
                    "Masjid Jamek (KJL)", "Pasar Seni (KJL)", "KL Sentral (KJL)",
                    "Bangsar", "Abdullah Hukum", "Kerinchi", "Universiti",
                    "Taman Jaya", "Asia Jaya", "Taman Paramount", "Taman Bahagia",
                    "Kelana Jaya", "Lembah Subang", "Ara Damansara", "Glenmarie",
                    "Subang Jaya", "SS 15", "SS 18", "USJ 7 (KJL)", "Taipan",
                    "Wawasan", "USJ 21", "Alam Megah", "Subang Alam", "Putra Heights (KJL)"
                ],
                // Add known problematic connections that need special handling
                problematicConnections: [
                    { from: "Ampang Park", to: "KLCC" }, // Major geographical jump
                    { from: "Taman Bahagia", to: "Kelana Jaya" } // Another potential jump
                ]
            },
            'SBK': {
                name: 'Sungai Buloh-Kajang Line',
                color: '#ff7f0e',
                stations: [
                    "Sungai Buloh", "Kampung Selamat", "Kwasa Damansara", "Kwasa Sentral",
                    "Kota Damansara", "Surian", "Mutiara Damansara", "Bandar Utama",
                    "TTDI", "Phileo Damansara", "Pusat Bandar Damansara", "Semantan",
                    "Muzium Negara", "Pasar Seni (SBK)", "Merdeka", "Bukit Bintang", 
                    "Tun Razak Exchange (TRX)", "Cochrane", "Maluri (SBK)", "Taman Pertama", 
                    "Taman Midah", "Taman Mutiara", "Taman Connaught", "Taman Suntex", 
                    "Sri Raya", "Bandar Tun Hussein Onn", "Batu 11 Cheras", "Bukit Dukung",
                    "Sungai Jernih", "Stadium Kajang", "Kajang"
                ]
            }
        };
        
        // Draw each metro line
        Object.keys(metroLines).forEach(lineCode => {
            const line = metroLines[lineCode];
            this.drawMetroLine(line, lineCode);
        });
        
        // Add metro lines legend with toggle
        this.addMetroLinesLegend(metroLines);
        
        console.log('Static metro lines drawn successfully');
    }
    
    clearMetroLines() {
        // Clear existing metro line polylines
        if (this.metroLinePolylines && this.metroLinePolylines.length > 0) {
            this.metroLinePolylines.forEach(polyline => {
                if (this.map.hasLayer(polyline)) {
                    this.map.removeLayer(polyline);
                }
            });
            this.metroLinePolylines = [];
        }
    }
    
    toggleMetroLines() {
        if (this.metroLinesVisible) {
            this.clearMetroLines();
            this.metroLinesVisible = false;
            console.log('Metro lines hidden');
        } else {
            this.drawStaticMetroLines();
            this.metroLinesVisible = true;
            console.log('Metro lines shown');
        }
    }
    
    drawMetroLine(line, lineCode) {
        // Get coordinates for all stations in this line
        const lineCoordinates = [];
        const stationPositions = [];
        
        line.stations.forEach(stationName => {
            const station = this.stations.find(s => s.name === stationName);
            if (station) {
                const coord = [station.latitude, station.longitude];
                lineCoordinates.push(coord);
                stationPositions.push({
                    name: stationName,
                    coord: coord,
                    station: station
                });
            }
        });
        
        if (lineCoordinates.length < 2) {
            console.warn(`Not enough coordinates for ${line.name}`);
            return;
        }
        
        // Draw individual segments between consecutive stations with improved routing
        for (let i = 0; i < stationPositions.length - 1; i++) {
            const currentStation = stationPositions[i];
            const nextStation = stationPositions[i + 1];
            
            // Calculate the distance between stations
            const distance = this.calculateDistance(currentStation.coord, nextStation.coord);
            
            // Check if this is a known problematic connection
            const isProblematic = line.problematicConnections && 
                line.problematicConnections.some(conn => 
                    conn.from === currentStation.name && conn.to === nextStation.name);
            
            // If the distance is too large or it's a known problematic connection,
            // draw a curved path instead of a straight line
            let pathCoordinates = [currentStation.coord, nextStation.coord];
            let lineStyle = {
                color: line.color,
                weight: 4,
                opacity: 0.8,
                smoothFactor: 2
            };
            
            if (distance > 0.05 || isProblematic) { // More than ~5km jump or known issue
                // Add intermediate points to create a more realistic curved path
                pathCoordinates = this.createCurvedPath(currentStation.coord, nextStation.coord);
                
                // Use dashed line for problematic connections to indicate uncertainty
                if (isProblematic) {
                    lineStyle.dashArray = '10, 5';
                    lineStyle.opacity = 0.6;
                }
            }
            
            // Create a connection line segment between consecutive stations
            const segmentPolyline = L.polyline(pathCoordinates, lineStyle).addTo(this.map);
            
            // Add hover effect to show connection info
            const distanceKm = (distance * 111).toFixed(1);
            const connectionType = isProblematic ? "⚠️ Geographical Jump" : "🚇 Direct Connection";
            
            segmentPolyline.bindTooltip(`
                <div style="text-align: center;">
                    <strong>${line.name}</strong><br>
                    ${currentStation.name} ↔ ${nextStation.name}<br>
                    <small>${connectionType}</small><br>
                    <small>Distance: ${distanceKm}km</small>
                </div>
            `, {
                sticky: true,
                className: 'connection-tooltip'
            });
            
            // Add click popup to segment
            segmentPolyline.bindPopup(`
                <div style="text-align: center;">
                    <h4 style="margin: 0 0 5px 0; color: ${line.color};">${line.name}</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        <strong>Connection:</strong> ${currentStation.name} ↔ ${nextStation.name}<br>
                        <strong>Type:</strong> ${connectionType}<br>
                        <strong>Segment:</strong> ${i + 1} of ${stationPositions.length - 1}<br>
                        <strong>Line Code:</strong> ${lineCode}<br>
                        <strong>Distance:</strong> ${distanceKm}km<br>
                        <strong>Coordinates:</strong><br>
                        &nbsp;&nbsp;From: ${currentStation.coord[0].toFixed(4)}, ${currentStation.coord[1].toFixed(4)}<br>
                        &nbsp;&nbsp;To: ${nextStation.coord[0].toFixed(4)}, ${nextStation.coord[1].toFixed(4)}
                    </p>
                </div>
            `);
            
            // Store the polyline reference
            if (!this.metroLinePolylines) {
                this.metroLinePolylines = [];
            }
            this.metroLinePolylines.push(segmentPolyline);
        }
        
        // Add station connection circles to show actual station-to-station connections
        stationPositions.forEach((station, index) => {
            // Create a small circle at each station to highlight it's part of this line
            const stationCircle = L.circleMarker(station.coord, {
                color: line.color,
                fillColor: line.color,
                fillOpacity: 0.7,
                radius: 6,
                weight: 2
            }).addTo(this.map);
            
            // Add popup to station circle
            stationCircle.bindPopup(`
                <div style="text-align: center;">
                    <h4 style="margin: 0 0 5px 0; color: ${line.color};">${station.name}</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        <strong>Line:</strong> ${line.name} (${lineCode})<br>
                        <strong>Position:</strong> ${index + 1} of ${stationPositions.length}<br>
                        <strong>Coordinates:</strong> ${station.coord[0].toFixed(4)}, ${station.coord[1].toFixed(4)}<br>
                        ${index > 0 ? `<strong>Previous:</strong> ${stationPositions[index - 1].name}<br>` : ''}
                        ${index < stationPositions.length - 1 ? `<strong>Next:</strong> ${stationPositions[index + 1].name}` : ''}
                    </p>
                </div>
            `);
            
            this.metroLinePolylines.push(stationCircle);
        });
    }
    
    calculateDistance(coord1, coord2) {
        // Calculate distance between two lat/lng coordinates (rough estimate)
        const lat1 = coord1[0], lng1 = coord1[1];
        const lat2 = coord2[0], lng2 = coord2[1];
        
        const dlat = lat2 - lat1;
        const dlng = lng2 - lng1;
        
        return Math.sqrt(dlat * dlat + dlng * dlng);
    }
    
    createCurvedPath(startCoord, endCoord) {
        // Create a curved path between two points that are far apart
        const lat1 = startCoord[0], lng1 = startCoord[1];
        const lat2 = endCoord[0], lng2 = endCoord[1];
        
        // Calculate midpoint
        const midLat = (lat1 + lat2) / 2;
        const midLng = (lng1 + lng2) / 2;
        
        // For the Ampang Park to KLCC connection, create a realistic curve
        // that follows the actual metro line path through the city
        if ((Math.abs(lat1 - 3.3326) < 0.001 && Math.abs(lat2 - 3.1588) < 0.001) ||
            (Math.abs(lat2 - 3.3326) < 0.001 && Math.abs(lat1 - 3.1588) < 0.001)) {
            
            // This is the Ampang Park <-> KLCC connection
            // Create a path that curves through the city center
            return [
                startCoord,
                [3.31, 101.70],   // Curve point 1 (city center approach)
                [3.28, 101.705],  // Curve point 2 (downtown area)
                [3.20, 101.71],   // Curve point 3 (KLCC approach)
                endCoord
            ];
        }
        
        // For other large gaps, create a simple curved path
        const offset = 0.01; // Adjust this for more/less curve
        
        // Determine curve direction based on the geographical relationship
        let curveOffsetLat, curveOffsetLng;
        
        if (lat2 > lat1) { // Going north
            curveOffsetLat = offset;
            curveOffsetLng = (lng2 > lng1) ? offset : -offset;
        } else { // Going south
            curveOffsetLat = -offset;
            curveOffsetLng = (lng2 > lng1) ? offset : -offset;
        }
        
        const curveLat = midLat + curveOffsetLat;
        const curveLng = midLng + curveOffsetLng;
        
        // Return path with intermediate points for smoother curve
        return [
            startCoord,
            [lat1 + (curveLat - lat1) * 0.33, lng1 + (curveLng - lng1) * 0.33],
            [curveLat, curveLng],
            [lat2 + (curveLat - lat2) * 0.33, lng2 + (curveLng - lng2) * 0.33],
            endCoord
        ];
    }
    
    addMetroLinesLegend(metroLines) {
        // Remove existing metro lines legend if present
        if (this.metroLinesLegend) {
            this.map.removeControl(this.metroLinesLegend);
        }
        
        this.metroLinesLegend = L.control({position: 'topleft'});
        
        this.metroLinesLegend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'metro-lines-legend');
            div.style.background = 'white';
            div.style.padding = '10px';
            div.style.borderRadius = '5px';
            div.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            div.style.fontSize = '12px';
            div.style.maxWidth = '200px';
            
            let legendHTML = '<h4 style="margin: 0 0 8px 0; font-size: 14px;">🚇 Metro Lines</h4>';
            
            // Add toggle button
            legendHTML += `
                <button id="toggle-metro-lines" style="width: 100%; margin-bottom: 8px; padding: 4px; border: 1px solid #ccc; border-radius: 3px; background: #f8f8f8; cursor: pointer; font-size: 11px;">
                    Toggle Line Visibility
                </button>
            `;
            
            Object.keys(metroLines).forEach(lineCode => {
                const line = metroLines[lineCode];
                legendHTML += `
                    <div class="legend-line-item" style="margin-bottom: 5px; display: flex; align-items: center;">
                        <span style="display: inline-block; width: 20px; height: 3px; background-color: ${line.color}; margin-right: 8px; border-radius: 2px;"></span>
                        <div style="flex: 1;">
                            <strong>${lineCode}</strong><br>
                            <span style="font-size: 10px; color: #666;">${line.stations.length} stations</span>
                        </div>
                    </div>
                `;
            });
            
            legendHTML += `
                <div style="margin-top: 8px; padding-top: 5px; border-top: 1px solid #eee; font-size: 10px; color: #666;">
                    <div>━━━ Station Connections</div>
                    <div>● Line Stations</div>
                </div>
            `;
            
            div.innerHTML = legendHTML;
            
            // Add click event to toggle button after the div is added to the map
            setTimeout(() => {
                const toggleBtn = document.getElementById('toggle-metro-lines');
                if (toggleBtn) {
                    toggleBtn.addEventListener('click', () => {
                        if (window.metroApp) {
                            window.metroApp.toggleMetroLines();
                        }
                    });
                }
            }, 100);
            
            return div;
        }.bind(this);
        
        this.metroLinesLegend.addTo(this.map);
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
            
            // Draw route on map with enhanced visualization
            this.drawRouteOnMap(routeData.path, routeData);
            
        } catch (error) {
            console.error('Error planning route:', error);
            resultElement.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    }
    
    displayRouteResult(routeData) {
        const resultElement = document.getElementById('route-result');
        
        // Check if we have enhanced route data
        if (routeData.steps && routeData.steps.length > 0) {
            // Enhanced route display with step-by-step information
            const hasTransfer = routeData.has_transfer || false;
            const linesUsed = routeData.lines_used || [];
            
            let stepsHTML = '';
            routeData.steps.forEach((step, index) => {
                const stepIcon = step.transfer ? '🔄' : '🚇';
                const transferNote = step.transfer ? ' <span class="transfer-note">(Transfer)</span>' : '';
                stepsHTML += `
                    <div class="route-step">
                        ${stepIcon} <strong>${step.line} Line:</strong> ${step.from_station} → ${step.to_station}${transferNote}
                    </div>
                `;
            });
            
            const routeHTML = `
                <div class="route-result enhanced">
                    <h4>📍 Route Found</h4>
                    <div class="route-summary">
                        <div class="route-info">
                            <span><strong>🚇 Lines:</strong> ${linesUsed.join(', ')}</span>
                            <span><strong>🔄 Transfer:</strong> ${hasTransfer ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="route-costs">
                            <span><strong>💰 Fare:</strong> RM ${(routeData.fare || routeData.total_fare || 0).toFixed(2)}</span>
                            <span><strong>⏱️ Time:</strong> ${routeData.travel_time_formatted || 'N/A'}</span>
                            <span><strong>📍 Stops:</strong> ${routeData.total_hops}</span>
                        </div>
                    </div>
                    <div class="route-steps">
                        <strong>📋 Route Details:</strong>
                        ${stepsHTML}
                    </div>
                </div>
            `;
            
            resultElement.innerHTML = routeHTML;
            
        } else {
            // Fallback to basic route display
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
                        <span><strong>💰 Fare:</strong> RM ${(routeData.fare || routeData.total_fare || 0).toFixed(2)}</span>
                        <span><strong>⏱️ Time:</strong> ${routeData.travel_time_formatted || 'N/A'}</span>
                        <span><strong>📍 Stops:</strong> ${routeData.total_hops}</span>
                    </div>
                </div>
            `;
            
            resultElement.innerHTML = routeHTML;
        }
    }
    
    drawRouteOnMap(path, routeData = null) {
        // Remove existing route
        if (this.routePolylines) {
            this.routePolylines.forEach(polyline => this.map.removeLayer(polyline));
        }
        if (this.routePolyline) {
            this.map.removeLayer(this.routePolyline);
        }
        if (this.transferMarkers) {
            this.transferMarkers.forEach(marker => this.map.removeLayer(marker));
        }
        
        this.routePolylines = [];
        this.transferMarkers = [];
        this.metroLinePolylines = [];
        this.metroLinesVisible = true;
        
        // Check if we have enhanced route data with steps
        console.log('Route data received:', routeData);
        if (routeData && routeData.steps && routeData.steps.length > 0) {
            console.log('Using enhanced route drawing');
            this.drawEnhancedRoute(routeData);
        } else {
            // Fallback to simple route drawing
            console.log('Using simple route drawing for path:', path);
            this.drawSimpleRoute(path);
        }
    }
    
    drawEnhancedRoute(routeData) {
        const lineColors = {
            'KJL': '#0066ff',  // Bright Blue for Kelana Jaya Line
            'SBK': '#ff3300'   // Bright Red for Sungai Buloh-Kajang Line
        };
        
        // Define line sequences (same as in train_movement.py)
        const lineSequences = {
            'KJL': [
                "Gombak", "Taman Melati", "Wangsa Maju", "Sri Rampai", 
                "Setiawangsa", "Jelatek", "Dato' Keramat", "Damai",
                "Ampang Park", "KLCC", "Kampung Baru", "Dang Wangi",
                "Masjid Jamek (KJL)", "Pasar Seni (KJL)", "KL Sentral (KJL)",
                "Bangsar", "Abdullah Hukum", "Kerinchi", "Universiti",
                "Taman Jaya", "Asia Jaya", "Taman Paramount", "Taman Bahagia",
                "Kelana Jaya", "Lembah Subang", "Ara Damansara", "Glenmarie",
                "Subang Jaya", "SS 15", "SS 18", "USJ 7 (KJL)", "Taipan",
                "Wawasan", "USJ 21", "Alam Megah", "Subang Alam", "Putra Heights (KJL)"
            ],
            'SBK': [
                "Sungai Buloh", "Kampung Selamat", "Kwasa Damansara", "Kwasa Sentral",
                "Kota Damansara", "Surian", "Mutiara Damansara", "Bandar Utama",
                "TTDI", "Phileo Damansara", "Pusat Bandar Damansara", "Semantan",
                "Muzium Negara", "Pasar Seni (SBK)", "Merdeka", "Bukit Bintang", 
                "Tun Razak Exchange (TRX)", "Cochrane", "Maluri (SBK)", "Taman Pertama", 
                "Taman Midah", "Taman Mutiara", "Taman Connaught", "Taman Suntex", 
                "Sri Raya", "Bandar Tun Hussein Onn", "Batu 11 Cheras", "Bukit Dukung",
                "Sungai Jernih", "Stadium Kajang", "Kajang"
            ]
        };
        
        let allCoordinates = [];
        
        // Draw each step of the route
        routeData.steps.forEach((step, index) => {
            const fromStation = this.stations.find(s => s.name === step.from_station);
            const toStation = this.stations.find(s => s.name === step.to_station);
            
            if (fromStation && toStation && step.line) {
                // Get the intermediate stations on this line
                const lineStations = this.getStationsOnLine(step.from_station, step.to_station, step.line, lineSequences);
                
                // Convert station names to coordinates
                const stepCoordinates = lineStations.map(stationName => {
                    const station = this.stations.find(s => s.name === stationName);
                    return station ? [station.latitude, station.longitude] : null;
                }).filter(coord => coord !== null);
                
                if (stepCoordinates.length > 1) {
                    // Choose color based on line
                    const lineColor = lineColors[step.line] || '#33ff33';
                    const isTransfer = step.transfer || false;
                    
                    // Draw polyline for this step following the actual line path
                    // Make the route line more prominent with higher z-index and thicker weight
                    const polyline = L.polyline(stepCoordinates, {
                        color: lineColor,
                        weight: isTransfer ? 8 : 6,  // Increased weight for better visibility
                        opacity: 0.9,  // Increased opacity
                        dashArray: isTransfer ? '10, 5' : null,
                        className: 'planned-route-line'  // Add CSS class for styling
                    }).addTo(this.map);
                    
                    // Add white outline/border for better contrast
                    const outlinePolyline = L.polyline(stepCoordinates, {
                        color: '#ffffff',
                        weight: isTransfer ? 10 : 8,  // Slightly thicker than main line
                        opacity: 0.7,
                        dashArray: isTransfer ? '10, 5' : null,
                        className: 'planned-route-outline'
                    }).addTo(this.map);
                    
                    this.routePolylines.push(outlinePolyline);  // Add outline first (behind)
                    this.routePolylines.push(polyline);        // Add main line on top
                    
                    // Bring route lines to front to ensure they appear above metro infrastructure
                    outlinePolyline.bringToFront();
                    polyline.bringToFront();
                    allCoordinates.push(...stepCoordinates);
                    
                    // Add transfer marker if this is a transfer
                    if (isTransfer) {
                        const transferMarker = L.marker([fromStation.latitude, fromStation.longitude], {
                            icon: L.divIcon({
                                className: 'transfer-icon',
                                html: '🔄',
                                iconSize: [20, 20],
                                iconAnchor: [10, 10]
                            })
                        }).addTo(this.map);
                        
                        transferMarker.bindPopup(`Transfer: ${step.line} Line<br>${step.from_station}`);
                        this.transferMarkers.push(transferMarker);
                    }
                }
            }
        });
        
        // Fit map to show entire route
        if (allCoordinates.length > 0) {
            const bounds = L.latLngBounds(allCoordinates);
            this.map.fitBounds(bounds, {padding: [20, 20]});
        }
        
        // Add legend
        this.addRouteLegend(routeData.lines_used);
    }
    
    getStationsOnLine(fromStation, toStation, line, lineSequences) {
        const sequence = lineSequences[line];
        if (!sequence) return [fromStation, toStation];
        
        const fromIndex = sequence.indexOf(fromStation);
        const toIndex = sequence.indexOf(toStation);
        
        if (fromIndex === -1 || toIndex === -1) {
            return [fromStation, toStation];
        }
        
        // Get the stations between from and to (inclusive)
        const startIndex = Math.min(fromIndex, toIndex);
        const endIndex = Math.max(fromIndex, toIndex);
        
        return sequence.slice(startIndex, endIndex + 1);
    }
    
    drawSimpleRoute(path) {
        console.log('Drawing simple route with path:', path);
        // Get coordinates for path stations
        const pathCoordinates = path.map(stationId => {
            const station = this.stations.find(s => s.station_id === stationId);
            if (station) {
                console.log(`Station ${stationId}: ${station.name} at [${station.latitude}, ${station.longitude}]`);
                return [station.latitude, station.longitude];
            } else {
                console.warn(`Station not found for ID: ${stationId}`);
                return null;
            }
        }).filter(coord => coord !== null);
        
        console.log('Path coordinates:', pathCoordinates);
        
        if (pathCoordinates.length > 1) {
            console.log('Creating polylines for route visualization');
            // Draw outline polyline first (white border for contrast)
            const outlinePolyline = L.polyline(pathCoordinates, {
                color: '#ffffff',
                weight: 8,  // Increased outline weight
                opacity: 0.8,  // Increased outline opacity
                className: 'planned-route-outline'
            }).addTo(this.map);
            
            // Draw main polyline for route on top
            this.routePolyline = L.polyline(pathCoordinates, {
                color: '#ff0066',  // Bright magenta/pink for high visibility
                weight: 6,  // Increased main line weight
                opacity: 1.0,  // Full opacity
                className: 'planned-route-line'
            }).addTo(this.map);
            
            this.routePolylines = [outlinePolyline, this.routePolyline];
            
            // Bring route lines to front to ensure they appear above metro infrastructure
            outlinePolyline.bringToFront();
            this.routePolyline.bringToFront();
            
            console.log('Route polylines created and brought to front');
            
            // Fit map to show entire route
            this.map.fitBounds(this.routePolyline.getBounds(), {padding: [20, 20]});
        } else {
            console.error('Not enough coordinates to draw route');
        }
    }
    
    addRouteLegend(linesUsed) {
        // Remove existing legend
        if (this.routeLegend) {
            this.map.removeControl(this.routeLegend);
        }
        
        if (!linesUsed || linesUsed.length === 0) return;
        
        const lineColors = {
            'KJL': '#1f77b4',
            'SBK': '#ff7f0e'
        };
        
        const lineNames = {
            'KJL': 'Kelana Jaya Line',
            'SBK': 'Sungai Buloh-Kajang Line'
        };
        
        this.routeLegend = L.control({position: 'topright'});
        
        this.routeLegend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'route-legend');
            div.innerHTML = '<h4>Route Lines</h4>';
            
            linesUsed.forEach(line => {
                const color = lineColors[line] || '#33ff33';
                const name = lineNames[line] || line;
                div.innerHTML += `
                    <div class="legend-item">
                        <span class="legend-line" style="background-color: ${color}"></span>
                        ${name}
                    </div>
                `;
            });
            
            return div;
        };
        
        this.routeLegend.addTo(this.map);
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

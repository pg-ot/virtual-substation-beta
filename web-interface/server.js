const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.static('public'));

// Simulation data
let simulationData = {
    voltage: 132.0,
    current: 450.0,
    frequency: 50.0,
    faultCurrent: 0.0,
    faultDetected: false,
    tripCommand: false,
    breakerStatus: false
};

// Add CORS headers for all responses
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// API endpoints
app.get('/api/simulation-data', (req, res) => {
    res.json(simulationData);
});

app.post('/api/command', (req, res) => {
    const { command, data } = req.body;
    
    switch(command) {
        case 'updateVoltage':
            simulationData.voltage = data.voltage;
            break;
        case 'updateCurrent':
            simulationData.current = data.current;
            break;
        case 'updateFrequency':
            simulationData.frequency = data.frequency;
            break;
        case 'updateFaultCurrent':
            simulationData.faultCurrent = data.faultCurrent;
            break;
        case 'toggleFault':
            simulationData.faultDetected = data.active;
            break;
        case 'toggleBreaker':
            simulationData.breakerStatus = data.open;
            break;
        case 'sendTrip':
            simulationData.tripCommand = true;
            simulationData.breakerStatus = true;  // Manual trip opens breaker
            setTimeout(() => {
                simulationData.tripCommand = false;
                simulationData.breakerStatus = false;  // Reset after trip
            }, 3000);
            break;
        case 'resetTrip':
            simulationData.tripCommand = false;
            simulationData.faultDetected = false;
            simulationData.current = 450.0;  // Reset to normal current
            simulationData.faultCurrent = 0.0;
            break;
        case 'toggleManualTrip':
            simulationData.tripCommand = data.active;
            break;
    }
    
    console.log(`Command received: ${command}`, data);
    console.log('Updated simulation data:', simulationData);
    
    res.json({ success: true, data: simulationData });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Web interface running on port ${PORT}`);
});
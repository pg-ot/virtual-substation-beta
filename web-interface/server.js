const express = require('express');
const path = require('path');
const http = require('http');
const WebSocket = require('ws');
// Using built-in fetch API available in Node.js 18+

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
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

// IED status data
let iedStatus = {
    protectionRelay: { status: 'offline', voltage: 132.0, current: 450.0, frequency: 50.0, faultDetected: false, tripCommand: false, breakerStatus: false, overcurrentPickup: false },
    circuitBreaker: { status: 'offline', tripReceived: false, stateNumber: 0, sequenceNumber: 0 },
    gooseRxOk: false,
    reportsEnabled: false,
    lastUpdated: 0
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

// Diagnostics proxy: fetch HMI diagnostics and return merged view
app.get('/api/diagnostics', async (req, res) => {
    try {
        const response = await fetch('http://hmi-scada:8080/diagnostics');
        if (!response.ok) return res.json({ error: 'hmi_unreachable' });
        const diag = await response.json();
        return res.json(diag);
    } catch (e) {
        return res.json({ error: 'hmi_error' });
    }
});

// SOE proxy
app.get('/api/soe', async (req, res) => {
    try {
        const response = await fetch('http://hmi-scada:8080/soe');
        if (!response.ok) return res.json([]);
        const soe = await response.json();
        return res.json(soe);
    } catch (e) {
        return res.json([]);
    }
});

// IED status snapshot
app.get('/api/ied-status', (req, res) => {
    res.json(iedStatus);
});

// Run orchestrated end-to-end tests
app.post('/api/run-tests', async (req, res) => {
  try {
    const results = [];
    const start = Date.now();

    const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    async function readHmiData() {
        try {
            const r = await fetch('http://hmi-scada:8080/data');
            return r.ok ? await r.json() : null;
        } catch (e) {
            return null;
        }
    }
    async function diag() {
        const r = await fetch('http://hmi-scada:8080/diagnostics');
        return r.ok ? await r.json() : null;
    }
    async function hmi(cmd) {
        return fetch(`http://hmi-scada:8080/${cmd}`, { method: 'POST' }).then(r => r.ok).catch(() => false);
    }
    function setVal(cmd, data) { handleCommand(cmd, data); }

    async function awaitCond(predicate, timeoutMs = 4000, pollMs = 100) {
        const t0 = Date.now();
        while (Date.now() - t0 < timeoutMs) {
            const d = await readHmiData();
            if (d && predicate(d)) return { ok: true, data: d, elapsed: Date.now() - t0 };
            await sleep(pollMs);
        }
        const d = await readHmiData();
        return { ok: false, data: d, elapsed: Date.now() - t0 };
    }

    // Normalize
    setVal('updateCurrent', { current: 450.0 });
    setVal('updateFaultCurrent', { faultCurrent: 0.0 });
    setVal('updateFrequency', { frequency: 50.0 });
    setVal('toggleFault', { active: false });
    await hmi('reset');
    await hmi('close');
    await sleep(300);
    results.push({ name: 'Normalize', ...(await awaitCond(d => !d.faultDetected && !d.tripCommand, 5000)) });

    // 51 Overcurrent (pickup then trip after ~1s)
    setVal('updateCurrent', { current: 1500 });
    const pickup = await awaitCond(d => d.overcurrentPickup === true, 1500);
    const trip51 = await awaitCond(d => d.breakerStatus === true, 4000); // true=open
    results.push({ name: '51 Overcurrent pickup', ...pickup });
    results.push({ name: '51 Overcurrent trip', ...trip51 });
    await hmi('reset'); await hmi('close'); await sleep(300);

    // 50 Instantaneous (>2500A)
    setVal('updateCurrent', { current: 2600 });
    const trip50 = await awaitCond(d => d.breakerStatus === true, 2000);
    results.push({ name: '50 Instantaneous OC trip', ...trip50 });
    await hmi('reset'); await hmi('close'); await sleep(300);

    // 51G Ground fault (300-799A -> 0.5s delay)
    setVal('updateFaultCurrent', { faultCurrent: 400 });
    setVal('toggleFault', { active: true });
    const trip51g = await awaitCond(d => d.breakerStatus === true, 3000);
    results.push({ name: '51G Ground fault trip', ...trip51g });
    setVal('toggleFault', { active: false });
    await hmi('reset'); await hmi('close'); await sleep(300);

    // 81U Underfrequency (<48.5 Hz)
    setVal('updateFrequency', { frequency: 48.0 });
    const trip81u = await awaitCond(d => d.breakerStatus === true, 2000);
    results.push({ name: '81U Underfrequency trip', ...trip81u });
    setVal('updateFrequency', { frequency: 50.0 });
    await hmi('reset'); await hmi('close'); await sleep(300);

    // Final normal check (extra reset/close and longer window)
    await hmi('reset'); await hmi('close'); await sleep(500);
    const final = await awaitCond(d => !d.faultDetected && !d.tripCommand && d.breakerStatus === false, 6000);
    results.push({ name: 'Return to normal', ...final });

    const summary = {
        ok: results.every(r => r.ok),
        durationMs: Date.now() - start,
        results
    };
    res.json(summary);
  } catch (e) {
    console.error('run-tests failed:', e);
    res.status(500).json({ ok: false, error: 'run_failed', message: String(e) });
  }
});

// Add IED status endpoint for fallback
app.get('/api/ied-status', (req, res) => {
    res.json(iedStatus);
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

// WebSocket connections
wss.on('connection', (ws) => {
    console.log('WebSocket client connected');
    
    // Send initial data
    ws.send(JSON.stringify({ type: 'iedUpdate', data: iedStatus }));
    
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            if (data.type === 'command') {
                handleCommand(data.command, data.data);
            }
        } catch (error) {
            console.error('WebSocket message error:', error);
        }
    });
    
    ws.on('close', () => {
        console.log('WebSocket client disconnected');
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

console.log('WebSocket server listening on port 3000');

// Function to handle commands
function handleCommand(command, data) {
    switch(command) {
        case 'updateVoltage':
            simulationData.voltage = data.voltage;
            iedStatus.protectionRelay.voltage = data.voltage;
            break;
        case 'updateCurrent':
            simulationData.current = data.current;
            iedStatus.protectionRelay.current = data.current;
            break;
        case 'updateFrequency':
            simulationData.frequency = data.frequency;
            iedStatus.protectionRelay.frequency = data.frequency;
            break;
        case 'updateFaultCurrent':
            simulationData.faultCurrent = data.faultCurrent;
            break;
        case 'toggleFault':
            simulationData.faultDetected = data.active;
            iedStatus.protectionRelay.faultDetected = data.active;
            break;
        case 'toggleBreaker':
            simulationData.breakerStatus = data.open;
            iedStatus.protectionRelay.breakerStatus = data.open;
            break;
        case 'sendTrip':
            simulationData.tripCommand = true;
            iedStatus.protectionRelay.tripCommand = true;
            iedStatus.protectionRelay.breakerStatus = true;
            setTimeout(() => {
                simulationData.tripCommand = false;
                iedStatus.protectionRelay.tripCommand = false;
            }, 3000);
            break;
        case 'resetTrip':
            simulationData.tripCommand = false;
            simulationData.faultDetected = false;
            simulationData.current = 450.0;
            simulationData.faultCurrent = 0.0;
            iedStatus.protectionRelay.tripCommand = false;
            iedStatus.protectionRelay.faultDetected = false;
            iedStatus.protectionRelay.current = 450.0;
            break;
        case 'toggleManualTrip':
            simulationData.tripCommand = data.active;
            iedStatus.protectionRelay.tripCommand = data.active;
            break;
    }
    
    // Broadcast update to all clients
    broadcastUpdate();
}

// Function to broadcast updates to all WebSocket clients
function broadcastUpdate() {
    const message = JSON.stringify({ type: 'iedUpdate', data: iedStatus });
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Function to check IED status via HMI server
async function checkIEDStatus() {
    try {
        const response = await fetch('http://hmi-scada:8080/diagnostics');
        if (response.ok) {
            const diagnostics = await response.json();
            console.log('IED Diagnostics:', diagnostics);
            iedStatus.protectionRelay.status = diagnostics.protectionRelay === 'ONLINE' ? 'online' : 'offline';
            iedStatus.circuitBreaker.status = diagnostics.circuitBreaker === 'ONLINE' ? 'online' : 'offline';
            iedStatus.gooseRxOk = !!diagnostics.gooseRxOk;
            iedStatus.reportsEnabled = !!diagnostics.reportsEnabled;
            
            // Get real-time data from HMI server
            const dataResponse = await fetch('http://hmi-scada:8080/data');
            if (dataResponse.ok) {
                const realTimeData = await dataResponse.json();
                iedStatus.protectionRelay.voltage = realTimeData.voltage || simulationData.voltage;
                iedStatus.protectionRelay.current = realTimeData.current || simulationData.current;
                iedStatus.protectionRelay.frequency = realTimeData.frequency || simulationData.frequency;
                iedStatus.protectionRelay.faultDetected = realTimeData.faultDetected || simulationData.faultDetected;
                iedStatus.protectionRelay.tripCommand = realTimeData.tripCommand || simulationData.tripCommand;
                iedStatus.protectionRelay.breakerStatus = realTimeData.breakerStatus || simulationData.breakerStatus;
                iedStatus.protectionRelay.overcurrentPickup = !!realTimeData.overcurrentPickup;
                console.log('IED Status Updated:', iedStatus.protectionRelay.status, iedStatus.circuitBreaker.status);
            }

            // Fetch breaker GOOSE counters from breaker HTTP API
            try {
                const brResp = await fetch('http://circuit_breaker_ied:8081/status');
                if (brResp.ok) {
                    const br = await brResp.json();
                    iedStatus.circuitBreaker.stateNumber = br.stNum || 0;
                    iedStatus.circuitBreaker.sequenceNumber = br.sqNum || 0;
                    iedStatus.circuitBreaker.messageCount = br.messageCount || 0;
                    iedStatus.circuitBreaker.lastGooseTime = br.lastTime || '--:--:--';
                }
            } catch (e) {
                // ignore
            }
        } else {
            console.log('HMI server not responding, setting IEDs offline');
            iedStatus.protectionRelay.status = 'offline';
            iedStatus.circuitBreaker.status = 'offline';
            iedStatus.gooseRxOk = false;
            iedStatus.reportsEnabled = false;
        }
    } catch (error) {
        console.error('Error checking IED status:', error);
        iedStatus.protectionRelay.status = 'offline';
        iedStatus.circuitBreaker.status = 'offline';
        iedStatus.gooseRxOk = false;
        iedStatus.reportsEnabled = false;
    }
    iedStatus.lastUpdated = Date.now();
    
    broadcastUpdate();
}

// Check IED status every 2 seconds
setInterval(checkIEDStatus, 2000);

// Initial status check
checkIEDStatus();

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Web interface running on port ${PORT}`);
});

// On-demand refresh endpoint
app.post('/api/refresh-status', async (req, res) => {
    try {
        await checkIEDStatus();
        res.json({ ok: true, data: iedStatus });
    } catch (e) {
        res.status(500).json({ ok: false });
    }
});

/**
 * Microservice Health Monitor — Dashboard Application
 * Real-time polling, sparkline charts, incident tracking
 */

// =========================================================================
// Configuration
// =========================================================================
const CONFIG = {
    // Base URL for services — change to your EC2 Public DNS when deployed
    // Example: 'http://ec2-13-233-100-200.ap-south-1.compute.amazonaws.com'
    baseUrl: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? '' // local dev — use relative URLs with port overrides
        : 'http://ec2-13-235-45-199.ap-south-1.compute.amazonaws.com', // REPLACE THIS WITH EC2 PUBLIC DNS WHEN DEPLOYED

    services: [
        {
            name: 'user-service',
            displayName: 'User Service',
            icon: '👤',
            healthPath: '/api/users/health',
            localPort: 5001,
            accentColor: '#6C5CE7',
        },
        {
            name: 'order-service',
            displayName: 'Order Service',
            icon: '📦',
            healthPath: '/api/orders/health',
            localPort: 5002,
            accentColor: '#00D2D3',
        },
        {
            name: 'notification-service',
            displayName: 'Notification Service',
            icon: '🔔',
            healthPath: '/api/notifications/health',
            localPort: 5003,
            accentColor: '#FD79A8',
        },
    ],

    pollIntervalMs: 10000,      // 10 seconds
    maxHistory: 30,             // sparkline data points
    maxIncidents: 50,           // max incidents in log
    responseTimeThreshold: 500, // ms — above this is "degraded"
    demoMode: false,            // when true, simulates data (for portfolio demos)
};

// =========================================================================
// State
// =========================================================================
const state = {
    services: {},     // keyed by service name
    incidents: [],
    checkCount: 0,
    isPolling: false,
};

// Initialize state for each service
CONFIG.services.forEach(svc => {
    state.services[svc.name] = {
        status: 'unknown',       // healthy | degraded | down | unknown
        lastResponse: null,      // last health check response data
        responseTimeMs: 0,
        responseHistory: [],     // array of { time, ms }
        uptime: 100,
        checksTotal: 0,
        checksHealthy: 0,
        lastCheckTime: null,
    };
});

// =========================================================================
// DOM Utilities
// =========================================================================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function formatUptime(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
    return `${(seconds / 86400).toFixed(1)}d`;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// =========================================================================
// Service Card Rendering
// =========================================================================
function renderServiceCards() {
    const grid = $('#services-grid');
    grid.innerHTML = '';

    CONFIG.services.forEach(svc => {
        const svcState = state.services[svc.name];
        const card = document.createElement('div');
        card.className = `service-card status-${svcState.status}`;
        card.id = `card-${svc.name}`;
        card.style.setProperty('--card-accent', svc.accentColor);

        card.innerHTML = `
            <div class="service-card-header">
                <div class="service-name-group">
                    <div class="service-icon">${svc.icon}</div>
                    <div>
                        <div class="service-name">${svc.displayName}</div>
                        <div class="service-endpoint">${svc.healthPath}</div>
                    </div>
                </div>
                <div class="status-badge ${svcState.status}" id="badge-${svc.name}">
                    <span class="badge-dot"></span>
                    <span>${svcState.status}</span>
                </div>
            </div>
            <div class="service-metrics">
                <div class="metric">
                    <span class="metric-value" id="rt-${svc.name}">${svcState.responseTimeMs ? svcState.responseTimeMs + 'ms' : '--'}</span>
                    <span class="metric-label">Response</span>
                </div>
                <div class="metric">
                    <span class="metric-value" id="uptime-${svc.name}">${svcState.uptime.toFixed(1)}%</span>
                    <span class="metric-label">Uptime</span>
                </div>
                <div class="metric">
                    <span class="metric-value" id="version-${svc.name}">${svcState.lastResponse?.version || '--'}</span>
                    <span class="metric-label">Version</span>
                </div>
            </div>
            <div class="sparkline-container">
                <canvas id="spark-${svc.name}"></canvas>
            </div>
        `;

        grid.appendChild(card);
    });
}

// =========================================================================
// Sparkline Drawing
// =========================================================================
function drawSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || data.length < 2) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = 4;

    const values = data.map(d => d.ms);
    const max = Math.max(...values, 100);
    const min = Math.min(...values, 0);
    const range = max - min || 1;

    ctx.clearRect(0, 0, w, h);

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, color + '30');
    gradient.addColorStop(1, color + '05');

    // Draw fill
    ctx.beginPath();
    ctx.moveTo(padding, h - padding);

    for (let i = 0; i < values.length; i++) {
        const x = padding + (i / (values.length - 1)) * (w - padding * 2);
        const y = h - padding - ((values[i] - min) / range) * (h - padding * 2);
        if (i === 0) ctx.lineTo(x, y);
        else ctx.lineTo(x, y);
    }

    ctx.lineTo(w - padding, h - padding);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    for (let i = 0; i < values.length; i++) {
        const x = padding + (i / (values.length - 1)) * (w - padding * 2);
        const y = h - padding - ((values[i] - min) / range) * (h - padding * 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();

    // Draw latest dot
    if (values.length > 0) {
        const lastX = w - padding;
        const lastY = h - padding - ((values[values.length - 1] - min) / range) * (h - padding * 2);
        ctx.beginPath();
        ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
        ctx.fillStyle = color + '30';
        ctx.fill();
    }
}

// =========================================================================
// Response Time Chart (main chart)
// =========================================================================
function drawResponseChart() {
    const canvas = document.getElementById('response-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    ctx.clearRect(0, 0, w, h);

    // Find max across all services
    let allValues = [];
    CONFIG.services.forEach(svc => {
        const history = state.services[svc.name].responseHistory;
        history.forEach(d => allValues.push(d.ms));
    });

    const maxVal = Math.max(...allValues, 200);
    const yScale = chartH / maxVal;

    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(w - padding.right, y);
        ctx.stroke();

        // Labels
        const val = Math.round(maxVal - (maxVal / gridLines) * i);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.font = '11px "JetBrains Mono"';
        ctx.textAlign = 'right';
        ctx.fillText(`${val}ms`, padding.left - 8, y + 4);
    }

    // Draw lines for each service
    CONFIG.services.forEach((svc, svcIdx) => {
        const history = state.services[svc.name].responseHistory;
        if (history.length < 2) return;

        const maxPoints = CONFIG.maxHistory;
        const points = history.slice(-maxPoints);

        ctx.beginPath();
        for (let i = 0; i < points.length; i++) {
            const x = padding.left + (i / (maxPoints - 1)) * chartW;
            const y = padding.top + chartH - points[i].ms * yScale;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = svc.accentColor;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.stroke();

        // Legend dot
        const legendX = padding.left + svcIdx * 160;
        const legendY = h - 8;
        ctx.beginPath();
        ctx.arc(legendX, legendY, 4, 0, Math.PI * 2);
        ctx.fillStyle = svc.accentColor;
        ctx.fill();
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '11px "Inter"';
        ctx.textAlign = 'left';
        ctx.fillText(svc.displayName, legendX + 10, legendY + 4);
    });
}

// =========================================================================
// Summary Bar Update
// =========================================================================
function updateSummaryBar() {
    let healthy = 0, degraded = 0, down = 0;
    let totalUptime = 0;

    CONFIG.services.forEach(svc => {
        const s = state.services[svc.name];
        if (s.status === 'healthy') healthy++;
        else if (s.status === 'degraded') degraded++;
        else if (s.status === 'down') down++;
        totalUptime += s.uptime;
    });

    $('#healthy-count').textContent = healthy;
    $('#degraded-count').textContent = degraded;
    $('#down-count').textContent = down;
    $('#avg-uptime').textContent = (totalUptime / CONFIG.services.length).toFixed(1) + '%';
}

// =========================================================================
// Incident Log
// =========================================================================
function addIncident(type, service, message) {
    const incident = {
        type,    // 'down' | 'degraded' | 'recovered'
        service,
        message,
        time: new Date(),
    };

    state.incidents.unshift(incident);
    if (state.incidents.length > CONFIG.maxIncidents) {
        state.incidents.pop();
    }

    renderIncidents();
}

function renderIncidents() {
    const log = $('#incident-log');
    const countBadge = $('#incident-count');

    if (state.incidents.length === 0) {
        log.innerHTML = `
            <div class="incident-empty">
                <span>🎉</span>
                <p>No incidents recorded. All services nominal.</p>
            </div>
        `;
        countBadge.textContent = '0 events';
        return;
    }

    countBadge.textContent = `${state.incidents.length} events`;
    log.innerHTML = state.incidents.map(inc => `
        <div class="incident-item">
            <div class="incident-dot dot-${inc.type}"></div>
            <div class="incident-details">
                <div class="incident-message">${inc.message}</div>
                <div class="incident-time">${formatTime(inc.time)}</div>
            </div>
        </div>
    `).join('');
}

// =========================================================================
// Health Check — Real or Simulated
// =========================================================================
async function checkServiceHealth(svcConfig) {
    const svcState = state.services[svcConfig.name];
    const prevStatus = svcState.status;
    const startTime = performance.now();

    try {
        let url;
        if (CONFIG.demoMode) {
            // In demo mode, simulate responses
            return simulateHealthCheck(svcConfig, svcState, prevStatus);
        }

        // Real mode: determine URL based on environment
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        if (isLocal && !CONFIG.baseUrl) {
            url = `http://localhost:${svcConfig.localPort}${svcConfig.healthPath}`;
        } else {
            // Use baseUrl + path (e.g. EC2 public DNS + /api/users/health)
            url = `${CONFIG.baseUrl}${svcConfig.healthPath}`;
        }

        const response = await fetch(url, {
            signal: AbortSignal.timeout(5000),
        });

        const elapsed = Math.round(performance.now() - startTime);
        const data = await response.json();

        svcState.responseTimeMs = elapsed;
        svcState.lastResponse = data;
        svcState.lastCheckTime = new Date();
        svcState.checksTotal++;

        if (response.ok && data.status === 'healthy') {
            svcState.checksHealthy++;
            svcState.status = elapsed > CONFIG.responseTimeThreshold ? 'degraded' : 'healthy';
        } else {
            svcState.status = 'degraded';
        }

    } catch (error) {
        svcState.status = 'down';
        svcState.responseTimeMs = 0;
        svcState.lastCheckTime = new Date();
        svcState.checksTotal++;
    }

    // Track history
    svcState.responseHistory.push({
        time: new Date(),
        ms: svcState.responseTimeMs,
    });
    if (svcState.responseHistory.length > CONFIG.maxHistory) {
        svcState.responseHistory.shift();
    }

    // Calculate uptime
    svcState.uptime = svcState.checksTotal > 0
        ? (svcState.checksHealthy / svcState.checksTotal) * 100
        : 100;

    // Detect status transitions
    if (prevStatus !== svcState.status && prevStatus !== 'unknown') {
        if (svcState.status === 'down') {
            addIncident('down', svcConfig.name, `${svcConfig.displayName} is DOWN — service unreachable`);
        } else if (svcState.status === 'degraded') {
            addIncident('degraded', svcConfig.name, `${svcConfig.displayName} is DEGRADED — high response time (${svcState.responseTimeMs}ms)`);
        } else if (svcState.status === 'healthy' && (prevStatus === 'down' || prevStatus === 'degraded')) {
            addIncident('recovered', svcConfig.name, `${svcConfig.displayName} has RECOVERED`);
        }
    }
}

// =========================================================================
// Demo Mode — Simulated Health Data
// =========================================================================
function simulateHealthCheck(svcConfig, svcState, prevStatus) {
    // Simulate realistic response times with occasional spikes
    const baseTime = 30 + Math.random() * 60; // 30-90ms
    const spike = Math.random() < 0.05 ? 300 + Math.random() * 200 : 0; // 5% chance of spike
    const downChance = Math.random() < 0.02; // 2% chance of going down

    if (downChance && state.checkCount > 5) {
        svcState.status = 'down';
        svcState.responseTimeMs = 0;
        svcState.checksTotal++;
    } else {
        const responseTime = Math.round(baseTime + spike);
        svcState.responseTimeMs = responseTime;
        svcState.checksTotal++;
        svcState.checksHealthy++;
        svcState.status = responseTime > CONFIG.responseTimeThreshold ? 'degraded' : 'healthy';

        svcState.lastResponse = {
            service: svcConfig.name,
            status: 'healthy',
            version: '1.0.0',
            uptime_seconds: state.checkCount * (CONFIG.pollIntervalMs / 1000),
            timestamp: new Date().toISOString(),
        };
    }

    svcState.lastCheckTime = new Date();

    // Track history
    svcState.responseHistory.push({
        time: new Date(),
        ms: svcState.responseTimeMs || (svcState.status === 'down' ? 0 : 50),
    });
    if (svcState.responseHistory.length > CONFIG.maxHistory) {
        svcState.responseHistory.shift();
    }

    // Uptime
    svcState.uptime = svcState.checksTotal > 0
        ? (svcState.checksHealthy / svcState.checksTotal) * 100
        : 100;

    // Detect transitions
    if (prevStatus !== svcState.status && prevStatus !== 'unknown') {
        if (svcState.status === 'down') {
            addIncident('down', svcConfig.name, `${svcConfig.displayName} is DOWN — service unreachable`);
        } else if (svcState.status === 'degraded') {
            addIncident('degraded', svcConfig.name, `${svcConfig.displayName} is DEGRADED — high latency (${svcState.responseTimeMs}ms)`);
        } else if (svcState.status === 'healthy' && (prevStatus === 'down' || prevStatus === 'degraded')) {
            addIncident('recovered', svcConfig.name, `${svcConfig.displayName} has RECOVERED`);
        }
    }
}

// =========================================================================
// Update UI After Health Check
// =========================================================================
function updateServiceCard(svcConfig) {
    const svcState = state.services[svcConfig.name];
    const card = document.getElementById(`card-${svcConfig.name}`);
    if (!card) return;

    // Update card status class
    card.className = `service-card status-${svcState.status}`;

    // Update badge
    const badge = document.getElementById(`badge-${svcConfig.name}`);
    if (badge) {
        badge.className = `status-badge ${svcState.status}`;
        badge.innerHTML = `<span class="badge-dot"></span><span>${svcState.status}</span>`;
    }

    // Update metrics
    const rtEl = document.getElementById(`rt-${svcConfig.name}`);
    if (rtEl) {
        rtEl.textContent = svcState.responseTimeMs ? `${svcState.responseTimeMs}ms` : '--';
    }

    const uptimeEl = document.getElementById(`uptime-${svcConfig.name}`);
    if (uptimeEl) {
        uptimeEl.textContent = `${svcState.uptime.toFixed(1)}%`;
    }

    const versionEl = document.getElementById(`version-${svcConfig.name}`);
    if (versionEl) {
        versionEl.textContent = svcState.lastResponse?.version || '--';
    }

    // Draw sparkline
    drawSparkline(`spark-${svcConfig.name}`, svcState.responseHistory, svcConfig.accentColor);
}

// =========================================================================
// Main Poll Loop
// =========================================================================
async function pollAll() {
    state.checkCount++;

    // Check all services in parallel
    await Promise.all(CONFIG.services.map(svc => checkServiceHealth(svc)));

    // Update UI
    CONFIG.services.forEach(svc => updateServiceCard(svc));
    updateSummaryBar();
    drawResponseChart();

    // Update header
    const now = new Date();
    $('#last-check').textContent = `Last check: ${formatTime(now)}`;
}

function startPolling() {
    if (state.isPolling) return;
    state.isPolling = true;

    // Initial check
    pollAll();

    // Continue polling
    setInterval(pollAll, CONFIG.pollIntervalMs);
}

// =========================================================================
// Initialization
// =========================================================================
function init() {
    renderServiceCards();
    renderIncidents();
    startPolling();

    // Resize handler for charts
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            CONFIG.services.forEach(svc => {
                drawSparkline(`spark-${svc.name}`, state.services[svc.name].responseHistory, svc.accentColor);
            });
            drawResponseChart();
        }, 150);
    });

    console.log(
        '%c🏥 Microservice Health Monitor %cv1.0.0',
        'color: #6C5CE7; font-size: 16px; font-weight: bold;',
        'color: #00D2D3; font-size: 12px;'
    );
    console.log(
        `%cMode: ${CONFIG.demoMode ? 'Demo (simulated data)' : 'Live (polling services)'}`,
        'color: #94a3b8; font-size: 11px;'
    );
    console.log(
        '%cTo switch to live mode, set CONFIG.demoMode = false in app.js',
        'color: #94a3b8; font-size: 11px;'
    );
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);

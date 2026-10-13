/* ==========================================================================
   Golden Hour Grid — Frontend Application Engine
   Role-Based Coordination, Real Road Map, Live Telemetry & Clinical Dossier
   Ref: docs/REAL_MAP_AND_ROUTING.md & docs/UI_DESIGN_REFERENCE_TNEA.md
   ========================================================================== */

const $ = id => document.getElementById(id);

const BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

// Real geographic coordinates for predefined locations (Chennai metropolitan area)
const LOCATIONS = {
  "Central Junction": [13.0827, 80.2707],
  "Tech Park": [12.9863, 80.2432],
  "Old Bazaar": [13.0878, 80.2785],
  "Highway Toll": [13.0067, 80.0526],
  "University Gate": [13.0113, 80.2354],
  "Port Junction": [13.0970, 80.2925],
  "North Market": [13.1143, 80.2872],
  "Railway Colony": [13.0833, 80.2348],
  "Riverside Road": [13.0732, 80.2609],
  "East Flyover": [13.0405, 80.2505],
  "South Industrial": [12.9915, 80.1693],
  "Hill Station / Ghat Road": [12.9516, 79.9410]
};

const SPECIALTY_NAMES = {
  trauma: "Trauma surgeon",
  neuro: "Neurosurgeon",
  cardiac: "Cardiologist",
  ortho: "Orthopaedic surgeon",
  burns: "Burns specialist"
};

const EMERGENCY_PRESETS = [
  ["🧠 Head injury", "neuro", "Critical"],
  ["🩸 Heavy bleeding", "trauma", "High"],
  ["❤️ Chest pain", "cardiac", "High"],
  ["🔥 Burns", "burns", "High"],
  ["🦴 Fracture", "ortho", "Moderate"]
];

// Global Application State
let currentUser = null;
let allHospitals = [];
let activeIncident = null;
let activeRanking = null;
let selectedHospital = null;
let mapStatus = null;
let leafletMap = null;
let leafletHospitalMap = null;
let leafletDossierMap = null;
let mapLayers = { markers: [], polylines: [] };
let hospMapLayers = { markers: [], polylines: [] };
let dossierMapLayers = { markers: [], polylines: [] };
let ws = null;
let pollTimer = null;
let clockInterval = null;

// Real-Time Road Simulation State
let simState = {
  active: false,
  paused: false,
  speedMultiplier: 1,
  currentIndex: 0,
  routePoints: [],
  totalDistanceKm: 12.0,
  totalDurationMins: 18.0,
  ambulanceMarker: null,
  traversedPolyline: null,
  remainingPolyline: null,
  timerId: null
};

// Hospital Active Dossier State
let activeDossierCase = null;

// ==========================================
// 1. AUTHENTICATION & NAVIGATION
// ==========================================

async function checkAuth() {
  try {
    const res = await fetch("/api/auth/me");
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      showWorkspace(currentUser.role);
      initRealtime();
      return;
    }
  } catch (err) {
    console.warn("Auth check failed:", err);
  }
  currentUser = null;
  showWorkspace("login");
}

function showWorkspace(view) {
  $("view-login").classList.remove("active");
  $("view-ambulance").classList.remove("active");
  $("view-hospital").classList.remove("active");

  const userDisplay = $("user-display");
  const connBadge = $("conn-badge");

  if (view === "ambulance") {
    $("view-ambulance").classList.add("active");
    userDisplay.style.display = "flex";
    connBadge.style.display = "flex";
    $("user-role-icon").textContent = "🚑";
    $("user-name-tag").textContent = `${currentUser.username} (Ambulance)`;
    window.history.replaceState({}, "", "/ambulance");
    initAmbulanceWorkspace();
  } else if (view === "hospital") {
    $("view-hospital").classList.add("active");
    userDisplay.style.display = "flex";
    connBadge.style.display = "flex";
    $("user-role-icon").textContent = "🏥";
    $("user-name-tag").textContent = `${currentUser.username} (Hospital)`;
    window.history.replaceState({}, "", "/hospital");
    initHospitalWorkspace();
  } else {
    $("view-login").classList.add("active");
    userDisplay.style.display = "none";
    connBadge.style.display = "none";
    window.history.replaceState({}, "", "/login");
    if (ws) { ws.close(); ws = null; }
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }
}

// Login Form Submit Handler
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = $("login-username").value.trim();
  const password = $("login-password").value;
  const errorBox = $("login-error");
  errorBox.style.display = "none";

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const err = await res.json();
      errorBox.textContent = err.detail || "Authentication failed.";
      errorBox.style.display = "block";
      return;
    }

    const data = await res.json();
    currentUser = data.user;
    showWorkspace(currentUser.role);
    initRealtime();
  } catch (err) {
    errorBox.textContent = "Network error connecting to backend.";
    errorBox.style.display = "block";
  }
});

// Logout Button Handler
$("logout-btn").addEventListener("click", async () => {
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } catch (err) {
    console.error("Logout error:", err);
  }
  currentUser = null;
  showWorkspace("login");
});

// ==========================================
// 2. REALTIME WEBSOCKET & POLLING FALLBACK
// ==========================================

function initRealtime() {
  if (ws) { ws.close(); }
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${location.host}/ws/updates`;

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus(true);
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerEvent(msg);
      } catch (e) {
        console.warn("Non-JSON WS message:", event.data);
      }
    };

    ws.onclose = () => {
      setConnectionStatus(false);
      startPollingFallback();
    };

    ws.onerror = () => {
      setConnectionStatus(false);
      startPollingFallback();
    };
  } catch (err) {
    setConnectionStatus(false);
    startPollingFallback();
  }
}

function setConnectionStatus(isLive) {
  const badge = $("conn-badge");
  const text = $("conn-text");
  if (isLive) {
    badge.className = "status-badge live";
    text.textContent = "Live Sync";
  } else {
    badge.className = "status-badge offline";
    text.textContent = "Polling Fallback";
  }
}

function startPollingFallback() {
  if (pollTimer) return;
  pollTimer = setInterval(async () => {
    if (!currentUser) return;
    if (currentUser.role === "hospital") {
      await loadHospitalData();
      await loadIncomingCases();
    } else if (currentUser.role === "ambulance" && activeIncident) {
      await refreshRanking();
    }
  }, 10000);
}

function handleServerEvent(event) {
  const type = event.event_type;

  if (type === "hospital.resource_changed") {
    if (currentUser?.role === "ambulance" && activeIncident) {
      logStatus(`Live resource change at ${event.payload.hospital_name || event.entity_id}. Re-evaluating recommendations.`);
      refreshRanking();
    } else if (currentUser?.role === "hospital") {
      loadHospitalData();
    }
  } else if (type === "incident.hospital_selected") {
    if (currentUser?.role === "hospital" && currentUser.hospital_id === event.payload.selected_hospital_id) {
      logStatus(`Incoming emergency case assigned to your facility.`);
      loadIncomingCases();
    }
  } else if (type === "hospital.case_acknowledged" || type === "hospital.case_declined") {
    if (currentUser?.role === "hospital") {
      loadIncomingCases();
    }
  } else if (type === "hospital.doctor_dispatched") {
    if (currentUser?.role === "hospital" && activeDossierCase?.incident_id === event.payload.incident_id) {
      logStatus(`Attending doctor ${event.payload.specialist_doctor} paged and dispatched to ${event.payload.bay_number}.`);
    } else if (currentUser?.role === "ambulance") {
      logStatus(`Destination hospital dispatched attending doctor to emergency bay.`);
    }
  } else if (type === "hospital.handover_completed") {
    if (currentUser?.role === "hospital") {
      loadIncomingCases();
    } else if (currentUser?.role === "ambulance") {
      logStatus(`Handover successfully confirmed by emergency bay staff.`);
      updateMilestone(3);
    }
  } else if (type === "coordination.blood_request_updated") {
    if (currentUser?.role === "hospital") {
      loadHospitalData();
    }
  }
}

// ==========================================
// 3. REAL ROAD MAP CONTROLLER (Leaflet)
// ==========================================

async function initMapStatus() {
  if (mapStatus) return mapStatus;
  try {
    const res = await fetch("/api/map/status");
    if (res.ok) {
      mapStatus = await res.json();
      const statusBadge = $("map-provider-status");
      if (statusBadge) {
        statusBadge.textContent = mapStatus.map_provider === "google" ? "Google Maps Roadmap" : "OpenStreetMap Roadmap";
        statusBadge.className = "status-badge live";
      }
      const noticeElem = $("map-notice");
      if (noticeElem) {
        noticeElem.textContent = mapStatus.traffic_aware ? "Live Traffic Aware" : "Standard Street Network";
      }
    }
  } catch (e) {
    console.warn("Map status check error:", e);
  }
  return mapStatus;
}

function ensureLeafletMap(containerId = "interactive-map") {
  const container = $(containerId);
  if (!container || typeof L === "undefined") return null;

  if (containerId === "interactive-map") {
    if (!leafletMap) {
      leafletMap = L.map(containerId, {
        center: [13.06, 80.24],
        zoom: 13,
        zoomControl: true,
        attributionControl: true
      });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(leafletMap);
    }
    return leafletMap;
  } else if (containerId === "hospital-interactive-map") {
    if (!leafletHospitalMap) {
      leafletHospitalMap = L.map(containerId, {
        center: [13.06, 80.24],
        zoom: 13,
        zoomControl: false,
        attributionControl: true
      });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19
      }).addTo(leafletHospitalMap);
    }
    return leafletHospitalMap;
  }
}

// Generate densely spaced path coordinates along road segments for fluid animation
function generateDensePath(geometry, totalPoints = 140) {
  if (!geometry || geometry.length < 2) return geometry || [];
  const points = [];
  const segmentCount = geometry.length - 1;
  const pointsPerSeg = Math.max(3, Math.floor(totalPoints / segmentCount));

  for (let i = 0; i < segmentCount; i++) {
    const p1 = geometry[i];
    const p2 = geometry[i + 1];
    for (let s = 0; s < pointsPerSeg; s++) {
      const t = s / pointsPerSeg;
      const lat = p1[0] + (p2[0] - p1[0]) * t;
      const lng = p1[1] + (p2[1] - p1[1]) * t;
      points.push([lat, lng]);
    }
  }
  points.push(geometry[geometry.length - 1]);
  return points;
}

async function renderRealRoadMap(incidentCoords, hospitalCoords, targetHospId) {
  const map = ensureLeafletMap("interactive-map");
  if (!map) return;

  // Stop previous simulation
  stopSimulation();

  // Clear previous layers
  mapLayers.markers.forEach(m => map.removeLayer(m));
  mapLayers.polylines.forEach(p => map.removeLayer(p));
  mapLayers.markers = [];
  mapLayers.polylines = [];

  // Plot candidate hospitals
  allHospitals.forEach(h => {
    if (h.latitude && h.longitude) {
      const isSelected = h.id === targetHospId;
      const markerColor = isSelected ? "#0b6f53" : "#1d4ed8";
      const iconHtml = `<div style="background:${markerColor};color:#fff;border:2px solid #fff;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 2px 4px rgba(0,0,0,0.3)">🏥</div>`;
      const customIcon = L.divIcon({ html: iconHtml, className: "", iconSize: [24, 24], iconAnchor: [12, 12] });
      const marker = L.marker([h.latitude, h.longitude], { icon: customIcon }).addTo(map);
      marker.bindPopup(`<b>${h.name}</b><br>ICU: ${h.icu_available} beds · Status: ${h.accepting_status}`);
      mapLayers.markers.push(marker);
    }
  });

  // Plot incident origin pin
  if (incidentCoords && incidentCoords[0] && incidentCoords[1]) {
    const incIconHtml = `<div style="background:#dc2626;color:#fff;border:2px solid #fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:13px;box-shadow:0 2px 5px rgba(0,0,0,0.4)">📍</div>`;
    const incIcon = L.divIcon({ html: incIconHtml, className: "", iconSize: [26, 26], iconAnchor: [13, 13] });
    const incMarker = L.marker(incidentCoords, { icon: incIcon }).addTo(map);
    incMarker.bindPopup(`<b>Incident Origin</b><br>${activeIncident ? activeIncident.location_label : "Emergency Scene"}`);
    mapLayers.markers.push(incMarker);
  }

  // Fetch detailed route geometry from backend
  if (activeIncident && targetHospId) {
    try {
      const resRoute = await fetch(`/api/incidents/${activeIncident.id}/route?hospital_id=${targetHospId}`);
      if (resRoute.ok) {
        const routeData = await resRoute.json();
        
        // Draw Alternate Route (dashed amber line)
        if (routeData.alternate_geometry && routeData.alternate_geometry.length > 1) {
          const altLine = L.polyline(routeData.alternate_geometry, {
            color: "#d97706",
            weight: 4,
            dashArray: "6, 8",
            opacity: 0.8
          }).addTo(map);
          altLine.bindPopup("Alternative road corridor detour");
          mapLayers.polylines.push(altLine);
        }

        // Setup Primary Route and Start Moving Ambulance Simulation
        if (routeData.primary_geometry && routeData.primary_geometry.length > 1) {
          map.fitBounds(L.polyline(routeData.primary_geometry).getBounds(), { padding: [35, 35] });

          // Start smooth moving ambulance traversal
          startRouteSimulation(
            map,
            routeData.primary_geometry,
            routeData.distance_km,
            routeData.duration_minutes
          );
        }
      }
    } catch (err) {
      console.warn("Detailed route fetch failed:", err);
    }
  } else if (incidentCoords && hospitalCoords) {
    map.fitBounds([incidentCoords, hospitalCoords], { padding: [40, 40] });
  }

  setTimeout(() => map.invalidateSize(), 150);
}

// ==========================================
// 4. MOVING AMBULANCE & REAL-TIME TELEMETRY
// ==========================================

function startRouteSimulation(map, geometry, totalDistanceKm, totalDurationMins) {
  stopSimulation();

  const densePoints = generateDensePath(geometry, 140);
  if (densePoints.length < 2) return;

  // Show HUD and Controls
  $("ambulance-telemetry-hud").style.display = "grid";
  $("sim-controls").style.display = "flex";

  // Polyline for traversed road path (muted gray)
  const traversed = L.polyline([], {
    color: "#64748b",
    weight: 4,
    dashArray: "4, 6"
  }).addTo(map);

  // Polyline for upcoming road path (bold institutional blue)
  const remaining = L.polyline(densePoints, {
    color: "#1d4ed8",
    weight: 5,
    opacity: 0.95
  }).addTo(map);

  // Animated Ambulance Marker with flashing emergency beacon
  const ambMarker = L.marker(densePoints[0], {
    icon: L.divIcon({
      className: "",
      html: `
        <div class="amb-marker-wrapper">
          <div class="amb-beacon-pulse"></div>
          <div class="amb-marker-body" id="amb-vehicle-icon">🚑</div>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 18]
    }),
    zIndexOffset: 1000
  }).addTo(map);

  mapLayers.markers.push(ambMarker);
  mapLayers.polylines.push(traversed, remaining);

  simState = {
    active: true,
    paused: false,
    speedMultiplier: 1,
    currentIndex: 0,
    routePoints: densePoints,
    totalDistanceKm: totalDistanceKm || 12.0,
    totalDurationMins: totalDurationMins || 18.0,
    ambulanceMarker: ambMarker,
    traversedPolyline: traversed,
    remainingPolyline: remaining,
    timerId: null
  };

  // Wire simulation control buttons
  $("btn-sim-play").textContent = "⏸ Pause";
  $("btn-sim-play").onclick = () => {
    simState.paused = !simState.paused;
    $("btn-sim-play").textContent = simState.paused ? "▶ Resume" : "⏸ Pause";
  };

  $("btn-sim-reset").onclick = () => {
    simState.currentIndex = 0;
    simState.paused = false;
    $("btn-sim-play").textContent = "⏸ Pause";
  };

  $("btn-speed-1x").onclick = () => setSimSpeed(1);
  $("btn-speed-2x").onclick = () => setSimSpeed(2);
  $("btn-speed-4x").onclick = () => setSimSpeed(4);

  // Animation loop (ticks every 120ms)
  simState.timerId = setInterval(() => {
    if (!simState.active || simState.paused) return;

    simState.currentIndex += simState.speedMultiplier;
    const maxIdx = simState.routePoints.length - 1;

    if (simState.currentIndex >= maxIdx) {
      simState.currentIndex = maxIdx;
      updateSimulationHUD(1.0);
      updateMilestone(3); // Handover at hospital entrance!
      stopSimulationTimer();
      logStatus(`Ambulance arrived at emergency bay entrance! Handover underway.`);
      return;
    }

    const curPos = simState.routePoints[simState.currentIndex];
    const nextPos = simState.routePoints[Math.min(maxIdx, simState.currentIndex + 1)];

    // Move ambulance marker
    simState.ambulanceMarker.setLatLng(curPos);

    // Compute heading direction angle and rotate vehicle icon
    if (nextPos) {
      const dy = nextPos[0] - curPos[0];
      const dx = (nextPos[1] - curPos[1]) * Math.cos(curPos[0] * Math.PI / 180);
      const angleDeg = Math.atan2(dx, dy) * 180 / Math.PI;
      const vehicleElem = $("amb-vehicle-icon");
      if (vehicleElem) {
        vehicleElem.style.transform = `rotate(${Math.round(angleDeg)}deg)`;
      }
    }

    // Update split polyline paths
    simState.traversedPolyline.setLatLngs(simState.routePoints.slice(0, simState.currentIndex + 1));
    simState.remainingPolyline.setLatLngs(simState.routePoints.slice(simState.currentIndex));

    // Progress fraction
    const progress = simState.currentIndex / maxIdx;
    updateSimulationHUD(progress);

  }, 120);
}

function setSimSpeed(speed) {
  simState.speedMultiplier = speed;
  ["1x", "2x", "4x"].forEach(s => {
    const btn = $(`btn-speed-${s}`);
    if (btn) {
      btn.style.fontWeight = s === `${speed}x` ? "700" : "500";
      btn.style.backgroundColor = s === `${speed}x` ? "var(--color-blue-subtle)" : "var(--bg-surface)";
    }
  });
}

function updateSimulationHUD(progress) {
  const fractionRemaining = Math.max(0, 1.0 - progress);

  // Live remaining distance in km
  const distRemainKm = (simState.totalDistanceKm * fractionRemaining).toFixed(1);

  // Live remaining time in seconds and MM:SS
  const totalSecondsRemain = Math.round(simState.totalDurationMins * 60 * fractionRemaining);
  const mins = Math.floor(totalSecondsRemain / 60);
  const secs = totalSecondsRemain % 60;
  const etaStr = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

  // Live simulated speed with realistic corridor variance
  const liveSpeed = Math.round(48 + Math.sin(simState.currentIndex) * 6);

  // Update telemetry DOM
  $("hud-eta").textContent = etaStr;
  $("hud-dist").textContent = `${distRemainKm} km`;
  $("hud-speed").textContent = `${liveSpeed} km/h · Green Wave Active`;

  // Milestone updates based on progress
  if (progress <= 0.05) {
    $("hud-status").textContent = "DISPATCHED / LEAVING SCENE";
    updateMilestone(0);
  } else if (progress < 0.75) {
    $("hud-status").textContent = "EN ROUTE (TRANSIT CORRIDOR)";
    updateMilestone(1);
  } else if (progress < 0.98) {
    $("hud-status").textContent = "NEAR HOSPITAL (<1.5 KM)";
    $("hud-status").style.color = "var(--color-amber)";
    updateMilestone(2);
  } else {
    $("hud-status").textContent = "ARRIVED AT EMERGENCY BAY";
    $("hud-status").style.color = "var(--color-green)";
    updateMilestone(3);
  }
}

function stopSimulationTimer() {
  if (simState.timerId) {
    clearInterval(simState.timerId);
    simState.timerId = null;
  }
}

function stopSimulation() {
  stopSimulationTimer();
  simState.active = false;
  const hud = $("ambulance-telemetry-hud");
  if (hud) hud.style.display = "none";
  const controls = $("sim-controls");
  if (controls) controls.style.display = "none";
}

// ==========================================
// 5. AMBULANCE WORKSPACE INTAKE & RANKING
// ==========================================

async function initAmbulanceWorkspace() {
  await initMapStatus();
  await loadHospitals();
  populateDropdowns();
  setupIntakeListeners();
  ensureLeafletMap("interactive-map");
}

async function loadHospitals() {
  try {
    const res = await fetch("/api/hospitals");
    if (!res.ok) return;
    allHospitals = await res.json();
  } catch (err) {
    console.error("Failed to load hospitals:", err);
  }
}

function populateDropdowns() {
  const locSelect = $("loc");
  locSelect.innerHTML = Object.keys(LOCATIONS).map(k => `<option value="${k}">${k}</option>`).join("");

  const bgSelect = $("bg");
  bgSelect.innerHTML = BLOOD_GROUPS.map(b => `<option value="${b}">${b}</option>`).join("");

  const chipsContainer = $("chips");
  chipsContainer.innerHTML = EMERGENCY_PRESETS.map(([lbl, inj, sev]) => `
    <button type="button" class="btn-secondary" style="font-size:11px;padding:4px 8px" onclick="applyPreset('${inj}', '${sev}')">
      ${lbl}
    </button>
  `).join("");
}

window.applyPreset = function(injury, priority) {
  $("inj").value = injury;
  $("sev").value = priority;
  if (priority === "Critical") {
    $("witness").value = "Critical";
    $("hr").value = 135;
    $("sp").value = 89;
  }
};

function setupIntakeListeners() {
  $("parse").addEventListener("click", () => {
    const text = $("vt").value.toLowerCase();
    if (!text) return;

    if (/head|brain|skull|concussion/.test(text)) $("inj").value = "neuro";
    else if (/chest|heart|cardiac|arrest/.test(text)) $("inj").value = "cardiac";
    else if (/burn|fire|scald/.test(text)) $("inj").value = "burns";
    else if (/fracture|leg|arm|bone/.test(text)) $("inj").value = "ortho";
    else if (/trauma|bleed|crash|collision/.test(text)) $("inj").value = "trauma";

    if (/unconscious|unresponsive|not breathing|critical/.test(text)) $("sev").value = "Critical";
    else if (/severe|heavy|high/.test(text)) $("sev").value = "High";

    const hrMatch = text.match(/(?:heart rate|hr|pulse)\D{0,6}(\d{2,3})/);
    if (hrMatch) $("hr").value = hrMatch[1];

    const spMatch = text.match(/(?:spo2|oxygen|sat)\D{0,6}(\d{2,3})/);
    if (spMatch) $("sp").value = spMatch[1];

    const bgMatch = text.match(/\b(ab|a|b|o)\s*(positive|negative|\+|-|pos|neg)/);
    if (bgMatch) {
      const group = bgMatch[1].toUpperCase() + (/pos|\+/.test(bgMatch[2]) ? "+" : "-");
      $("bg").value = group;
    }

    logStatus("Parsed narrative report into structured triage values. Verify prior to dispatch.");
    submitIncidentAndRank();
  });

  $("ex").addEventListener("click", () => {
    const locs = Object.keys(LOCATIONS);
    $("loc").value = locs[Math.floor(Math.random() * locs.length)];
    $("inj").value = ["trauma", "neuro", "cardiac", "ortho", "burns"][Math.floor(Math.random() * 5)];
    $("sev").value = ["Critical", "High", "Moderate"][Math.floor(Math.random() * 3)];
    $("bg").value = BLOOD_GROUPS[Math.floor(Math.random() * BLOOD_GROUPS.length)];
    $("witness").value = ["Unknown", "Critical", "Moderate", "Stable / normal"][Math.floor(Math.random() * 4)];
    $("hr").value = 85 + Math.floor(Math.random() * 60);
    $("sp").value = 88 + Math.floor(Math.random() * 12);
    $("pao2").value = "";
    document.querySelectorAll("#hazards input").forEach(cb => cb.checked = false);
    submitIncidentAndRank();
  });

  $("btn-rank").addEventListener("click", () => {
    submitIncidentAndRank();
  });

  $("btn-confirm-dest").addEventListener("click", () => {
    if (selectedHospital) {
      logStatus(`Confirmed destination: ${selectedHospital.name}. Ambulance dispatched en route.`);
      updateMilestone(1);
      updateIncidentStatus("en_route");
    }
  });

  $("btn-stage-blood").addEventListener("click", async () => {
    if (!activeIncident || !selectedHospital) return;
    try {
      const units = activeIncident.reported_priority === "Critical" ? 4 : 2;
      await fetch(`/api/incidents/${activeIncident.id}/blood-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hospital_id: selectedHospital.id,
          reported_group: activeIncident.reported_blood_group,
          requested_units: units,
          reason: "Dispatcher pre-stage coordination"
        })
      });
      logStatus(`Staged draft blood request: ${units} units of ${activeIncident.reported_blood_group} for ${selectedHospital.name}.`);
      alert(`Staged request recorded. Blood bank confirmation and cross-match verification remain required.`);
    } catch (e) {
      console.error(e);
    }
  });
}

function getSelectedHazards() {
  const cbs = document.querySelectorAll("#hazards input:checked");
  return Array.from(cbs).map(cb => cb.value);
}

async function submitIncidentAndRank() {
  const locKey = $("loc").value;
  const coords = LOCATIONS[locKey] || [13.0827, 80.2707];

  const payload = {
    location: {
      label: locKey,
      latitude: coords[0],
      longitude: coords[1]
    },
    injury_category: $("inj").value,
    incident_source: $("source").value,
    gender: $("gender").value,
    reported_priority: $("sev").value,
    witness_assessment: $("witness").value,
    vitals: {
      heart_rate_bpm: $("hr").value ? parseInt($("hr").value) : null,
      spo2_percent: $("sp").value ? parseFloat($("sp").value) : null,
      pao2_mmhg: $("pao2").value ? parseFloat($("pao2").value) : null
    },
    reported_blood_group: $("bg").value,
    blood_group_verified: false,
    route_hazards: getSelectedHazards()
  };

  try {
    const resCreate = await fetch("/api/incidents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!resCreate.ok) {
      const err = await resCreate.json();
      alert("Validation error creating incident: " + JSON.stringify(err.detail));
      return;
    }

    activeIncident = await resCreate.json();
    logStatus(`Incident registered: ${activeIncident.injury_category.toUpperCase()} at ${activeIncident.location_label}. Priority: ${activeIncident.reported_priority}.`);
    updateMilestone(0);

    await refreshRanking();

  } catch (err) {
    console.error("Submission failed:", err);
    alert("Connection error contacting backend ranking engine.");
  }
}

async function refreshRanking() {
  if (!activeIncident) return;

  try {
    const resRank = await fetch(`/api/incidents/${activeIncident.id}/recommendations`);
    if (!resRank.ok) return;

    activeRanking = await resRank.json();
    const recs = activeRanking.recommendations;
    if (!recs || recs.length === 0) return;

    renderPriorityDestination(recs[0]);
    renderAlternativesList(recs);
    renderComparison(recs);

    await selectHospitalDestination(recs[0].hospital_id, false);

  } catch (err) {
    console.error("Ranking refresh error:", err);
  }
}

function renderPriorityDestination(topRec) {
  const card = $("priority-dest-card");
  card.style.display = "block";
  card.className = topRec.warnings.length ? "priority-recommendation-card has-warnings" : "priority-recommendation-card";

  $("p1-name").textContent = topRec.hospital_name;
  $("p1-score").textContent = `Score: ${topRec.score} / 100`;
  $("p1-eta-dist").textContent = `Estimated Travel: ${topRec.eta.minutes} min · Distance: ${topRec.distance_km || "--"} km`;

  const b = topRec.components;
  $("p1-breakdown").innerHTML = `
    <div class="score-breakdown-item"><span class="label">Travel</span><span class="val">${b.travel} pts</span></div>
    <div class="score-breakdown-item"><span class="label">Specialist</span><span class="val">${b.specialist} pts</span></div>
    <div class="score-breakdown-item"><span class="label">ICU Beds</span><span class="val">${b.icu} pts</span></div>
    <div class="score-breakdown-item"><span class="label">ED Load</span><span class="val">${b.er_load} pts</span></div>
    <div class="score-breakdown-item"><span class="label">Blood Stock</span><span class="val">${b.blood_support} pts</span></div>
  `;

  $("p1-reasons").innerHTML = topRec.reasons.map(r => `<span class="tag-reason">✔ ${r}</span>`).join("");
  $("p1-warnings").innerHTML = topRec.warnings.map(w => `<span class="tag-warning">⚠ ${w}</span>`).join("");
}

function renderAlternativesList(recs) {
  const container = $("rank-list");
  container.innerHTML = `
    <table class="ranking-table">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Hospital Name</th>
          <th>Score</th>
          <th>ETA</th>
          <th>ICU</th>
          <th>Specialist</th>
          <th>Blood (${activeIncident.reported_blood_group})</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${recs.map(rec => {
          const isSelected = selectedHospital && selectedHospital.id === rec.hospital_id;
          const isEligible = rec.eligible;

          return `
            <tr class="${isSelected ? "selected-row" : ""}">
              <td><b>#${rec.rank}</b></td>
              <td>
                <b>${rec.hospital_name}</b>
                ${rec.warnings.length ? `<div style="font-size:10px;color:var(--color-amber)">⚠ ${rec.warnings[0]}</div>` : ""}
              </td>
              <td><b>${rec.score}</b></td>
              <td>${rec.eta.minutes} min</td>
              <td>${rec.icu_available} beds</td>
              <td>${rec.specialist_status}</td>
              <td>${rec.blood_units} units</td>
              <td>
                <button class="btn-secondary" style="font-size:11px;padding:2px 8px" onclick="overrideDestination('${rec.hospital_id}')" ${!isEligible ? "disabled" : ""}>
                  ${isSelected ? "Selected" : "Select"}
                </button>
              </td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

window.overrideDestination = function(hospId) {
  if (selectedHospital && selectedHospital.id === hospId) return;
  const reason = prompt("Enter dispatcher justification for selecting this destination:", "Operational override: specific facility bed allocation.");
  if (reason !== null) {
    selectHospitalDestination(hospId, true, reason);
  }
};

async function selectHospitalDestination(hospitalId, isOverride = false, overrideReason = "") {
  if (!activeIncident) return;

  const hospObj = allHospitals.find(h => h.id === hospitalId);
  if (!hospObj) return;

  selectedHospital = hospObj;

  try {
    await fetch(`/api/incidents/${activeIncident.id}/select-hospital`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hospital_id: hospitalId,
        override_reason: isOverride ? overrideReason : null
      })
    });
  } catch (err) {
    console.error("Select destination failed:", err);
  }

  const destCard = $("selected-dest-card");
  destCard.style.display = "block";
  $("selected-dest-content").innerHTML = `
    <div style="padding:10px;background:var(--bg-subtle);border:1px solid var(--border-color);border-radius:var(--radius-sm)">
      <div style="font-weight:700;font-size:14px;color:var(--color-navy)">Selected Destination: ${hospObj.name}</div>
      <div style="font-size:12px;color:var(--color-text-muted);margin:4px 0">
        Dispatch Priority: ${activeIncident.reported_priority} · Scene: ${activeIncident.location_label} · Injury: ${activeIncident.injury_category.toUpperCase()}
      </div>
      <div style="font-size:12px;margin-bottom:8px">
        Reported Blood Group: <b>${activeIncident.reported_blood_group}</b> · Vitals: Pulse ${activeIncident.vitals.heart_rate_bpm || "N/R"} bpm, SpO₂ ${activeIncident.vitals.spo2_percent || "N/R"}%
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn-primary" id="btn-prealert" style="font-size:12px;padding:4px 10px">🔔 Transmit Specialist Pre-Alert</button>
        <button class="btn-secondary" id="btn-update-enroute" style="font-size:12px;padding:4px 10px">Mark En Route</button>
      </div>
    </div>
  `;

  $("btn-prealert").onclick = async () => {
    try {
      await fetch(`/api/incidents/${activeIncident.id}/specialist-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hospital_id: hospitalId,
          specialty: activeIncident.injury_category,
          reason: "Dispatcher specialist pre-alert"
        })
      });
      $("btn-prealert").textContent = "✔ Pre-Alert Transmitted";
      logStatus(`Pre-alert notification transmitted to ${hospObj.name}.`);
    } catch (e) {
      console.error(e);
    }
  };

  $("btn-update-enroute").onclick = async () => {
    await updateIncidentStatus("en_route");
    updateMilestone(1);
  };

  if (activeRanking) {
    renderAlternativesList(activeRanking.recommendations);
  }

  const originCoords = (activeIncident.latitude && activeIncident.longitude)
    ? [activeIncident.latitude, activeIncident.longitude]
    : LOCATIONS[activeIncident.location_label] || [13.0827, 80.2707];

  const hospCoords = (hospObj.latitude && hospObj.longitude)
    ? [hospObj.latitude, hospObj.longitude]
    : [13.0827, 80.2707];

  await renderRealRoadMap(originCoords, hospCoords, hospObj.id);
  logStatus(`Destination confirmed: ${hospObj.name}. Real road transit underway.`);
}

function renderComparison(recs) {
  const top = recs[0];
  const originCoords = LOCATIONS[activeIncident.location_label] || [13.0827, 80.2707];

  const nearest = [...allHospitals].sort((a, b) => {
    const da = Math.hypot((a.latitude || 13.0) - originCoords[0], (a.longitude || 80.2) - originCoords[1]);
    const db = Math.hypot((b.latitude || 13.0) - originCoords[0], (b.longitude || 80.2) - originCoords[1]);
    return da - db;
  })[0];

  const nearRec = recs.find(r => r.hospital_id === nearest.id) || top;

  $("cmp-box").innerHTML = `
    <div style="padding:10px;background:var(--color-red-bg);border:1px solid var(--color-red-border);border-radius:var(--radius-sm)">
      <div style="font-size:11px;font-weight:600;color:var(--color-red)">GEOGRAPHICALLY NEAREST</div>
      <div style="font-weight:700;font-size:14px;color:var(--color-navy)">${nearest.name}</div>
      <div style="font-size:12px;margin:2px 0">ETA: <b>${nearRec.eta.minutes} min</b> · Score: ${nearRec.score}</div>
      <div style="font-size:11px;color:var(--color-text-muted)">ICU: ${nearRec.icu_available} beds · Blood: ${nearRec.blood_units} units · Specialist: ${nearRec.specialist_status}</div>
    </div>
    <div style="padding:10px;background:var(--color-green-bg);border:1px solid var(--color-green-border);border-radius:var(--radius-sm)">
      <div style="font-size:11px;font-weight:600;color:var(--color-green)">GRID HIGHEST-RANKED (#1)</div>
      <div style="font-weight:700;font-size:14px;color:var(--color-navy)">${top.hospital_name}</div>
      <div style="font-size:12px;margin:2px 0">ETA: <b>${top.eta.minutes} min</b> · Score: ${top.score}</div>
      <div style="font-size:11px;color:var(--color-text-muted)">ICU: ${top.icu_available} beds · Blood: ${top.blood_units} units · Specialist: ${top.specialist_status}</div>
    </div>
  `;
}

async function updateIncidentStatus(newStatus) {
  if (!activeIncident) return;
  try {
    const res = await fetch(`/api/incidents/${activeIncident.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      logStatus(`Incident transit status updated to: ${newStatus.toUpperCase()}`);
    }
  } catch (e) {
    console.error("Status update error:", e);
  }
}

function updateMilestone(idx) {
  for (let i = 0; i < 4; i++) {
    const step = $(`s${i}`);
    if (!step) continue;
    if (i < idx) {
      step.className = "milestone-step completed";
    } else if (i === idx) {
      step.className = "milestone-step active";
    } else {
      step.className = "milestone-step";
    }
  }
}

function logStatus(msg) {
  const container = $("status-log");
  if (!container) return;
  const time = new Date().toLocaleTimeString();
  const entry = document.createElement("div");
  entry.className = "activity-log-entry";
  entry.innerHTML = `<span style="color:var(--color-text-muted)">[${time}]</span> ${msg}`;
  container.prepend(entry);
}

// ==========================================
// 6. HOSPITAL COMMAND WORKSPACE & CLINICAL DOSSIER
// ==========================================

let currentHospitalData = null;

async function initHospitalWorkspace() {
  await loadHospitalData();
  await loadIncomingCases();
  await loadStagedBloodRequests();
  setupHospitalControls();

  $("btn-back-to-queue").onclick = () => {
    $("hospital-dossier-view").style.display = "none";
    $("incoming-cases-panel").style.display = "block";
    loadIncomingCases();
  };
}

async function loadHospitalData() {
  try {
    const res = await fetch("/api/hospital/me/resources");
    if (!res.ok) return;

    currentHospitalData = await res.json();
    renderHospitalReadiness(currentHospitalData);
    renderHospitalBloodGrid(currentHospitalData);
    renderHospitalSpecialists(currentHospitalData);
  } catch (err) {
    console.error("Failed to load hospital resources:", err);
  }
}

function renderHospitalReadiness(data) {
  $("hosp-banner-name").textContent = `${data.name} — Command Center`;
  $("hosp-banner-status").textContent = `Assigned Facility ID: ${data.id} · Admissions Status: ${data.accepting_status.toUpperCase()}`;

  $("hosp-icu-val").textContent = `${data.icu_available} / ${data.icu_capacity}`;
  $("hosp-er-val").textContent = `${Math.round(data.er_load * 100)}%`;
  $("er-slider").value = Math.round(data.er_load * 100);

  const acceptingElem = $("hosp-accepting-val");
  acceptingElem.textContent = data.accepting_status === "accepting" ? "Accepting" : "Diverting";
  acceptingElem.style.color = data.accepting_status === "accepting" ? "var(--color-green)" : "var(--color-red)";

  $("hosp-freshness-val").textContent = data.is_demo ? "Synthetic Demo" : "Live";
  const updated = new Date(data.updated_at).toLocaleTimeString();
  $("hosp-updated-val").textContent = `Updated: ${updated}`;
}

function renderHospitalBloodGrid(data) {
  const grid = $("hosp-blood-grid");
  const inventories = data.blood_inventory || [];

  grid.innerHTML = BLOOD_GROUPS.map(bg => {
    const item = inventories.find(b => b.blood_group === bg);
    const units = item ? item.units_available : 0;
    const statusClass = units >= 6 ? "adequate" : units >= 2 ? "low" : "critical";

    return `
      <div class="blood-cell ${statusClass}">
        <div class="group-name">${bg}</div>
        <div class="units-val">${units} units</div>
        <div style="margin-top:6px;display:flex;gap:4px;justify-content:center">
          <button class="btn-secondary" style="padding:1px 6px;font-size:10px" onclick="adjustBlood('${bg}', -1)">-</button>
          <button class="btn-secondary" style="padding:1px 6px;font-size:10px" onclick="adjustBlood('${bg}', 1)">+</button>
        </div>
      </div>
    `;
  }).join("");
}

window.adjustBlood = async function(bloodGroup, delta) {
  if (!currentHospitalData) return;
  const currentInv = currentHospitalData.blood_inventory || [];
  const item = currentInv.find(b => b.blood_group === bloodGroup);
  const currentUnits = item ? item.units_available : 0;
  const newUnits = Math.max(0, currentUnits + delta);

  try {
    const res = await fetch("/api/hospital/me/resources", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blood: { [bloodGroup]: newUnits } })
    });
    if (res.ok) {
      currentHospitalData = await res.json();
      renderHospitalBloodGrid(currentHospitalData);
    }
  } catch (err) {
    console.error("Failed to update blood:", err);
  }
};

function renderHospitalSpecialists(data) {
  const container = $("hosp-spec-list");
  const specialists = data.specialists || [];
  const allSpecs = ["trauma", "neuro", "cardiac", "ortho", "burns"];

  container.innerHTML = `
    <table class="specialist-table">
      <thead>
        <tr>
          <th>Specialty</th>
          <th>Physician on Call</th>
          <th>Readiness Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${allSpecs.map(spKey => {
          const s = specialists.find(x => x.specialty === spKey);
          const status = s ? s.status : "unavailable";
          const doctorName = s?.doctor_name || "Assigned On Duty";
          const statusBadge = status === "free"
            ? `<span class="status-badge live">Available Now</span>`
            : status === "surgery"
            ? `<span class="status-badge offline">In Surgery</span>`
            : `<span class="status-badge neutral">Unavailable</span>`;

          return `
            <tr>
              <td><b>${SPECIALTY_NAMES[spKey]}</b></td>
              <td>${doctorName}</td>
              <td>${statusBadge}</td>
              <td>
                <button class="btn-secondary" style="font-size:11px;padding:2px 8px" onclick="cycleSpecialistStatus('${spKey}', '${status}')">Cycle Status</button>
              </td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

window.cycleSpecialistStatus = async function(specKey, currentStatus) {
  const nextStatus = currentStatus === "free" ? "surgery" : currentStatus === "surgery" ? "none" : "free";
  try {
    const res = await fetch("/api/hospital/me/resources", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ specialists: { [specKey]: nextStatus } })
    });
    if (res.ok) {
      currentHospitalData = await res.json();
      renderHospitalSpecialists(currentHospitalData);
    }
  } catch (err) {
    console.error("Failed to update specialist:", err);
  }
};

function setupHospitalControls() {
  $("icu-dec").addEventListener("click", async () => {
    if (!currentHospitalData) return;
    const newIcu = Math.max(0, currentHospitalData.icu_available - 1);
    await updateHospitalResource({ icu_available: newIcu });
  });

  $("icu-inc").addEventListener("click", async () => {
    if (!currentHospitalData) return;
    const newIcu = Math.min(6, currentHospitalData.icu_available + 1);
    await updateHospitalResource({ icu_available: newIcu });
  });

  $("er-save").addEventListener("click", async () => {
    const val = parseFloat($("er-slider").value) / 100.0;
    await updateHospitalResource({ er_load: val });
  });

  $("toggle-accepting").addEventListener("click", async () => {
    if (!currentHospitalData) return;
    const next = currentHospitalData.accepting_status === "accepting" ? "not_accepting" : "accepting";
    await updateHospitalResource({ accepting_status: next });
  });
}

async function updateHospitalResource(patch) {
  try {
    const res = await fetch("/api/hospital/me/resources", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch)
    });
    if (res.ok) {
      currentHospitalData = await res.json();
      renderHospitalReadiness(currentHospitalData);
    }
  } catch (e) {
    console.error("Resource update error:", e);
  }
}

// Incoming Cases Queue
async function loadIncomingCases() {
  try {
    const res = await fetch("/api/hospital/incoming-cases");
    if (!res.ok) return;

    const cases = await res.json();
    renderIncomingCases(cases);
  } catch (err) {
    console.error("Failed to load incoming cases:", err);
  }
}

function renderIncomingCases(cases) {
  const container = $("incoming-cases-list");
  if (!cases || cases.length === 0) {
    container.innerHTML = `<div style="font-size:12px;color:var(--color-text-muted);padding:10px;text-align:center">No incoming ambulance alerts currently assigned to your hospital.</div>`;
    $("hospital-route-map-panel").style.display = "none";
    return;
  }

  container.innerHTML = cases.map(c => {
    const isCritical = c.reported_priority === "Critical";
    const selectedTime = new Date(c.selected_at).toLocaleTimeString();

    return `
      <div class="incoming-case-item ${isCritical ? "critical" : ""}">
        <div class="incoming-case-header">
          <div class="incoming-case-title">Case #${c.incident_id.slice(0, 8)}: ${c.injury_category.toUpperCase()}</div>
          <div style="display:flex;gap:6px">
            <span class="status-badge ${isCritical ? "offline" : "live"}">${c.reported_priority} Priority</span>
            <span class="status-badge neutral">Status: ${c.status.toUpperCase()}</span>
          </div>
        </div>

        <div style="font-size:12px;color:var(--color-text-muted)">
          📍 Location: <b>${c.location_label}</b> · Scenario: ${c.incident_source} · Dispatched at: ${selectedTime}
        </div>

        <div class="incoming-case-vitals">
          <span>Pulse: <b>${c.vitals.heart_rate_bpm || "N/R"} bpm</b></span>
          <span>SpO₂: <b>${c.vitals.spo2_percent || "N/R"}%</b></span>
          <span>Blood Group: <b>${c.reported_blood_group}</b> (unverified)</span>
          ${c.route_hazards.length ? `<span>Hazards: <b>${c.route_hazards.join(", ")}</b></span>` : ""}
        </div>

        <div class="incoming-case-actions">
          <button class="btn-success" onclick="openPatientDossier('${c.incident_id}')">✔ Acknowledge & Open Clinical Dossier</button>
          <button class="btn-danger" onclick="declineCase('${c.incident_id}')">✖ Decline Case</button>
          <button class="btn-secondary" onclick="viewCaseRoute('${c.incident_id}', '${c.location_label}')">🗺 View Route</button>
        </div>
      </div>
    `;
  }).join("");
}

// Open Active Clinical Dossier when hospital acknowledges or inspects case
window.openPatientDossier = async function(incidentId) {
  try {
    // 1. Acknowledge case on backend
    await fetch(`/api/hospital/incidents/${incidentId}/acknowledge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: "Trauma team and emergency bay prepared." })
    });

    // 2. Fetch full incident details
    const resInc = await fetch(`/api/incidents/${incidentId}`);
    if (!resInc.ok) return;
    const inc = await resInc.json();
    activeDossierCase = inc;

    // 3. Switch view
    $("incoming-cases-panel").style.display = "none";
    $("hospital-route-map-panel").style.display = "none";
    const dossierPanel = $("hospital-dossier-view");
    dossierPanel.style.display = "block";

    $("dossier-case-id").textContent = `Case #${inc.id.slice(0, 8)} · Patient Emergency Bay Clinical Dossier`;
    $("dossier-status-badge").textContent = `STATUS: ${inc.status.toUpperCase()}`;

    // Find assigned specialist doctor on duty
    const specKey = inc.injury_category.toLowerCase();
    const specObj = currentHospitalData?.specialists?.find(s => s.specialty === specKey);
    const assignedDoctor = specObj?.doctor_name || "Dr. Mehta";

    // Check blood inventory
    const bloodInv = currentHospitalData?.blood_inventory?.find(b => b.blood_group === inc.reported_blood_group);
    const availableUnits = bloodInv ? bloodInv.units_available : 0;

    // Render comprehensive clinical report & doctor dispatch console
    $("dossier-content").innerHTML = `
      <div class="dossier-container">
        
        <!-- Left: Clinical Report & Patient Telemetry -->
        <div>
          <div style="padding:10px;background:var(--bg-subtle);border:1px solid var(--border-color);border-radius:var(--radius-sm);margin-bottom:12px">
            <div style="font-size:11px;font-weight:700;color:var(--color-navy);text-transform:uppercase">Patient Triage Profile</div>
            <div style="font-size:16px;font-weight:700;color:var(--color-navy);margin:3px 0">${inc.injury_category.toUpperCase()} EMERGENCY</div>
            <div style="font-size:12px;color:var(--color-text-muted)">
              Dispatch Priority: <b>${inc.reported_priority}</b> · Incident Scene: <b>${inc.location_label}</b> · Scenario: ${inc.incident_source}
            </div>
            <div style="font-size:12px;color:var(--color-text-muted);margin-top:2px">
              Patient Gender (context only): <b>${inc.gender}</b> · Witness Assessment: <b>${inc.witness_assessment}</b>
            </div>
          </div>

          <!-- Vitals Strip -->
          <div class="dossier-vitals-strip">
            <div class="dossier-vital-card">
              <div class="v-label">Heart Rate</div>
              <div class="v-val">${inc.vitals.heart_rate_bpm || "--"} <span style="font-size:12px">bpm</span></div>
              <div style="font-size:10px;color:var(--color-green)">Reported</div>
            </div>
            <div class="dossier-vital-card">
              <div class="v-label">SpO₂ Oxygen</div>
              <div class="v-val" style="color:${(inc.vitals.spo2_percent && inc.vitals.spo2_percent <= 90) ? 'var(--color-red)' : 'var(--color-navy)'}">
                ${inc.vitals.spo2_percent || "--"} <span style="font-size:12px">%</span>
              </div>
              <div style="font-size:10px;color:${(inc.vitals.spo2_percent && inc.vitals.spo2_percent <= 90) ? 'var(--color-red)' : 'var(--color-green)'}">
                ${(inc.vitals.spo2_percent && inc.vitals.spo2_percent <= 90) ? 'Hypoxia Review' : 'Reported'}
              </div>
            </div>
            <div class="dossier-vital-card">
              <div class="v-label">PaO₂ Blood Gas</div>
              <div class="v-val">${inc.vitals.pao2_mmhg || "N/R"} <span style="font-size:12px">mmHg</span></div>
              <div style="font-size:10px;color:var(--color-text-muted)">Clinically Observed</div>
            </div>
          </div>

          <!-- Blood Bank Verification Block -->
          <div style="padding:10px;background:var(--color-amber-bg);border:1px solid var(--color-amber-border);border-radius:var(--radius-sm);margin-bottom:12px">
            <div style="font-weight:700;font-size:12px;color:var(--color-amber)">BLOOD BANK RESERVE & CROSS-MATCH</div>
            <div style="font-size:13px;margin:2px 0">
              Reported Blood Group: <b>${inc.reported_blood_group}</b> (unverified) · Hospital Inventory: <b>${availableUnits} units available</b>
            </div>
            <div style="font-size:11px;color:var(--color-amber)">
              Notice: Sample cross-match & verification required prior to transfusion.
            </div>
          </div>

          <!-- Attending Doctor Dispatch Console -->
          <div class="doctor-dispatch-box">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
              <div>
                <div style="font-size:11px;font-weight:700;color:var(--color-navy);text-transform:uppercase">Assigned Attending Physician</div>
                <div style="font-size:15px;font-weight:700;color:var(--color-navy)">${assignedDoctor} (${SPECIALTY_NAMES[specKey] || "On Call Specialist"})</div>
              </div>
              <span id="doc-dispatch-badge" class="status-badge live">Physician Assigned</span>
            </div>

            <div style="font-size:12px;margin:6px 0;color:var(--color-text)">
              Emergency Bay Destination: <b>Trauma Bay 1 (Ground Floor Resuscitation)</b>
            </div>

            <div style="display:flex;gap:8px;margin-top:10px">
              <button type="button" class="btn-primary" id="btn-page-doctor" style="padding:8px 14px">
                🔔 Page & Dispatch ${assignedDoctor} to Bay 1
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Real-time Transit Road Map & Bay Preparation -->
        <div>
          <!-- Mini Live Transit Road Map -->
          <div class="map-panel" style="margin-bottom:12px">
            <div class="map-control-bar">
              <span>Transit Road Corridor Navigation</span>
              <span class="status-badge live">Live Telemetry</span>
            </div>
            <div id="dossier-map" style="width:100%;height:240px"></div>
          </div>

          <!-- Bay Readiness Checklist -->
          <div style="padding:12px;background:var(--bg-surface);border:1px solid var(--border-color);border-radius:var(--radius-sm)">
            <div style="font-weight:700;font-size:12px;color:var(--color-navy);margin-bottom:6px">
              EMERGENCY BAY READINESS CHECKLIST
            </div>
            <div class="bay-checklist-box">
              <label class="bay-check-item">
                <input type="checkbox" id="chk-bay" checked>
                <span>Trauma Bay 1 Pre-cleared & Sanitized</span>
              </label>
              <label class="bay-check-item">
                <input type="checkbox" id="chk-airway" checked>
                <span>Rapid Sequence Intubation (RSI) / Airway cart at bedside</span>
              </label>
              <label class="bay-check-item">
                <input type="checkbox" id="chk-blood" checked>
                <span>Rapid infuser primed & 2 units ${inc.reported_blood_group} cross-matched</span>
              </label>
              <label class="bay-check-item">
                <input type="checkbox" id="chk-ct">
                <span>Emergency CT Scanner & Radiologist on standby</span>
              </label>
            </div>

            <div class="form-group" style="margin-top:10px">
              <label style="font-size:11px;font-weight:600">Physician Clinical Instructions & Reception Notes</label>
              <textarea id="dossier-notes" rows="2" style="font-size:12px" placeholder="Enter instructions for incoming paramedic team..."></textarea>
            </div>

            <div style="display:flex;gap:8px;margin-top:10px">
              <button type="button" class="btn-success" id="btn-finalize-handover" style="padding:9px 16px;width:100%">
                ✔ Complete Bay Handover & Admit Patient
              </button>
            </div>
          </div>
        </div>

      </div>
    `;

    // Initialize the dossier road map
    renderDossierMap(inc);

    // Doctor dispatch button listener
    $("btn-page-doctor").onclick = async () => {
      try {
        const notes = $("dossier-notes").value;
        const resDoc = await fetch(`/api/hospital/incidents/${inc.id}/dispatch-doctor`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            specialist_doctor: assignedDoctor,
            bay_number: "Trauma Bay 1",
            prep_notes: notes || "Trauma bay cleared and staff assembled."
          })
        });

        if (resDoc.ok) {
          $("doc-dispatch-badge").className = "status-badge live";
          $("doc-dispatch-badge").textContent = `${assignedDoctor} Paged & At Bay`;
          $("btn-page-doctor").textContent = `✔ ${assignedDoctor} Dispatched to Bay 1`;
          $("btn-page-doctor").disabled = true;
          logStatus(`Attending physician ${assignedDoctor} paged to Trauma Bay 1.`);
          alert(`Paging alert sent to ${assignedDoctor}. Trauma bay reception confirmed.`);
        }
      } catch (e) {
        console.error(e);
      }
    };

    // Finalize Bay Handover listener
    $("btn-finalize-handover").onclick = async () => {
      try {
        const handoverNotes = $("dossier-notes").value || "Patient handover complete. Admitted to Trauma Bay 1.";
        const resH = await fetch(`/api/hospital/incidents/${inc.id}/complete-handover`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ handover_notes: handoverNotes })
        });

        if (resH.ok) {
          alert(`Handover complete! Patient admitted to Trauma Bay 1. Case archived.`);
          $("hospital-dossier-view").style.display = "none";
          $("incoming-cases-panel").style.display = "block";
          loadIncomingCases();
        }
      } catch (e) {
        console.error(e);
      }
    };

  } catch (err) {
    console.error("Open dossier error:", err);
  }
};

function renderDossierMap(inc) {
  const container = $("dossier-map");
  if (!container || typeof L === "undefined") return;

  if (leafletDossierMap) {
    leafletDossierMap.remove();
    leafletDossierMap = null;
  }

  leafletDossierMap = L.map("dossier-map", {
    center: [13.06, 80.24],
    zoom: 13,
    zoomControl: false,
    attributionControl: false
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(leafletDossierMap);

  const originCoords = LOCATIONS[inc.location_label] || [13.0827, 80.2707];
  const hospCoords = [currentHospitalData.latitude || 13.0827, currentHospitalData.longitude || 80.2707];

  fetch(`/api/incidents/${inc.id}/route?hospital_id=${currentHospitalData.id}`)
    .then(r => r.json())
    .then(routeData => {
      if (routeData.primary_geometry && routeData.primary_geometry.length > 1) {
        const line = L.polyline(routeData.primary_geometry, { color: "#1d4ed8", weight: 5 }).addTo(leafletDossierMap);
        leafletDossierMap.fitBounds(line.getBounds(), { padding: [25, 25] });

        // Add ambulance icon near arrival
        const midPoint = routeData.primary_geometry[Math.floor(routeData.primary_geometry.length * 0.75)];
        L.marker(midPoint, {
          icon: L.divIcon({
            html: `<div style="background:#fff;border:2px solid #1d4ed8;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.3)">🚑</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          })
        }).addTo(leafletDossierMap).bindPopup("Approaching Ambulance");
      }
    })
    .catch(e => console.warn(e));

  L.marker(originCoords).addTo(leafletDossierMap).bindPopup(`Incident: ${inc.location_label}`);
  L.marker(hospCoords).addTo(leafletDossierMap).bindPopup(`Your Facility: ${currentHospitalData.name}`);

  setTimeout(() => leafletDossierMap.invalidateSize(), 150);
}

window.viewCaseRoute = async function(incidentId, locationLabel) {
  openPatientDossier(incidentId);
};

window.acknowledgeCase = async function(incidentId) {
  openPatientDossier(incidentId);
};

window.declineCase = async function(incidentId) {
  const reason = prompt("Enter justification for diversion/decline:", "ICU beds and trauma bays currently at capacity.");
  if (!reason) return;

  try {
    const res = await fetch(`/api/hospital/incidents/${incidentId}/decline`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    if (res.ok) {
      alert("Case declined and returned to dispatch queue.");
      loadIncomingCases();
    }
  } catch (err) {
    console.error("Decline error:", err);
  }
};

async function loadStagedBloodRequests() {
  const container = $("staged-blood-list");
  if (container) {
    container.innerHTML = `<div style="font-size:12px;color:var(--color-text-muted);padding:8px">No pending blood bank coordination requests for this facility.</div>`;
  }
}

// Clock Display (Countdown from 60:00)
let remainingSeconds = 3600;
function startClock() {
  if (clockInterval) clearInterval(clockInterval);
  clockInterval = setInterval(() => {
    remainingSeconds = Math.max(0, remainingSeconds - 1);
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    const timeStr = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    const clockElem = $("tl");
    if (clockElem) clockElem.textContent = timeStr;
  }, 1000);
}

startClock();
checkAuth();

// ATM Cash Prediction System - Bangalore Edition Client Script

let map = null;
let centerMarker = null;
let selectedMarker = null;
let mapMarkersLayer = null;
let allMapPoints = [];
const BLR_CENTER = [12.9716, 77.5946];

document.addEventListener("DOMContentLoaded", async () => {
    initLeafletMap();
    await loadFilterMetadata();
    await onFilterChange();
    await loadMapPoints();

    // Default load ATM0009 (Koramangala, Bangalore)
    quickSelect("ATM0009");
});

// Initialize Leaflet OpenStreetMap
function initLeafletMap() {
    map = L.map('map').setView(BLR_CENTER, 11);

    // OpenStreetMap standard tile layer (free, no API key required)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Layer group for ATM markers
    mapMarkersLayer = L.layerGroup().addTo(map);

    // Bangalore City Center reference marker
    const centerIcon = L.divIcon({
        className: 'center-div-icon',
        html: '<div style="background-color: #dc2626; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">★</div>',
        iconSize: [26, 26],
        iconAnchor: [13, 13]
    });

    centerMarker = L.marker(BLR_CENTER, { icon: centerIcon }).addTo(map);
    centerMarker.bindPopup("<b>Bangalore City Center</b><br>Majestic / Vidhana Soudha<br>Lat: 12.9716, Lon: 77.5946");
}

// Load Bangalore areas and banks for dropdown filters
async function loadFilterMetadata() {
    try {
        const resp = await fetch("/api/bangalore-meta");
        const data = await resp.json();

        // Populate Bangalore Areas
        const areaSelect = document.getElementById("areaSelect");
        areaSelect.innerHTML = '<option value="All">All Bangalore Areas</option>';
        data.bangalore_areas.forEach(area => {
            const opt = document.createElement("option");
            opt.value = area;
            opt.textContent = area;
            areaSelect.appendChild(opt);
        });

        // Add Mysuru as nearby Karnataka option
        const optMysuru = document.createElement("option");
        optMysuru.value = "Mysuru_All";
        optMysuru.textContent = "Nearby: Mysuru (Karnataka)";
        areaSelect.appendChild(optMysuru);

        // Populate Banks
        const bankSelect = document.getElementById("bankSelect");
        bankSelect.innerHTML = '<option value="All">All Banks</option>';
        data.banks.forEach(bank => {
            const opt = document.createElement("option");
            opt.value = bank;
            opt.textContent = bank;
            bankSelect.appendChild(opt);
        });

    } catch (err) {
        console.error("Failed to load filter metadata:", err);
    }
}

// Filter ATMs based on Area and Bank selection
async function onFilterChange() {
    const areaVal = document.getElementById("areaSelect").value;
    const bankVal = document.getElementById("bankSelect").value;

    let url = `/api/atms?bank=${encodeURIComponent(bankVal)}`;

    if (areaVal === "Mysuru_All") {
        url += `&city=Mysuru`;
    } else if (areaVal !== "All") {
        url += `&city=Bengaluru&area=${encodeURIComponent(areaVal)}`;
    } else {
        url += `&city=Bengaluru`;
    }

    try {
        const resp = await fetch(url);
        const data = await resp.json();

        const atmSelect = document.getElementById("atmSelect");
        atmSelect.innerHTML = "";

        if (data.atms.length === 0) {
            atmSelect.innerHTML = '<option value="">No ATMs match these filters</option>';
            document.getElementById("filterCountBadge").textContent = "0 ATMs found";
            return;
        }

        document.getElementById("filterCountBadge").textContent = `${data.atms.length} ATMs Available`;

        data.atms.forEach(atm => {
            const opt = document.createElement("option");
            opt.value = atm.atm_id;
            opt.textContent = `${atm.atm_id} - ${atm.bank} (${atm.area}) [${atm.dist_to_center_km} km]`;
            atmSelect.appendChild(opt);
        });

    } catch (err) {
        console.error("Failed to filter ATMs:", err);
    }
}

// Load all Bangalore ATM markers on map
async function loadMapPoints() {
    try {
        const resp = await fetch("/api/bangalore-map-points");
        const data = await resp.json();
        allMapPoints = data.points;

        mapMarkersLayer.clearLayers();

        data.points.forEach(pt => {
            const circle = L.circleMarker([pt.latitude, pt.longitude], {
                radius: 6,
                fillColor: pt.cash_pct_remaining < 20 ? "#dc2626" : "#2563eb",
                color: "#ffffff",
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.8
            });

            circle.bindPopup(`
                <strong>${pt.atm_id} (${pt.bank})</strong><br>
                Area: ${pt.area}<br>
                Remaining Cash: ₹${pt.closing_balance.toLocaleString('en-IN')} (${pt.cash_pct_remaining.toFixed(1)}%)<br>
                Distance: ${pt.dist_km} km to City Center<br>
                <button style="margin-top:5px; padding:3px 8px; cursor:pointer;" onclick="quickSelect('${pt.atm_id}')">Select this ATM</button>
            `);

            circle.addTo(mapMarkersLayer);
        });
    } catch (err) {
        console.error("Failed to load map points:", err);
    }
}

// Quick Select button helper
async function quickSelect(atmId) {
    const areaSelect = document.getElementById("areaSelect");
    const bankSelect = document.getElementById("bankSelect");

    // Reset filters to All to ensure the ATM is in the list
    areaSelect.value = "All";
    bankSelect.value = "All";
    await onFilterChange();

    const atmSelect = document.getElementById("atmSelect");
    atmSelect.value = atmId;

    await checkSelectedATM();
}

// Check ATM and Display Prediction & Distance
async function checkSelectedATM() {
    const atmSelect = document.getElementById("atmSelect");
    const atmId = atmSelect.value;

    if (!atmId) {
        alert("Please select an ATM first.");
        return;
    }

    const checkBtn = document.getElementById("checkAtmBtn");
    checkBtn.disabled = true;
    checkBtn.textContent = "⏳ Checking ATM...";

    try {
        // Fetch details and prediction in parallel
        const [detailsResp, predResp] = await Promise.all([
            fetch(`/api/atm/${atmId}`),
            fetch(`/api/predict/${atmId}`)
        ]);

        const details = await detailsResp.json();
        const pred = await predResp.json();

        checkBtn.disabled = false;
        checkBtn.textContent = "🔍 Check ATM & Predict";

        if (details.error || pred.error) {
            alert("Error: " + (details.error || pred.error));
            return;
        }

        renderATMDetails(details);
        renderPrediction(pred);
        highlightATMOnMap(details, pred);

    } catch (err) {
        console.error("Failed to check ATM:", err);
        checkBtn.disabled = false;
        checkBtn.textContent = "🔍 Check ATM & Predict";
        alert("Failed to connect to Flask server.");
    }
}

// Render ATM Information & Distance Panel
function renderATMDetails(d) {
    const formatINR = (val) => "₹" + Number(val).toLocaleString("en-IN");

    document.getElementById("atmCityBadge").textContent = `${d.city} • ${d.area}`;

    let barColor = "safe";
    if (d.cash_pct_remaining < 15) {
        barColor = "danger";
    } else if (d.cash_pct_remaining < 35) {
        barColor = "warning";
    }

    const html = `
        <div class="details-grid">
            <div class="detail-item">
                <div class="detail-label">ATM ID & Bank</div>
                <div class="detail-val">${d.atm_id} • ${d.bank}</div>
                <div class="detail-sub">${d.location_type}</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Area & City</div>
                <div class="detail-val">${d.area}</div>
                <div class="detail-sub">${d.city}, Karnataka</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">GPS Coordinates</div>
                <div class="detail-val">${d.latitude.toFixed(4)}° N, ${d.longitude.toFixed(4)}° E</div>
                <div class="detail-sub">Actual Dataset Values</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Distance to Bangalore Center</div>
                <div class="detail-val"><span class="distance-highlight">${d.dist_to_center_km} km</span></div>
                <div class="detail-sub">Haversine Great-Circle Formula</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Current Available Cash</div>
                <div class="detail-val" style="color: #0f3d6e;">${formatINR(d.closing_balance)}</div>
                <div class="detail-sub">Closing balance end-of-day</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Total Cash Capacity</div>
                <div class="detail-val">${formatINR(d.cash_capacity)}</div>
                <div class="detail-sub">Full Cassette Capacity</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Today's Total Withdrawn</div>
                <div class="detail-val">${formatINR(d.total_withdrawn)}</div>
                <div class="detail-sub">${d.num_transactions} transactions (Avg ${formatINR(d.avg_txn_amount)})</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">Expected Daily Demand</div>
                <div class="detail-val">${formatINR(d.base_daily_demand)}</div>
                <div class="detail-sub">Footfall Score: ${(d.footfall_index * 100).toFixed(0)}%</div>
            </div>
        </div>

        <div class="cash-status-box">
            <div class="cash-bar-label">
                <span>Cash Percentage Remaining:</span>
                <span style="font-weight: 700;">${d.cash_pct_remaining.toFixed(1)}%</span>
            </div>
            <div class="bar-bg">
                <div class="bar-fill ${barColor}" style="width: ${Math.min(100, Math.max(0, d.cash_pct_remaining))}%;"></div>
            </div>
        </div>
    `;

    document.getElementById("atmDetailsContainer").innerHTML = html;
}

// Render Prediction Result Panel
function renderPrediction(p) {
    const isCashOut = p.pred_class === 1;
    const bannerClass = isCashOut ? "verdict-banner danger" : "verdict-banner safe";
    const icon = isCashOut ? "⚠️" : "✅";
    const barColor = isCashOut ? "#dc2626" : "#16a34a";

    let reasonsHtml = "";
    if (p.reasons && p.reasons.length > 0) {
        reasonsHtml = p.reasons.map(r => `<li>${r}</li>`).join("");
    } else {
        reasonsHtml = `<li>Model evaluation verified that cash reserves match predicted tomorrow's demand.</li>`;
    }

    const html = `
        <div class="${bannerClass}">
            <div class="verdict-icon">${icon}</div>
            <div>
                <h3>${p.prediction}</h3>
                <p>Status: <strong>${p.risk_level}</strong> • Target: <code>cash_out_next_day = ${p.pred_class}</code></p>
            </div>
        </div>

        <div class="prob-card">
            <div class="prob-label-row">
                <span><strong>Cash-Out Risk Probability:</strong></span>
                <span class="prob-value" style="color: ${barColor};">${p.cash_out_probability}%</span>
            </div>
            <div class="prob-bar-bg">
                <div class="prob-bar-fill" style="width: ${Math.min(100, Math.max(4, p.cash_out_probability))}%; background-color: ${barColor};"></div>
            </div>
        </div>

        <div class="reasons-box ${isCashOut ? 'danger' : ''}">
            <h4>Key Contributing Factors:</h4>
            <ul>${reasonsHtml}</ul>
        </div>
    `;

    document.getElementById("predictionContainer").innerHTML = html;
}

// Highlight Selected ATM on Leaflet Map
function highlightATMOnMap(d, p) {
    if (!map) return;

    if (selectedMarker) {
        map.removeLayer(selectedMarker);
    }

    const isRisk = p.pred_class === 1;
    const pinColor = isRisk ? "#dc2626" : "#16a34a";

    const customPin = L.divIcon({
        className: 'selected-div-icon',
        html: `<div style="background-color: ${pinColor}; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; border: 3px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.4);">📍</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    selectedMarker = L.marker([d.latitude, d.longitude], { icon: customPin }).addTo(map);

    selectedMarker.bindPopup(`
        <div style="min-width: 180px;">
            <strong style="font-size: 14px;">${d.atm_id} - ${d.bank}</strong><br>
            <strong>Area:</strong> ${d.area}, ${d.city}<br>
            <strong>Distance:</strong> ${d.dist_to_center_km} km from City Center<br>
            <strong>Cash Left:</strong> ₹${d.closing_balance.toLocaleString('en-IN')} (${d.cash_pct_remaining.toFixed(1)}%)<br>
            <strong style="color: ${pinColor}; margin-top: 4px; display: inline-block;">${p.prediction}</strong>
        </div>
    `).openPopup();

    map.setView([d.latitude, d.longitude], 13);
}

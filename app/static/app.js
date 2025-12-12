// Always talk to the FastAPI backend on port 8000
// const API_BASE = "http://127.0.0.1:8000";
const API_BASE = "";
console.log("Loaded app.js at", new Date().toISOString());

const statusEl = document.getElementById("status");
const addrLabel = document.getElementById("addrLabel");
const agentTextEl = document.getElementById("agentText");

// Initialize the map
const map = L.map("map", { zoomControl: true }).setView([40.7128, -74.0060], 12);

// Add OpenStreetMap tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

// Custom red icon for "You are here"
const redIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// User marker
let userMarker = null;
function setUserMarker(lat, lon, label = "You are here") {
  if (userMarker) userMarker.remove();
  userMarker = L.marker([lat, lon], { icon: redIcon }).addTo(map).bindPopup(label);
  map.setView([lat, lon], 14);
}

// Court markers
let courtMarkers = [];
function clearCourts() {
  courtMarkers.forEach((m) => m.remove());
  courtMarkers = [];
}
function addCourts(list) {
  clearCourts();
  const bounds = [];

  list.forEach((c) => {
    const name = c.Name ?? "";
    const borough = c.Borough ?? "";
    const rawDist = c.Distance_Km;
    const dist =
      typeof rawDist === "number" ? `${rawDist.toFixed(2)} km` : rawDist ?? "";
    const lat = c.Lat;
    const lon = c.Lon;

    const html = `
      <div style="font-size:12px;line-height:1.3">
        <b>${name}</b><br>
        ${borough ? `${borough}<br>` : ""}
        ${dist ? `${dist}<br>` : ""}
        ${c.Num_Of_Courts ? `Number of Courts: ${c.Num_Of_Courts}<br>` : ""}
      </div>`;

    const m = L.marker([lat, lon]).addTo(map).bindPopup(html);
    courtMarkers.push(m);
    bounds.push([lat, lon]);
  });

  if (bounds.length) {
    if (userMarker) bounds.push(userMarker.getLatLng());
    map.fitBounds(bounds, { padding: [30, 30] });
  }
}

// Fetch nearest courts
async function fetchNearest(lat, lon) {
  const url = `${API_BASE}/nearest?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(
    lon
  )}&limit=10`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      statusEl.textContent = `Nearest failed: HTTP ${res.status}`;
      throw new Error(`Nearest lookup failed: ${res.status}`);
    }
    const data = await res.json();
    statusEl.textContent = "";
    addCourts(data.results || []);
  } catch (e) {
    statusEl.textContent = "Failed to load nearby courts. See console for details.";
    console.error(e);
  }
}

// Reverse geocode current coords -> label
async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(`${API_BASE}/geocodeReverse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lon }),
      cache: "no-store",
    });
    if (!res.ok) {
      addrLabel.textContent = "";
      return;
    }
    const data = await res.json();
    addrLabel.textContent = data.display_name || "";
  } catch {
    addrLabel.textContent = "";
  }
}

// Geolocate and drop a marker + load nearest + label
document.getElementById("btnLocate").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocation not supported by your browser.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords;
      setUserMarker(latitude, longitude);
      reverseGeocode(latitude, longitude);
      fetchNearest(latitude, longitude);
    },
    (err) => {
      console.error(err);
      alert("Could not get your location.");
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

// Address search (click + Enter)
document.getElementById("btnSearch").addEventListener("click", onSearch);
document.getElementById("address").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    onSearch();
  }
});

async function onSearch() {
  const address = document.getElementById("address").value.trim();
  if (!address) return;

  try {
    const res = await fetch(`${API_BASE}/geocodeForward`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
      cache: "no-store",
    });
    if (!res.ok) {
      alert("Address not found");
      return;
    }
    const data = await res.json();
    setUserMarker(data.lat, data.lon, data.display_name || "Selected location");
    if (userMarker) userMarker.openPopup();
    addrLabel.textContent = data.display_name || "";
    fetchNearest(data.lat, data.lon);
  } catch (e) {
    console.error(e);
    alert("Geocoding request failed.");
  }
}

// -------------------- Agent --------------------

let previous_response_id = null;

async function askAgent() {
  const query = document.getElementById("userInput").value;

  const res = await fetch("/agent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: query,
      // previous_response_id: previous_response_id
    }),
  });

  const data = await res.json();
  console.log("Agent response JSON:", data);

  // show a one-liner "latest agent answer"
  const answerText = data.text ?? data.response ?? "";
  agentTextEl.innerText = answerText;

  // previous_response_id = data.response_id;

  const chatDiv = document.getElementById("chat");
  chatDiv.innerHTML += `<p><strong>You:</strong> ${query}</p>`;
  chatDiv.innerHTML += `<p><strong>Agent:</strong> ${answerText}</p>`;
}

// Hook up the button (instead of inline onclick)
document.getElementById("btnAskAgent").addEventListener("click", askAgent);

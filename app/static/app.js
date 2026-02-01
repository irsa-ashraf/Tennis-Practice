const API_BASE = "";

const statusEl = document.getElementById("status");
const addrLabel = document.getElementById("addrLabel");
const sportSelect = document.getElementById("sportSelect");

// Chat UI
const chatLog = document.getElementById("chatLog");
const inputEl = document.getElementById("userInput");
const sendBtn = document.getElementById("btnAskAgent");
const agentStatus = document.getElementById("agentStatus");
const chatToggle = document.getElementById("chatToggle");

function setAgentStatus(text) {
  if (agentStatus) agentStatus.textContent = text;
}

function setText(el, text, label) {
  if (!el) {
    console.warn(`Missing element: ${label}`);
    return;
  }
  el.textContent = text;
}

function appendMessage(role, text) {
  const row = document.createElement("div");
  row.className = `msgRow ${role === "me" ? "me" : "bot"}`;

  const bubble = document.createElement("div");
  bubble.className = "msg";
  bubble.textContent = text;

  row.appendChild(bubble);
  chatLog.appendChild(row);

  // scroll to bottom
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  inputEl.disabled = isLoading;
  setAgentStatus(isLoading ? "Thinking…" : "Ready");
}

if (chatToggle) {
  chatToggle.addEventListener("click", () => {
    const panel = document.querySelector(".chatPanel");
    if (!panel) return;
    const isOpen = panel.classList.toggle("open");
    chatToggle.classList.toggle("open", isOpen);
    chatToggle.textContent = isOpen ? "Close chat" : "Chat";
  });
}

// Initialize map
const map = L.map("map", { zoomControl: true }).setView([40.7128, -74.0060], 12);

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

const sportIcons = {
  handball: new L.Icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  }),
  tennis: new L.Icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  }),
};

// User marker
let userMarker = null;
let lastCoords = null;
function setUserMarker(lat, lon, label = "You are here") {
  if (userMarker) userMarker.remove();
  userMarker = L.marker([lat, lon], { icon: redIcon }).addTo(map).bindPopup(label);
  map.setView([lat, lon], 14);
  lastCoords = { lat, lon };
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
    const sport = (c.Sport || "handball").toLowerCase();
    const sportLabel = sport ? sport.charAt(0).toUpperCase() + sport.slice(1) : "";
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
        ${sportLabel ? `Sport: ${sportLabel}<br>` : ""}
        ${borough ? `${borough}<br>` : ""}
        ${dist ? `${dist}<br>` : ""}
        ${c.Num_Of_Courts ? `Number of Courts: ${c.Num_Of_Courts}<br>` : ""}
      </div>`;

    const icon = sportIcons[sport] || sportIcons.handball;
    const m = L.marker([lat, lon], { icon }).addTo(map).bindPopup(html);
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
  const sport = (sportSelect && sportSelect.value) || "handball";
  const url = `${API_BASE}/nearest?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(
    lon
  )}&limit=10&sport=${encodeURIComponent(sport)}`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
    setText(statusEl, `Nearest failed: HTTP ${res.status}`, "status");
    return;
  }
  const data = await res.json();
  setText(statusEl, "", "status");
  addCourts(data.results || []);
} catch (e) {
  setText(statusEl, "Failed to load nearby courts. See console for details.", "status");
  console.error(e);
}
}

// Reverse geocode
async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(`${API_BASE}/geocodeReverse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lon }),
      cache: "no-store",
    });
    if (!res.ok) {
      setText(addrLabel, "", "addrLabel");
      return;
    }
    const data = await res.json();
    setText(addrLabel, data.display_name || "", "addrLabel");
  } catch {
    setText(addrLabel, "", "addrLabel");
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

// Address search
document.getElementById("btnSearch").addEventListener("click", onSearch);
document.getElementById("address").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    onSearch();
  }
});

async function geocodeForwardWithRetry(address, attempts = 2) {
  let lastErr = null;

  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(`${API_BASE}/geocodeForward`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address }),
        cache: "no-store",
      });

      if (res.ok) {
        try {
          return await res.json();
        } catch (e) {
          const raw = await res.clone().text();
          throw new Error(`Invalid JSON response: ${raw.slice(0, 300)}`);
        }
      }

      const errBody = await res.text();
      lastErr = new Error(`HTTP ${res.status}: ${errBody.slice(0, 300)}`);
    } catch (e) {
      lastErr = e;
    }

    await new Promise((r) => setTimeout(r, 400 + i * 600));
  }

  throw lastErr || new Error("Geocode failed");
}

async function onSearch() {
  const address = document.getElementById("address").value.trim();
  if (!address) return;

  setText(statusEl, "Searching address…", "status");

  try {
    const data = await geocodeForwardWithRetry(address, 2);

    setUserMarker(data.lat, data.lon, data.display_name || "Selected location");
    if (userMarker) userMarker.openPopup();

    setText(addrLabel, data.display_name || "", "addrLabel");
    setText(statusEl, "", "status");
    fetchNearest(data.lat, data.lon);
  } catch (e) {
    console.error(e);
    setText(statusEl, "", "status");
    alert(
      `Address not found (or geocoder temporarily busy). Try again in a moment.\n\nDetails: ${
        e && e.message ? e.message : "Unknown error"
      }`
    );
  }
}

if (sportSelect) {
  sportSelect.addEventListener("change", () => {
    if (lastCoords) {
      fetchNearest(lastCoords.lat, lastCoords.lon);
    }
  });
}

// -------------------- Agent --------------------

async function askAgent() {
  const query = (inputEl.value || "").trim();
  if (!query) return;

  appendMessage("me", query);
  inputEl.value = "";

  setLoading(true);

  const typingId = `typing-${Date.now()}`;
  const typingRow = document.createElement("div");
  typingRow.className = "msgRow bot";
  typingRow.id = typingId;
  const typingBubble = document.createElement("div");
  typingBubble.className = "msg";
  typingBubble.textContent = "…";
  typingRow.appendChild(typingBubble);
  chatLog.appendChild(typingRow);
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await res.json();

    const t = document.getElementById(typingId);
    if (t) t.remove();

    if (!res.ok) {
      const msg = data?.detail || data?.error || `Agent error: HTTP ${res.status}`;
      appendMessage("bot", String(msg));
      return;
    }

    const answerText = data.text ?? data.response ?? "";
    appendMessage("bot", answerText || "(No response)");
  } catch (e) {
    const t = document.getElementById(typingId);
    if (t) t.remove();
    console.error(e);
    appendMessage("bot", "Sorry — the agent request failed. Check your server logs.");
  } finally {
    setLoading(false);
  }
}

sendBtn.addEventListener("click", askAgent);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    askAgent();
  }
});

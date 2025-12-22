# 🎾 AI-Powered NYC Tennis Courts Finder

A production-ready web application that helps users discover nearby public tennis courts in New York City using geospatial search and natural-language queries powered by an AI agent.

**Live Demo:** https://nyc-places.onrender.com
**Tech Stack:** FastAPI · Python · OpenAI Responses API · Docker · Pandas · Folium · Leaflet

---

## Overview

Users can:
- Find the **nearest tennis courts** based on their current location or a typed address
- Ask **natural-language questions** such as:
  - “How many tennis courts are there in NYC?”
  - “Which courts are closest to Central Park?”
- Interact with an AI agent that reasons over **real application data**

The app is containerized and deployed, making it a realistic production example

---

## Key Features

### 📍 Location-Aware Court Search
- Forward geocoding converts user-entered addresses into coordinates
- Real-time distance calculations between users and tennis courts
- Returns nearest courts with metadata and map visualization

### AI Agent (OpenAI Responses API)
- Uses OpenAI’s **Responses API**
- Handles free-form user questions about tennis courts
- Grounds responses in the project’s CSV dataset (no hallucinations)
- Maintains conversational context across queries

### Interactive Map
- NYC tennis courts rendered using Folium + Leaflet
- Visual markers update based on user location and search results

---

## Architecture

app/
├── server.py # FastAPI app & API routes
├── agent.py # AI agent logic (Responses API)
├── data_prep.py # Data loading & preprocessing
├── nearest.py # Distance calculations & nearest-neighbor logic
├── pydantic_models.py # Typed request/response models
├── static/ # Frontend assets (HTML / CSS / JS)
└── settings.py # Environment-based configuration

---

## 🛠️ Tech Stack

| Layer | Technology |
|-----|-----------|
| Backend API | FastAPI |
| AI | OpenAI Responses API |
| Data Processing | Pandas |
| Geospatial | Geopy |
| Visualization | Folium, Leaflet |
| Frontend | HTML, JavaScript |
| Deployment | Docker, Render |

---

## Example Queries

“How many tennis courts are there in NYC?”
“Which courts are closest to me?”
“Show me courts near Brooklyn Heights”

The AI agent dynamically queries and reasons over the dataset before responding.

---

## Local Setup

### Clone the repo
git clone https://github.com/your-username/Tennis-Practice.git

cd Tennis-Practice

### Run locally (Python)
pip install -r requirements.txt
python run_server.py


### Run with Docker
docker build -t tennis-courts-ai .
docker run -p 8000:8000 tennis-courts-ai

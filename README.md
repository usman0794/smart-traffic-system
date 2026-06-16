# Smart Traffic Intelligence System

A real-time AI-powered traffic monitoring system using YOLO, DeepSORT, FastAPI, PostgreSQL, and React.

## Features

- Vehicle Detection using YOLO
- Multi-Object Tracking using DeepSORT
- Vehicle Counting
- Incoming / Outgoing Traffic Analysis
- Vehicle Type Classification
- Traffic Density Monitoring
- Accident Detection
- Video Upload and Processing
- Analytics Dashboard
- PostgreSQL Data Storage
- One-Way / Two-Way Road Support

## Technology Stack

### Frontend
- React.js
- Tailwind CSS
- Axios
- Recharts

### Backend
- FastAPI
- OpenCV
- YOLO
- DeepSORT
- PostgreSQL
- SQLAlchemy

### AI / Computer Vision
- YOLO Vehicle Detection
- DeepSORT Tracking
- Traffic Density Analysis
- Accident Detection

---

## System Workflow

1. Upload Traffic Video
2. Select Road Type
3. Vehicle Detection
4. Vehicle Tracking
5. Traffic Analysis
6. Store Results in PostgreSQL
7. Display Analytics Dashboard

---

## Project Structure

smart-traffic-system/

├── backend/

│ ├── app/

│ │ ├── api/

│ │ ├── core/

│ │ ├── database/

│ │ └── main.py

│ └── requirements.txt

│

├── frontend/

│ ├── src/

│ │ ├── components/

│ │ ├── pages/

│ │ └── services/

│ └── package.json

│

├── outputs/

├── videos/

└── README.md

---

## Installation

### Backend

```bash
cd backend

python -m venv venv

source venv/Scripts/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## API Endpoints

### Analytics

GET /analytics/summary

GET /analytics/snapshots

GET /analytics/vehicle-events

GET /analytics/accidents

### Videos

POST /videos/upload

POST /videos/process/{filename}

---

## Future Enhancements

- Live Webcam Processing
- WebSocket Real-Time Dashboard
- Traffic Forecasting
- PDF Reports
- Email Alerts

---

## Author

Muhammad Usman Ali

Computer Science

University of Management and Technology (UMT)

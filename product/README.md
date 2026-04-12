# Customer Segmentation Tool

## Quick start

### Backend
```bash
cd product/backend
pip install -r requirements.txt
uvicorn main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend
```bash
cd product/frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  Segmentation engines (Pandas + sklearn)
                                                          ↓
                                                   CSV download
```

## Wizard flow

| Step | What happens |
|------|-------------|
| 1 | Choose method: RFM Quintiles, RFM K-Means, ABC, LRFMS |
| 2 | Upload CSV or Excel file |
| 3 | Auto-map columns, confirm or adjust |
| 4 | Clean data (nulls, negatives, duplicates) |
| 5 | Configure method parameters |
| 6 | View results and download CSV |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload file, returns session_id |
| POST | `/mapping/auto` | Auto-detect column mapping |
| POST | `/mapping/confirm` | Confirm column mapping |
| POST | `/clean` | Clean data |
| POST | `/segment/rfm-quintiles` | Run RFM quintile segmentation |
| POST | `/segment/rfm-kmeans` | Run RFM K-Means segmentation |
| POST | `/segment/abc` | Run ABC analysis |
| POST | `/segment/lrfms` | Run LRFMS time-series segmentation |
| GET | `/segment/download/{session_id}/{token}` | Download result CSV |

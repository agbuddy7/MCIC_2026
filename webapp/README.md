# Person C: Defense Lab UI

React frontend plus a Python API so the demo can call the real gate and classifier.

## Run locally

From the repo root:

```bash
pip install -r requirements.txt
python webapp/backend/app.py
```

In a second terminal:

```bash
cd webapp/frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` to port 5000.

## API

- `GET /api/catalog` — featured and grouped conversation IDs
- `POST /api/simulate` — `{ "conversationId": "inj-1000" }`
- `GET /api/evaluation` — gate vs detector table
- `GET /api/metrics` — holdout precision / recall / F1 / AUC

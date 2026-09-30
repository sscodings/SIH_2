.PHONY: install seed train test dev run-backend run-frontend clean

install:
	cd backend && python -m venv venv && ./venv/Scripts/pip install -r requirements.txt
	cd frontend && npm install

seed:
	cd backend && ./venv/Scripts/python -m app.db.seed

train:
	cd backend && ./venv/Scripts/python -m app.ml.train

test:
	cd backend && ./venv/Scripts/pytest tests/

dev:
	@echo "Starting ChainNetra backend and frontend..."
	start cmd /k "cd backend && set PYTHONPATH=. && .\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
	start cmd /k "cd frontend && npm run dev"

clean:
	rm -rf backend/venv frontend/node_modules frontend/dist

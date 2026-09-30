.PHONY: install seed train test dev run-backend run-frontend clean

ifeq ($(OS),Windows_NT)
	VENV_BIN = backend/venv/Scripts
else
	VENV_BIN = backend/venv/bin
endif

PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip
PYTEST = $(VENV_BIN)/pytest
UVICORN = $(VENV_BIN)/uvicorn

install:
	cd backend && python -m venv venv
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install

seed:
	cd backend && $(PYTHON) -m app.db.seed

train:
	cd backend && $(PYTHON) -m app.ml.train

test:
	cd backend && $(PYTEST) tests/

audit: pip-audit npm-audit

pip-audit:
	$(PIP) install pip-audit && $(VENV_BIN)/pip-audit --requirement backend/requirements.txt

npm-audit:
	cd frontend && npm audit

run-backend:
	cd backend && $(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

clean:
	rm -rf backend/venv frontend/node_modules frontend/dist

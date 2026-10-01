# Cross-platform Makefile for ChainNetra
# Delegates to stdlib scripts/dev.py to guarantee consistency across Linux, macOS, and Windows.

.PHONY: setup seed dev test lint check docker-up docker-down clean

PYTHON ?= python3

# Fallback detection for python executable
ifeq ($(OS),Windows_NT)
	PYTHON := python
endif

setup:
	$(PYTHON) scripts/dev.py setup

seed:
	$(PYTHON) scripts/dev.py seed

dev:
	$(PYTHON) scripts/dev.py dev

test:
	$(PYTHON) scripts/dev.py test

lint:
	$(PYTHON) scripts/dev.py lint

check:
	$(PYTHON) scripts/dev.py check

docker-up:
	$(PYTHON) scripts/dev.py docker-up

docker-down:
	$(PYTHON) scripts/dev.py docker-down

clean:
	rm -rf .venv backend/venv frontend/node_modules frontend/dist __pycache__ .pytest_cache

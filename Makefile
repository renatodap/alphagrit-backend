PY=python
PIP=pip

.PHONY: setup install run dev fmt lint test pre-commit

setup:
	$(PY) -m venv .venv
	. .venv/bin/activate || .venv\Scripts\activate && $(PIP) install --upgrade pip
	. .venv/bin/activate || .venv\Scripts\activate && $(PIP) install -r requirements.txt
	. .venv/bin/activate || .venv\Scripts\activate && pre-commit install

install:
	$(PIP) install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	black . && isort .

lint:
	ruff . && mypy app

test:
	pytest -q

pre-commit:
	pre-commit run --all-files

.PHONY: run setup initdb

all: run

setup:
	python3 -m venv venv
	@echo "Installing python dependencies"
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Setting up frontend dependencies..."
	cd frontend && npm install
	@echo "Setup complete. Activate venv with: . venv/bin/activate"

run:
	@. venv/bin/activate && flask run

initdb:
	@. venv/bin/activate && python create_db.py

populate:
	@. venv/bin/activate && python populate_warehouse.py

js:
	@echo "Starting frontend development server (npm run dev)..."
	cd frontend && npm run dev

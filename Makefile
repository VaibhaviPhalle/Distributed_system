.PHONY: up down setup-policies test demo dashboard help install

# Default target when 'make' is run without arguments
help:
	@echo "Available commands:"
	@echo "  make up          - Start Docker containers"
	@echo "  make down        - Stop Docker containers"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Setup tenant policies"
	@echo "  make test        - Run Locust tests"
	@echo "  make dashboard   - Launch the Streamlit dashboard"
	@echo "  make demo        - Full flow (Install -> Up -> Setup -> Test)"

# Setup/Installation
install:
	pip install -r requirements.txt

# Docker Control
up:
	docker-compose up -d

down:
	docker-compose down -v

# Logic
setup:
	@echo "Waiting for API to be ready..."
	@until curl -s http://localhost:8000/healthz > /dev/null; do \
        echo "Service not ready... sleeping 2s"; \
        sleep 2; \
    done
	@echo "API is ready. Configuring tenant policies..."
	curl -X PUT http://localhost:8000/policies/GoodCitizen -H "Content-Type: application/json" -d '{"limit": 100, "window": 60}'
	curl -X PUT http://localhost:8000/policies/SpikyUser -H "Content-Type: application/json" -d '{"limit": 20, "window": 60}'
	@echo "\nPolicies updated!"

# Run Locust Tests
test:
	locust -f locustfile.py -u 20 -r 5 --host http://localhost:8000

# Run Dashboard
dashboard:
	streamlit run dashboard.py

# Full Orchestration
# Note: we use install and setup as dependencies, not as commands inside the flow
demo: up setup test
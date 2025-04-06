.PHONY: install run-cli run-web clean test lint collect-data venv check-env install-fix

# Python interpreter to use
PYTHON = python3
VENV_DIR = venv
VENV_BIN = $(VENV_DIR)/bin
VENV_PYTHON = $(VENV_BIN)/python
VENV_PIP = $(VENV_BIN)/pip

# Check if virtual environment exists
check-env:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Creating one..."; \
		make venv; \
	fi

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)"

# Install dependencies
install: check-env
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "Dependencies installed successfully"

# Install dependencies with fix for Levenshtein issues
install-fix: check-env
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt --no-deps fuzzywuzzy
	@echo "Dependencies installed successfully with Levenshtein fix"

# Run the CLI version
run-cli: check-env
	$(VENV_PYTHON) run.py --mode cli

# Run the web interface
run-web: check-env
	$(VENV_PYTHON) run.py --mode web
	# If the above fails, try running streamlit directly from the virtual environment
	$(VENV_BIN)/streamlit run app/streamlit_app.py

# Collect data from external API
collect-data: check-env
	$(VENV_PYTHON) utils/data_collector.py

# Clean up Python cache files and virtual environment
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	rm -rf $(VENV_DIR)
	@echo "Cleaned up Python cache files and virtual environment"

# Run tests
test: check-env
	$(VENV_PYTHON) -m pytest tests/

# Run linting
lint: check-env
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m black . --check
	$(VENV_PYTHON) -m isort . --check-only

# Format code
format: check-env
	$(VENV_PYTHON) -m black .
	$(VENV_PYTHON) -m isort .

# Help command
help:
	@echo "Available commands:"
	@echo "  make install      - Install project dependencies in virtual environment"
	@echo "  make install-fix  - Install dependencies with fix for Levenshtein issues"
	@echo "  make run-cli      - Run the CLI version"
	@echo "  make run-web      - Run the web interface"
	@echo "  make collect-data - Collect fresh data from external API"
	@echo "  make clean        - Clean up Python cache files and virtual environment"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make venv         - Create virtual environment"
	@echo "  make help         - Show this help message" 
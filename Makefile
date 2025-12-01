.PHONY: help install test lint format type-check lint-all clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install package with dev dependencies"
	@echo "  make test        - Run tests with coverage"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Format code with black"
	@echo "  make type-check  - Run mypy type checker"
	@echo "  make lint-all    - Run all linting checks (black, ruff, mypy)"
	@echo "  make clean       - Remove build artifacts"

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

test:
	python -m pytest tests/ --cov=shinzo --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

lint-all:
	@echo "Running all linting checks..."
	@echo "\n==> Running Black formatter check..."
	black --check src/ tests/
	@echo "\n==> Running Ruff linter..."
	ruff check src/ tests/
	@echo "\n==> Running MyPy type checker..."
	mypy src/
	@echo "\n✅ All linting checks passed!"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

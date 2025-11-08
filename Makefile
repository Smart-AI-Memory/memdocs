.PHONY: help install install-dev test test-api test-all lint format clean build docs

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in editable mode
	pip install -e .

install-dev:  ## Install with all development dependencies
	pip install -e ".[dev,embeddings,all]"

test:  ## Run tests (excluding API tests)
	pytest -m "not api" --cov=memdocs --cov-report=term-missing --cov-report=html -v

test-api:  ## Run API integration tests (costs money!)
	@echo "⚠️  WARNING: This will make real API calls and cost money (~\$$0.10-0.20)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		pytest -m api -v; \
	fi

test-all:  ## Run all tests including API tests
	pytest --cov=memdocs --cov-report=term-missing --cov-report=html -v

test-coverage:  ## Run tests and open coverage report
	pytest --cov=memdocs --cov-report=html -v
	open htmlcov/index.html

lint:  ## Run code quality checks
	@echo "Running ruff..."
	ruff check memdocs/ tests/
	@echo "Running black..."
	black --check memdocs/ tests/
	@echo "Running mypy..."
	mypy memdocs/ --ignore-missing-imports

format:  ## Auto-format code
	black memdocs/ tests/
	ruff check --fix memdocs/ tests/

type-check:  ## Run mypy type checking
	mypy memdocs/ --ignore-missing-imports

security:  ## Run security audit
	pip-audit

clean:  ## Remove build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

publish-test:  ## Publish to TestPyPI
	python -m build
	twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI (use with caution!)
	@echo "⚠️  WARNING: This will publish to PyPI!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python -m build; \
		twine upload dist/*; \
	fi

docs-serve:  ## Serve documentation locally (when docs are set up)
	@echo "Documentation serving not yet implemented"

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

ci:  ## Run full CI pipeline locally
	@echo "Running full CI pipeline..."
	$(MAKE) lint
	$(MAKE) test
	@echo "✅ CI pipeline passed!"

demo:  ## Run a demo of memdocs
	@echo "Running MemDocs demo..."
	memdocs review memdocs/schemas.py --scope file

version:  ## Show current version
	@python -c "from memdocs import __version__; print(f'MemDocs v{__version__}')"

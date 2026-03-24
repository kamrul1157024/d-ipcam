.PHONY: setup install run clean test lint help build dmg

help:
	@echo "D-IPCam - Dahua IP Camera Viewer"
	@echo ""
	@echo "Usage:"
	@echo "  make setup    - Install dependencies with uv"
	@echo "  make run      - Run the application"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linter"
	@echo "  make build    - Build macOS app bundle"
	@echo "  make dmg      - Build macOS DMG installer"
	@echo "  make clean    - Remove cache files"
	@echo ""

setup:
	uv sync
	@echo ""
	@echo "Setup complete! Run 'make run' to start the application."

install:
	uv sync

run:
	uv run python -m d_ipcam.main

run-dev:
	uv run python -m d_ipcam.main 2>&1 | tee d-ipcam.log

test:
	uv run pytest tests/

lint:
	uv run ruff check d_ipcam/

format:
	uv run ruff format d_ipcam/

build:
	uv run pyinstaller d-ipcam.spec --noconfirm

dmg: build
	./scripts/build_dmg.sh

clean:
	rm -rf .venv
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf d_ipcam/__pycache__
	rm -rf d_ipcam/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf build
	rm -rf dist

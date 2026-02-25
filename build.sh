#!/bin/bash
set -e

echo "Running integration tests before build..."
pytest itest/ -v --tb=short || { echo "Integration tests failed!"; exit 1; }

echo "Integration tests passed. Building Docker image..."
docker build -t crowdsec-dashboard:latest .

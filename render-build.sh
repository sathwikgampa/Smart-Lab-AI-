#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "========================================="
echo "Building SmartLab AI Production Bundle..."
echo "========================================="

echo "Step 1: Installing frontend dependencies and building production bundle..."
cd frontend
npm ci || npm install
npm run build
cd ..

echo "Step 2: Installing Python backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "========================================="
echo "Build succeeded! Ready for production."
echo "========================================="

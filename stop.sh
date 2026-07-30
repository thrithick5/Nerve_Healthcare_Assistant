#!/bin/bash

echo "Stopping AI Healthcare Assistant..."

# Kill backend
pkill -f "uvicorn app.main:app" 2>/dev/null
echo "Backend stopped"

# Kill frontend
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null
echo "Frontend stopped"

echo "All services stopped"

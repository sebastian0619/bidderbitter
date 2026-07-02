#!/bin/bash
# Kill existing processes
pkill -f uvicorn 2>/dev/null
pkill -f vite 2>/dev/null
sleep 1

# Start backend
cd backend
rm -f bidtool.db
rm -rf __pycache__
nohup /usr/bin/python3.13 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
echo "Backend started: $!"

# Start frontend
cd ../frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
echo "Frontend started: $!"

# Wait and check
sleep 3
echo ""
echo "=== Services Status ==="
curl -s http://localhost:8000/api/health && echo " - Backend OK"
curl -s http://localhost:5173 | grep -o "<title>.*</title>" && echo " - Frontend OK"

#!/bin/bash
cd backend
nohup /usr/bin/python3.13 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
echo "Backend PID: $!"

cd ../frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
echo "Frontend PID: $!"

sleep 3
echo "Backend: $(curl -s http://localhost:8000/api/health)"
echo "Frontend: $(curl -s http://localhost:5173 | head -1)"

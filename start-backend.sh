#!/bin/bash
cd /workingfile/0.Archive/dev-projects/bidtool/backend
rm -f bidtool.db
/usr/bin/python3.13 -m uvicorn main:app --host 0.0.0.0 --port 8000

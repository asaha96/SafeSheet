#!/bin/bash
# Start SafeSheet frontend

cd "$(dirname "$0")/frontend"
npm install
npm run dev


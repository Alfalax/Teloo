@echo off
echo Starting TeLOO V3 Application Services...
echo.

echo Building and starting all services...
docker-compose up --build

echo.
echo All services should now be running!
echo.
echo Access URLs:
echo - Admin Frontend: http://localhost:3000
echo - Advisor Frontend: http://localhost:3001
echo - Core API Docs: http://localhost:8000/docs
echo - Agent IA Docs: http://localhost:8001/docs
echo - Analytics Docs: http://localhost:8002/docs
echo - Realtime Gateway: http://localhost:8003
echo - Files Service Docs: http://localhost:8004/docs
echo - MinIO Console: http://localhost:9001
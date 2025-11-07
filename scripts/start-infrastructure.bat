@echo off
echo Starting TeLOO V3 Infrastructure Services...
echo.

echo Starting PostgreSQL, Redis, and MinIO...
docker-compose up -d postgres redis minio

echo.
echo Waiting for services to be healthy...
timeout /t 10 /nobreak > nul

echo.
echo Checking service status...
docker-compose ps postgres redis minio

echo.
echo Infrastructure services started successfully!
echo.
echo PostgreSQL: localhost:5432
echo Redis: localhost:6379  
echo MinIO Console: http://localhost:9001 (teloo_minio / teloo_minio_password)
echo.
echo You can now start the application services with: start-services.bat
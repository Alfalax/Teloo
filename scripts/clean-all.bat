@echo off
echo WARNING: This will remove all containers, volumes, and data!
echo.
set /p confirm="Are you sure you want to continue? (y/N): "
if /i "%confirm%" neq "y" (
    echo Operation cancelled.
    exit /b 0
)

echo.
echo Stopping and removing all containers, networks, and volumes...
docker-compose down -v --remove-orphans

echo.
echo Removing all TeLOO images...
docker images | findstr teloo | for /f "tokens=3" %%i in ('more') do docker rmi %%i

echo.
echo Cleanup completed!
@echo off
echo Setting up TeLOO V3 environment files...
echo.

echo Copying environment files for backend services...
if not exist "services\core-api\.env" (
    copy "services\core-api\.env.example" "services\core-api\.env"
    echo Created services\core-api\.env
)

if not exist "services\agent-ia\.env" (
    copy "services\agent-ia\.env.example" "services\agent-ia\.env"
    echo Created services\agent-ia\.env
)

if not exist "services\analytics\.env" (
    copy "services\analytics\.env.example" "services\analytics\.env"
    echo Created services\analytics\.env
)

if not exist "services\realtime-gateway\.env" (
    copy "services\realtime-gateway\.env.example" "services\realtime-gateway\.env"
    echo Created services\realtime-gateway\.env
)

if not exist "services\files\.env" (
    copy "services\files\.env.example" "services\files\.env"
    echo Created services\files\.env
)

echo.
echo Copying environment files for frontend services...
if not exist "frontend\admin\.env" (
    copy "frontend\admin\.env.example" "frontend\admin\.env"
    echo Created frontend\admin\.env
)

if not exist "frontend\advisor\.env" (
    copy "frontend\advisor\.env.example" "frontend\advisor\.env"
    echo Created frontend\advisor\.env
)

echo.
echo Environment setup completed!
echo.
echo IMPORTANT: Please review and update the following files with your actual configuration:
echo - services\core-api\.env (JWT_SECRET_KEY)
echo - services\agent-ia\.env (WhatsApp and LLM API keys)
echo - All other .env files as needed
echo.
echo After updating the environment files, you can start the infrastructure with:
echo   scripts\start-infrastructure.bat
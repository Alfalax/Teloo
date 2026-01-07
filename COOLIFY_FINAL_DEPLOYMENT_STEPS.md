# Coolify Final Deployment Steps - Backend + Analytics with Nginx Gateway

## Overview
This guide will help you deploy Backend (Core API) and Analytics as a single Coolify application using nginx as a reverse proxy gateway. This is the correct architecture because Coolify only exposes 1 port per application.

## Architecture
```
Coolify (Port 80) → Nginx Gateway → /api/* → Backend (Core API) :8000
                                  → /analytics/* → Analytics :8002
                                  → postgres :5432
                                  → redis :6379
```

All services run in the same Docker network and can communicate using service names.

---

## Step 1: Delete Standalone Services (Cleanup)

### 1.1 Delete Analytics Application
1. Go to Coolify dashboard
2. Find the **Analytics** application (standalone)
3. Click on it → Settings → Delete Application
4. Confirm deletion

### 1.2 Delete Redis Database
1. Go to Coolify dashboard
2. Find the **Redis** database (standalone)
3. Click on it → Settings → Delete Database
4. Confirm deletion

---

## Step 2: Update Backend Application Configuration

### 2.1 Change Build Pack to Docker Compose
1. Go to your **Backend** application in Coolify
2. Click on **General** tab
3. Find **Build Pack** section
4. Change from "Dockerfile" to **"Docker Compose"**
5. In **Docker Compose File** field, enter: `docker-compose.coolify.yml`
6. Click **Save**

### 2.2 Configure Environment Variables
1. Still in the Backend application, click on **Environment Variables** tab
2. Add/Update these variables:

```
BACKEND_CORS_ORIGINS=http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-teloo-2025
AGENT_IA_API_KEY=m4YQECAHqUZl_4O9p3ZG8YlYjvFF_IAbxiFu6l_6epk
ANALYTICS_API_KEY=wHe7MRSvi1prmjG9H75CmiDxaRON7mDDbe9fKQ8bt0E
```

**IMPORTANT**: 
- For `BACKEND_CORS_ORIGINS`, use the plain URL without brackets or quotes
- If you need multiple origins, separate with commas: `http://url1,http://url2`

3. Click **Save**

### 2.3 Update Port Configuration
1. Click on **Ports** or **Network** tab
2. Change the exposed port from **8000** to **80** (nginx port)
3. Click **Save**

---

## Step 3: Deploy the Application

### 3.1 Trigger Deployment
1. Go to **Deployments** tab
2. Click **Deploy** button
3. Wait for the deployment to complete (this will take a few minutes)

### 3.2 Monitor Deployment Logs
Watch the logs for:
- ✅ Postgres starting and becoming healthy
- ✅ Redis starting and becoming healthy
- ✅ Core API starting and connecting to database
- ✅ Analytics starting and connecting to database
- ✅ Nginx starting and routing requests

### 3.3 Verify Deployment Success
Once deployment completes, test these endpoints:

**Test Backend:**
```bash
curl http://g0k48wkwowwokcgoc480oo4g.72.62.130.152.sslip.io/api/
```
Should return: `{"service":"TeLOO V3 Core API","version":"3.0.0",...}`

**Test Analytics:**
```bash
curl http://g0k48wkwowwokcgoc480oo4g.72.62.130.152.sslip.io/analytics/
```
Should return: `{"service":"TeLOO V3 Analytics","version":"3.0.0",...}`

**Test Health:**
```bash
curl http://g0k48wkwowwokcgoc480oo4g.72.62.130.152.sslip.io/health
```
Should return: `healthy`

---

## Step 4: Update Frontend Admin Configuration

### 4.1 Update Analytics API URL
1. Go to **Frontend Admin** application in Coolify
2. Click on **Environment Variables** tab
3. Find or add `VITE_ANALYTICS_API_URL`
4. Set it to: `http://g0k48wkwowwokcgoc480oo4g.72.62.130.152.sslip.io/analytics`
   
   **IMPORTANT**: Note the `/analytics` path, NOT a separate domain!

5. Click **Save**

### 4.2 Verify Backend API URL
Make sure `VITE_API_URL` is set to:
```
http://g0k48wkwowwokcgoc480oo4g.72.62.130.152.sslip.io/api
```

### 4.3 Redeploy Frontend
1. Go to **Deployments** tab
2. Click **Deploy** button
3. Wait for deployment to complete

---

## Step 5: Test End-to-End

### 5.1 Test Login
1. Open Frontend Admin: `http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io`
2. Login with your credentials
3. Should work without CORS errors ✅

### 5.2 Test Analytics Dashboard
1. After login, navigate to Dashboard
2. Check if analytics widgets load
3. Open browser DevTools → Network tab
4. Look for requests to `/analytics/*` endpoints
5. Should return data without 404 errors ✅

### 5.3 Test Configuration Page
1. Navigate to Configuración page
2. Should load without CORS errors ✅

---

## Troubleshooting

### If Backend deployment fails:
1. Check logs for database connection errors
2. Verify `DATABASE_URL` is correct: `postgres://teloo_admin:Teloo2025.@postgres:5432/teloo_production`
3. Check if postgres container is healthy

### If Analytics returns 503:
1. Check Analytics logs for database connection errors
2. Verify Analytics can connect to postgres and redis
3. Check healthcheck status: `curl http://DOMAIN/analytics/health`

### If Frontend can't connect:
1. Verify CORS origins include Frontend URL
2. Check browser console for CORS errors
3. Verify API URLs use `/api` and `/analytics` paths

### If nginx routing fails:
1. Check nginx logs in Coolify
2. Verify `nginx.coolify.conf` is mounted correctly
3. Test nginx health: `curl http://DOMAIN/health`

---

## What Changed and Why

### Before (WRONG):
- Backend: Separate Coolify app with postgres/redis
- Analytics: Separate Coolify app (couldn't connect to postgres/redis)
- Redis: Separate database (isolated network)
- **Problem**: Services in different Coolify apps can't communicate

### After (CORRECT):
- Single Coolify app with docker-compose
- Nginx gateway routes `/api/*` to Backend and `/analytics/*` to Analytics
- All services (nginx, backend, analytics, postgres, redis) in same Docker network
- **Solution**: Services can communicate using hostnames (postgres, redis, core-api, analytics)

### Why Nginx?
- Coolify only exposes 1 port per application
- We need to expose both Backend (8000) and Analytics (8002)
- Nginx listens on port 80 and routes to internal services
- Frontend makes all requests to same domain with different paths

---

## Summary

After completing these steps:
- ✅ Backend accessible at: `http://DOMAIN/api/*`
- ✅ Analytics accessible at: `http://DOMAIN/analytics/*`
- ✅ Frontend can connect to both services
- ✅ No CORS errors
- ✅ No 404 errors on analytics endpoints
- ✅ All services in same network, can communicate
- ✅ Single Coolify application, easier to manage

---

## Next Steps After Successful Deployment

1. Test all functionality in Frontend Admin
2. Monitor logs for any errors
3. Set up monitoring/alerts if needed
4. Document any custom configurations
5. Consider adding more services (agent-ia, files, realtime-gateway) to the same docker-compose if needed

---

**Created**: 2026-01-07
**Status**: Ready for deployment
**Estimated Time**: 15-20 minutes

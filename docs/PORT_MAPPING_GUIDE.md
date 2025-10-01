# Port Mapping Guide - Billing System

## 🚨 Critical Port Configuration

After the bun migration on 2025-10-01, the API Gateway port was changed from **3000** to **8080** to avoid conflicts with the Next.js frontend.

---

## 📍 Complete Port Mapping

| Component | Port | URL | Environment Variable | Notes |
|-----------|------|-----|---------------------|-------|
| **Frontend (Next.js)** | 3000 | `http://localhost:3000` | (Next.js default) | Web UI for users |
| **API Gateway (Fastify)** | 8080 | `http://localhost:8080` | `PORT=8080` | Changed from 3000 |
| **Transformation Service** | 3001 | `http://localhost:3001` | `PORT=3001` | Python/FastAPI |
| **Rating Service** | 3002 | `http://localhost:3002` | `PORT=3002` | Python/FastAPI |
| **Billing Service** | 3003 | `http://localhost:3003` | `PORT=3003` | Python/FastAPI |
| **PostgreSQL** | 5432 | `localhost:5432` | (default) | Database |

---

## ⚙️ Configuration Files

### Frontend (`frontend/.env.local`)
```bash
# Frontend on :3000, API Gateway on :8080
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### API Gateway (`api-gateway/.env`)
```bash
PORT=8080
TRANSFORMATION_SERVICE_URL=http://localhost:3001
RATING_SERVICE_URL=http://localhost:3002
BILLING_SERVICE_URL=http://localhost:3003
```

### Python Services (each service has its own `.env` or default port)
```bash
# services/transformation/.env
PORT=3001

# services/rating/.env
PORT=3002

# services/billing/.env
PORT=3003
```

---

## 🔧 Troubleshooting Port Conflicts

### Issue: Frontend can't connect to API Gateway

**Symptoms**:
- Network errors in browser console
- 404 or connection refused errors
- "Failed to fetch" errors

**Solution**:
1. Check that API Gateway is running on port 8080:
   ```bash
   curl http://localhost:8080/health
   ```

2. Verify frontend environment variable:
   ```bash
   cd frontend
   cat .env.local | grep NEXT_PUBLIC_API_URL
   # Should show: NEXT_PUBLIC_API_URL=http://localhost:8080
   ```

3. Check browser network tab - requests should go to `localhost:8080`, NOT `localhost:3000`

### Issue: Port already in use

**Error**: `EADDRINUSE: address already in use :::8080`

**Solution**:
```bash
# Find process using port 8080
lsof -i :8080

# Kill process (use PID from above command)
kill -9 <PID>

# Or use different port
PORT=8081 bun run dev
```

---

## 🚀 Startup Commands

### Option 1: Manual Startup (Recommended for Development)

```bash
# Terminal 1: Start API Gateway
cd api-gateway
bun run dev
# Should show: API Gateway listening on 0.0.0.0:8080

# Terminal 2: Start Frontend
cd frontend
bun run dev
# Should show: ready - started server on 0.0.0.0:3000

# Terminal 3: Start Python Services
python3 scripts/start_services.py
# Should show all 3 services starting on ports 3001, 3002, 3003
```

### Option 2: Script-based Startup

```bash
# From project root
python3 scripts/start_all.py
```

---

## 🔍 Verification Checklist

After starting all services, verify each endpoint:

```bash
# Frontend (should show HTML)
curl http://localhost:3000

# API Gateway health
curl http://localhost:8080/health

# Transformation service
curl http://localhost:3001/health

# Rating service
curl http://localhost:3002/health

# Billing service
curl http://localhost:3003/health
```

---

## 📝 Migration Notes (2025-10-01)

### What Changed
- API Gateway port: `3000` → `8080`
- Package manager: `npm` → `bun`
- Frontend API client fallback: Updated to 8080

### What Stayed the Same
- Frontend port: Still `3000` (Next.js default)
- Backend services: Still `3001`, `3002`, `3003`
- Database port: Still `5432`

### Files Modified
1. `api-gateway/src/server.js` - Line 55: Changed default port to 8080
2. `api-gateway/package.json` - All scripts changed to use bun
3. `frontend/src/lib/api.ts` - Line 5: Changed fallback to 8080
4. `frontend/.env.example` - Line 3: Updated to 8080
5. `frontend/.env.local` - Already had correct value (8080)

---

## 🐛 Common Issues

### 1. Frontend shows "Network Error"
**Cause**: Frontend trying to connect to wrong port
**Fix**: Check `NEXT_PUBLIC_API_URL` in `.env.local`

### 2. API Gateway returns 404 for all routes
**Cause**: API Gateway not running
**Fix**: Start API Gateway with `cd api-gateway && bun run dev`

### 3. Backend services unreachable
**Cause**: Python services not started
**Fix**: Run `python3 scripts/start_services.py`

### 4. Port conflict on 8080
**Cause**: Another application using port 8080
**Fix**: Kill process or change `PORT` in `api-gateway/.env`

---

## 📚 Related Documentation

- Main project README: `../README.md`
- System readiness guide: `./SYSTEM_READY_383.md`
- Frontend setup: `../frontend/README.md`
- API Gateway setup: `../api-gateway/README.md`

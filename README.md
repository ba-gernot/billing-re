# Billing RE System

Modern microservices-based billing system for complex transport logistics (rail+road) processing orders through 6 stages: Input → Transformation → Rating → Pricing → Billing → Invoice.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Bun (Node.js runtime)
- Python 3.11+

### Development Setup

1. **Clone and setup environment**
```bash
cd billing-re
cp .env.example .env
# Edit .env with your Supabase credentials
```

2. **Start infrastructure**
```bash
docker-compose up -d postgres redis
```

3. **Initialize database**
```bash
# Run migrations
docker exec -i billing-re_postgres_1 psql -U billing_user -d billing_re < database/migrations/001_initial.sql
docker exec -i billing-re_postgres_1 psql -U billing_user -d billing_re < database/seeds/002_master_data.sql
```

4. **Start services (separate terminals)**
```bash
# Transformation Service
cd services/transformation
pip install -r requirements.txt
uvicorn main:app --reload --port 3001

# Rating Service
cd services/rating
pip install -r requirements.txt
uvicorn main:app --reload --port 3002

# Billing Service
cd services/billing
pip install -r requirements.txt
uvicorn main:app --reload --port 3003

# API Gateway
cd api-gateway
npm install
npm run dev
```

### Test End-to-End

```bash
curl -X POST http://localhost:3000/api/v1/process-order \
  -H "Content-Type: application/json" \
  -d @"../Requirement documents/1_operative_Auftragsdaten.json"
```

Expected result: €383 total invoice

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Transformation  │ => │ Rating Service  │ => │ Billing Service │
│ Service (3001)  │    │ (3002)          │    │ (3003)          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               ↑
┌─────────────────────────────────────────────────────────────────┐
│                API Gateway (3000)                               │
│            Orchestration | Authentication | Routing            │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + Redis                           │
│          Database | Caching | Rules | Prices                   │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Main Processing
- `POST /api/v1/process-order` - Complete order processing pipeline

### Health Checks
- `GET /health` - API Gateway health
- `GET /health/services` - All services health
- `GET /api/v1/process-order/health` - Order processing health

## Project Status

✅ **Phase 1 Complete**: Foundation
- [x] Repository structure
- [x] Docker environment
- [x] Database schema
- [x] Base services setup
- [x] API Gateway orchestration

🔄 **Phase 2 Next**: Core Services Implementation
- [ ] Input validation & enrichment
- [ ] DMN rule engine integration
- [ ] Database price lookups
- [ ] PDF invoice generation

## Development Guidelines

- **Services**: Python/FastAPI for business logic
- **Gateway**: Node.js/Fastify for orchestration
- **Database**: PostgreSQL with full schema
- **Testing**: E2E scenarios with expected €383 result
- **Deployment**: Docker containers + AWS Lambda
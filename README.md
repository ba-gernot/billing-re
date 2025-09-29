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

✅ **Phase 2 Complete**: Core Services Implementation
- [x] Input validation & enrichment
- [x] DMN rule engine integration (with XLSX processor fallback)
- [x] Database price lookups
- [x] Tax calculation (Export/Import/Domestic)

✅ **Phase 3 Complete**: Business Rules & Pricing
- [x] Dynamic DMN rules in XLSX format (4 rule tables)
- [x] Weight classification (20A/20B/40A-40D)
- [x] Service determination with COLLECT policy
- [x] Trip type mapping (LB→Zustellung, LA→Abholung)
- [x] Tax determination rules
- [x] Dynamic pricing SQL generation
- [x] €383 target calculation validated (100% pass rate)

✅ **Phase 4 Complete**: Frontend & Integration
- [x] Next.js admin portal
- [x] E2E testing with sample order
- [x] Business logic validation tests
- [x] DMN rules validation suite

🔄 **Phase 5 In Progress**: Production Deployment
- [ ] AWS Lambda deployment
- [ ] Monitoring & logging
- [ ] PDF invoice generation
- [ ] Performance optimization

## Documentation

- **Current Implementation**: See `/DMN_DYNAMIC_IMPLEMENTATION_SUMMARY.md` for DMN and pricing details
- **Historical Context**: See `DMN_IMPLEMENTATION_DOCUMENTATION.md` for problem-solving journey
- **Project Overview**: See `CLAUDE.md` for architecture and commands
- **Progress Tracking**: See `Progress tracking/BILLING_RE_ROADMAP.md` for detailed roadmap

## Testing

### Business Logic Tests
```bash
python3 test_business_logic.py
# Tests transformation, weight classification, service determination, pricing, and tax
# Expected: €383 total, all tests passing
```

### DMN Rules Validation
```bash
python3 test_dmn_rules_validation.py
# Validates all 4 DMN XLSX files contain correct rules
# Expected: 100% pass rate (6 tests)
```

### End-to-End Integration
```bash
cd billing-re
python3 test_e2e.py
# Tests complete microservices pipeline with async calls
# Requires all 3 services running
```

## Development Guidelines

- **Services**: Python/FastAPI for business logic
- **Gateway**: Node.js/Fastify for orchestration
- **Database**: PostgreSQL with full schema
- **DMN Rules**: XLSX files in `shared/dmn-rules/` with three-layer fallback
- **Pricing**: Dynamic SQL generation from XLSX sources
- **Testing**: E2E scenarios with expected €383 result
- **Deployment**: Docker containers + AWS Lambda
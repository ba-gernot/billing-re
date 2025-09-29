# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern microservices-based billing system for complex transport logistics (rail+road). The system processes orders through 6 stages: Input → Transformation → Rating → Pricing → Billing → Invoice, with €383 expected result for the test scenario.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js/Vercel)                 │
│                   Rule Management & Monitoring               │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│              API Gateway (Node.js/Fastify)                   │
│            Authentication | Orchestration | Routing          │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────┬──────────────────┬────────────────────────────┐
│Transformation│  Rating Service  │   Billing Service          │
│   Service    │  (Python/FastAPI)│   (Python/FastAPI)         │
│(Python/FastAPI)               │                            │
└──────────────┴──────────────────┴────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Supabase)                     │
│          Auth | Database | Storage | Rules | Prices          │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Frontend**: Next.js 14 with App Router, TypeScript, Tailwind CSS, shadcn/ui
- **API Gateway**: Node.js/Fastify orchestrator at `:3000`
- **Services**: Python/FastAPI microservices
  - Transformation Service (`:3001`) - Input validation & enrichment
  - Rating Service (`:3002`) - Price determination & rules
  - Billing Service (`:3003`) - Invoice generation & tax calculation
- **Database**: PostgreSQL via Supabase with auth and RLS policies

## Development Commands

### Package Manager
- Use **bun** as the package manager and runtime for all JavaScript/TypeScript code
- Python services use pip with requirements.txt

### Frontend Development (billing-re/frontend/)
```bash
bun run dev          # Start development server with turbopack
bun run build        # Build for production with turbopack
bun run start        # Start production server
bun run lint         # Run ESLint
bun run test         # Run Jest tests
bun run test:watch   # Run tests in watch mode
bun run test:coverage # Run tests with coverage
```

### API Gateway (billing-re/api-gateway/)
```bash
npm run dev          # Start with nodemon
npm run start        # Start production server
npm test            # Run Jest tests
```

### Python Services (services/transformation/, services/rating/, services/billing/)
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port [3001|3002|3003]
```

### Full System Setup
```bash
cd billing-re
cp .env.example .env  # Configure Supabase credentials

# Start infrastructure
docker-compose up -d postgres redis

# Initialize database
docker exec -i billing-re_postgres_1 psql -U billing_user -d billing_re < database/migrations/001_initial.sql
docker exec -i billing-re_postgres_1 psql -U billing_user -d billing_re < database/seeds/002_master_data.sql

# Start all services (separate terminals)
cd services/transformation && uvicorn main:app --reload --port 3001
cd services/rating && uvicorn main:app --reload --port 3002
cd services/billing && uvicorn main:app --reload --port 3003
cd api-gateway && npm run dev
cd frontend && bun run dev
```

### End-to-End Testing
```bash
curl -X POST http://localhost:3000/api/v1/process-order \
  -H "Content-Type: application/json" \
  -d @"../Requirement documents/1_operative_Auftragsdaten.json"
```
Expected result: €383 total invoice

## Technology Stack

### Frontend
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: Zustand for global state
- **Forms**: React Hook Form + Zod validation
- **Auth**: Supabase Auth with JWT

### Backend
- **API Gateway**: Node.js 20+ with Fastify
- **Services**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ via Supabase
- **Validation**: Pydantic (Python), Zod (TypeScript)

### Code Quality
- **TypeScript**: Strict mode, ESLint, Prettier
- **Python**: Black formatter, type hints
- **Testing**: Jest (frontend), Pytest (backend)

## Business Logic

### Order Processing Pipeline
1. **Input**: Operational order JSON validation
2. **Transformation**: Field enrichment, service decomposition (main/trucking/additional)
3. **Rating**: DMN rule application, weight classification (20A/20B/40A/40B)
4. **Pricing**: Database price lookups with multi-level fallbacks
5. **Billing**: Tax calculation (Export 0%, Import reverse, Domestic 19%)
6. **Invoice**: PDF generation with German standards

### Key Rules
- Container weight classification affects pricing tiers
- Service 456 (security surcharge) only valid 2025-05-01 to 2025-08-31
- Export orders have 0% VAT, domestic orders 19% VAT
- €383 expected total for test scenario in requirement documents

## File Structure
```
billing-re/
├── frontend/                    # Next.js admin portal
├── api-gateway/                 # Fastify orchestrator
├── services/
│   ├── transformation/          # Input validation & enrichment
│   ├── rating/                  # Rules & pricing engine
│   │   ├── dmn/                # DMN engine with XLSX processor fallback
│   │   ├── rules/              # Hardcoded business logic fallbacks
│   │   └── pricing/            # Price calculations
│   └── billing/                 # Invoice generation
├── database/
│   ├── migrations/              # SQL schema changes
│   └── seeds/                   # Sample data + dynamic pricing SQL
└── shared/
    ├── dmn-rules/              # Business rule XLSX files (4 tables)
    └── price-tables/           # XLSX pricing data
```

## Progress Tracking
- Whenever you complete a phase from the roadmap, mark the respective progress in "Progress tracking/BILLING_RE_ROADMAP.md"
- Current status: Phase 4 complete (frontend & integration), Phase 5 pending (production deployment)

## DMN Implementation
- **Current State**: Dynamic DMN rules implemented with three-layer fallback architecture
- **Rule Files**: 4 XLSX files in `billing-re/shared/dmn-rules/`:
  - `weight_class.dmn.xlsx` - 6 rules (20A/20B/40A-40D)
  - `service_determination.dmn.xlsx` - 9 rules with COLLECT policy
  - `trip_type.dmn.xlsx` - 3 rules (LB→Zustellung, LA→Abholung)
  - `tax_calculation.dmn.xlsx` - 4 rules (Export/Import/Domestic)
- **Fallback Strategy**:
  1. Try pyDMNrules with `.dmn.xlsx` files (blocked by library bugs)
  2. Use XLSX Processor (custom Python parser) - currently active
  3. Use hardcoded Python rules (guaranteed fallback)
- **Validation**: 100% test pass rate via `test_dmn_rules_validation.py`
- **Documentation**: See `/DMN_DYNAMIC_IMPLEMENTATION_SUMMARY.md` for complete details

### ✅ Updating DMN Rules (Auto-Reload Enabled)
**Changes to XLSX files are detected automatically** (no restart needed):
```bash
# 1. Edit XLSX files in billing-re/shared/dmn-rules/
# 2. Save the file
# 3. Next API call automatically picks up changes ✅
```
**How it works**: XLSX Processor tracks file modification times and auto-reloads when files change. See `/PYDMNRULES_BUG_ANALYSIS.md` for technical details.

## Pricing System
- **Dynamic Generation**: `generate_pricing_sql.py` converts XLSX → SQL
- **Output Files** in `billing-re/database/seeds/`:
  - `dynamic_main_prices.sql` - Main service prices
  - `dynamic_additional_prices.sql` - Additional service prices
  - `hardcoded_prices_383.sql` - Baseline for €383 test scenario
- **Update Process**: Edit XLSX → Run generator → Load SQL → Prices updated

## Testing
- **Business Logic**: `billing-re/test_business_logic.py` - Unit tests without services
- **E2E Integration**: `billing-re/test_e2e.py` - Full pipeline with async calls
- **DMN Validation**: `test_dmn_rules_validation.py` - XLSX content validation
- **Expected Result**: €383 total for sample order

## Important Notes
- Database-driven rules with DMN integration (pyDMNrules with XLSX processor fallback)
- All services use structured logging with correlation IDs
- JWT tokens have 15-minute expiry with refresh capability
- Rate limiting: 100 requests/minute per user
- Maximum 10MB request size, 1000 records per API response
- Always use python3 in this project
- DMN files must be in `billing-re/shared/dmn-rules/` (not root-level)
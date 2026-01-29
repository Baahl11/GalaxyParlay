# 🌌 ParlayGalaxy

**Smart Football Betting Intelligence Platform**

ParlayGalaxy revoluciona la experiencia de apuestas deportivas mediante:
- 🎯 Predicciones ML calibradas y transparentes
- 🌌 Visualización Galaxy interactiva de oportunidades semanales
- 📊 Data quality scoring y transparencia total
- 🎨 UI/UX diseñada para decisiones rápidas e informadas

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Web)                   │
│  Next.js 14 + TypeScript + Tailwind + Shadcn/UI   │
│           + PixiJS (Galaxy Canvas)                  │
└──────────────────┬──────────────────────────────────┘
                   │ REST API
                   ▼
┌─────────────────────────────────────────────────────┐
│              Supabase (Backend)                     │
│  • PostgreSQL (data storage)                        │
│  • Row Level Security (RLS)                         │
│  • Realtime subscriptions                           │
│  • Edge Functions                                   │
└──────────────────┬──────────────────────────────────┘
                   │ Service Role
                   ▼
┌─────────────────────────────────────────────────────┐
│            Worker (Python FastAPI)                  │
│  • Ingesta API-Football                             │
│  • ML Models (Ensemble: XGBoost + Elo + Poisson)   │
│  • Scoring & Calibration                            │
│  • Quality Gates                                    │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
parlaygalaxy/
├── apps/
│   ├── web/                    # Next.js 14 App Router
│   │   ├── app/
│   │   │   ├── api/           # API routes
│   │   │   ├── galaxy/        # Galaxy page
│   │   │   └── layout.tsx
│   │   ├── components/        # React components
│   │   ├── lib/               # Utilities
│   │   └── __tests__/         # Tests
│   │
│   └── worker/                # Python FastAPI Worker
│       ├── app/
│       │   ├── jobs/          # Background jobs
│       │   ├── models/        # ML models
│       │   ├── api/           # API routes
│       │   └── main.py
│       ├── tests/             # Pytest tests
│       └── requirements.txt
│
├── packages/                   # Shared packages
│   ├── types/                 # TypeScript types
│   └── config/                # Shared configs
│
├── supabase/
│   ├── migrations/            # DB migrations
│   ├── seed.sql              # Seed data
│   └── config.toml
│
├── .github/
│   └── workflows/             # CI/CD
│
├── package.json              # Monorepo config
├── turbo.json                # Turborepo config
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 18.0.0
- **pnpm** >= 8.0.0
- **Python** >= 3.11
- **PostgreSQL** >= 15 (via Supabase)
- **Redis** >= 7.0 (for caching)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/parlaygalaxy.git
cd parlaygalaxy

# Install dependencies
pnpm install

# Setup Python environment
cd apps/worker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env.local

# Configure your keys:
# - Supabase URL & keys
# - API-Football key
# - Redis URL
# - Sentry DSN (optional)
```

### 3. Database Setup

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase (if not already)
supabase init

# Link to your project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push

# Seed initial data
psql $DATABASE_URL < supabase/seed.sql
```

### 4. Run Development

```bash
# Terminal 1: Web (Next.js)
pnpm web
# → http://localhost:3000

# Terminal 2: Worker (FastAPI)
pnpm worker
# → http://localhost:8000/docs

# Terminal 3: Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 🧪 Testing

```bash
# Run all tests
pnpm test

# Coverage report
pnpm test:coverage

# E2E tests (Playwright)
pnpm test:e2e

# Worker tests (Pytest)
cd apps/worker
pytest tests/ -v --cov=app
```

---

## 📦 Deployment

### Web (Vercel)

```bash
# Connect to Vercel
vercel

# Deploy
vercel --prod
```

### Worker (Railway / Render)

```bash
# Railway
railway up

# Or Render (via dashboard)
# Connect GitHub repo → auto-deploy
```

---

## 🎯 Project Phases

### ✅ Fase 0 - Setup (CURRENT)
- [x] Monorepo structure
- [x] Database schema
- [x] Basic configurations
- [ ] CI/CD pipeline

### 📍 Fase 1 - Data Ingestion
- [ ] API-Football integration
- [ ] Rate limiting & caching
- [ ] Circuit breaker
- [ ] Fixtures sync jobs

### 🔮 Fase 2 - ML Models
- [ ] Feature engineering
- [ ] Model training
- [ ] Calibration system
- [ ] Predictions pipeline

### 🌌 Fase 3 - Galaxy UI
- [ ] PixiJS canvas
- [ ] Node rendering
- [ ] Interactions
- [ ] Match drawer

### 🎨 Fase 4 - Polish
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Analytics
- [ ] Error handling

### 🚀 Fase 5 - Launch
- [ ] User authentication
- [ ] Watchlist feature
- [ ] Documentation
- [ ] Production deployment

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5.3
- **Styling:** Tailwind CSS + shadcn/ui
- **Canvas:** PixiJS 8
- **State:** React Server Components + Zustand
- **Testing:** Vitest + Playwright

### Backend
- **API:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15 (Supabase)
- **Cache:** Redis 7
- **ML:** XGBoost, LightGBM, scikit-learn
- **Testing:** Pytest + httpx

### Infrastructure
- **Hosting:** Vercel (web) + Railway (worker)
- **Monitoring:** Sentry + Prometheus
- **CI/CD:** GitHub Actions
- **Cache:** Redis Cloud

---

## 📊 Key Metrics

- **Prediction Accuracy:** Target 60%+ (vs 52% market baseline)
- **Calibration Error:** < 0.10 (Expected Calibration Error)
- **API Response Time:** p95 < 500ms
- **Test Coverage:** 70%+ worker, 60%+ web

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pnpm test`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Team

- **Lead Developer:** [Your Name]
- **ML Engineer:** [ML Lead]
- **Designer:** [Designer]

---

## 📞 Support

- **Documentation:** [docs.parlaygalaxy.com]
- **Issues:** [GitHub Issues](https://github.com/your-org/parlaygalaxy/issues)
- **Email:** support@parlaygalaxy.com

---

**Built with ❤️ and ☕ by the ParlayGalaxy Team**

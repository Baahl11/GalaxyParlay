# GalaxyParlay — Plan Maestro

**Última actualización:** 22 Abril 2026  
**Estado:** Producción activa ✅

---

## 1. RESUMEN DEL PROYECTO

Plataforma de analítica deportiva educativa **(18+)**. Muestra el calendario semanal de partidos como una **vista tipo galaxia** (zoom/pan) con probabilidades ML por mercados de apuestas. Sin integración con sportsbooks, sin afiliación, sin payouts.

**Principios:**

- Calendario primero (semana como eje)
- Transparencia: nada es "seguro"
- Data Quality Gate (grades A/B/C/D)
- Compliance: app educativa 18+

---

## 2. STACK & INFRAESTRUCTURA

| Capa          | Tecnología                                      | URL / Ubicación                                |
| ------------- | ----------------------------------------------- | ---------------------------------------------- |
| Frontend      | Next.js 14 + React 18.2 + TypeScript + Tailwind | https://galaxyparlay.vercel.app                |
| Backend       | FastAPI Python 3.11 + APScheduler               | https://galaxyparlay-production.up.railway.app |
| Base de datos | Supabase PostgreSQL 17                          | pqswprhhgpsvhvhsxscw.supabase.co               |
| ML stack      | XGBoost + Dixon-Coles + Contextual Elo + xG     | `apps/worker/app/ml/`                          |
| Data source   | API-Football Pro (7,500 req/día, season 2025)   | `APIFOOTBALL_API_KEY` en .env                  |
| Monorepo      | Turborepo + pnpm workspaces                     | raíz del proyecto                              |

### Estructura de carpetas clave

```
apps/
  web/                     # Next.js frontend
    app/page.tsx            # Página principal con tabs
    components/             # GalaxyCanvas, MatchDrawer, ValueBetList, ModelAccuracy, etc.
    lib/api.ts              # Todas las llamadas a Supabase
  worker/                  # FastAPI backend
    app/
      main.py               # Entry point
      config.py             # Settings + env vars
      routes/jobs.py        # Todos los job endpoints
      scheduler_v2.py       # APScheduler (3 jobs automáticos)
      ml/                   # Modelos predictivos
        dixon_coles.py      # Dixon-Coles Bivariate Poisson
        elo.py              # Contextual Elo ratings
        multi_market_predictor.py  # 35 mercados
        league_config.py    # Home advantage por liga
        smart_parlay.py     # Parlay correlation validator
      services/
        fifa_scraper.py     # FIFA ratings integration
supabase/
  migrations/              # Migraciones SQL
  seed.sql                 # Datos iniciales
```

### Variables de entorno

**`apps/worker/.env`**

```
SUPABASE_URL=https://pqswprhhgpsvhvhsxscw.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<ver Railway env vars>
APIFOOTBALL_API_KEY=<ver Railway env vars>
API_RATE_LIMIT=0.08
API_BURST_CAPACITY=20
```

**`apps/web/.env.local`**

```
NEXT_PUBLIC_SUPABASE_URL=https://pqswprhhgpsvhvhsxscw.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<ver Vercel env vars>
NEXT_PUBLIC_API_URL=https://galaxyparlay-production.up.railway.app
```

---

## 3. ✅ LO QUE ESTÁ IMPLEMENTADO

### Fase 0 — Fundación

- [x] Monorepo Turborepo (pnpm workspaces)
- [x] Next.js 14 + FastAPI bootstrapped
- [x] Supabase schema: `leagues`, `fixtures`, `model_predictions`, `odds_snapshots`, `watchlists`
- [x] RLS (Row Level Security) configurado

### Fase 1 — Frontend visual

- [x] `GalaxyCanvas` — vista tipo galaxia con nodos por partido
- [x] `NetworkGraphView` — grafo de relaciones entre equipos
- [x] `LeagueClusterView` — clusters por liga
- [x] `MatchDrawer` — panel lateral con detalle de predicciones
- [x] `CategoryFilter` — filtro por tipo de mercado
- [x] `GradeFilter` — filtro Grade A/B/C/D
- [x] `LeagueFilter` — filtro por liga (PL, La Liga, Bundesliga, Serie A, Ligue 1, UCL, UEL)
- [x] 7 tabs: Network Graph, Liga Clusters, Galaxy View, List View, Value Bets, Player Props, Accuracy

### Fase 2 — Investigación científica

- [x] Base científica para 35 mercados documentada
- [x] Referencias: Dixon & Coles 1997, Karlis & Ntzoufras 2003
- [x] Benchmark de accuracy esperado por mercado
- [x] Matriz de correlación entre mercados

#### Expansion de mercados (investigacion academica)

- Mercados objetivo: corners, cards, fouls, 1st half totals, BTTS, tackles, player score/assist, offsides
- Corners: compound Poisson regression para conteos y clustering de corners; base para O/U y team corners. Fuente: https://arxiv.org/abs/2112.13001
- Cards + fouls: referee bias y home advantage afectan fouls y tarjetas. Fuente: https://paperity.org/p/280768679/home-advantage-mediated-ham-by-referee-bias-and-team-performance-during-covid
- BTTS / score correlation: bivariate Poisson permite dependencia entre goles y mejora draws. Fuente: https://www.readkong.com/page/analysis-of-sports-data-by-using-bivariate-poisson-models-4354801
- 1st half markets: xG usa tiempo de tiro y contexto; partir por halves para HT totals. Fuente: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0282295
- Player score/assist: xG supera estadisticas tradicionales y soporta features de jugador; base para player props. Fuente: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0282295
- Tackles + offsides: modelar como count data (Poisson/NegBin, overdispersion). Fuente: https://www.cambridge.org/core/books/regression-analysis-of-count-data/2AB83B406C5798030F7C91ECC99B1BE4
- Goals/1X2 baseline: Poisson regression para scores y market inefficiencies. Fuente: https://research-information.bris.ac.uk/en/publications/modelling-association-football-scores-and-inefficiencies-in-the-f/

### Fase 3 — Mejoras del modelo (7/7 implementadas)

| Mejora                                    | Impacto esperado      | Estado |
| ----------------------------------------- | --------------------- | ------ |
| Negative Binomial para Corners            | +5-8%                 | ✅     |
| Base de datos de árbitros                 | +7-10% en cards       | ✅     |
| Features avanzadas de offsides            | +5-8%                 | ✅     |
| Bivariate Poisson (Dixon-Coles) para BTTS | +4-6%                 | ✅     |
| Contextual Elo (home/away/H2H/form)       | +3-5% en match_winner | ✅     |
| Integración xG real desde API-Football    | +5-7% global          | ✅     |
| Backtesting framework                     | validación            | ✅     |

### Fase 4 — Backtesting & Validación

- [x] **1,000 fixtures backtestados**, 16,506 predicciones, 9 mercados
- [x] Accuracy global: **72.18%** | Brier score: 0.1862
- [x] Accuracy por liga: La Liga 74.81% (mejor) / UCL 63.89% (peor)
- [x] Grade A predictions: 79.90% accuracy (Over/Under 1.5)
- [x] Archivo: `apps/worker/backtest_results.json`

### Fase 5 — Features avanzados

- [x] **League-specific home advantage calibration** (`league_config.py`)
  - UCL: 63.89% → target 68-70% (+5-7%)
  - Bundesliga: 68.50% → target 71-73%
- [x] **Smart Parlay Validator** (`smart_parlay.py`)
  - Correlación > 0.70 → REJECT
  - Correlación 0.30-0.70 → WARN + 5% penalty
  - Correlación < 0.30 → APPROVE
- [x] Endpoints: `POST /parlay/validate`, `GET /parlay/recommend/{id}`, `GET /market-confidence`
- [x] Market confidence badges en frontend

### FIFA Integration

- [x] 100+ equipos con 16 stats cada uno
- [x] Integrado en `dixon_coles.py` (match_winner: quality gap + star player adjustment)
- [x] Integrado en `multi_market_predictor.py` (corners: pace/skill, cards: physical mismatch, shots, offsides)
- [x] LRU cache para lookups instantáneos
- ⚠️ Datos son estimados/mock — no API oficial de SoFIFA

### Producción & Mejoras recientes (Abril 2026)

- [x] Sync window: 7 → **14 días** (más fixtures cargados)
- [x] **EV real**: `getValueBets` usa odds reales de `odds_snapshots` (no sintéticas)
  - Edge mínimo: 3% | EV mínimo: 2%
  - Kelly fraction calculado con odds reales de Bet365
- [x] **Job sync_results** cada 3h (actualiza FT fixtures automáticamente)
- [x] **Tab Accuracy** con `ModelAccuracy.tsx` — backtesting visual (accuracy, Brier, por mercado)
- [x] Rate limit API-Football: 0.08 req/s, burst capacity: 20 (Pro plan)
- [x] 133 fixtures reales season 2025 | 4,655 predicciones | 4,483 odds snapshots
- [x] 22 ligas activas (Europa + LATAM + Asia + Oceanía + Copa Europa)

### APScheduler (3 jobs automáticos)

| Job                  | Frecuencia                  | Función                              |
| -------------------- | --------------------------- | ------------------------------------ |
| load_fixtures        | Cada 12h (cron 6AM/6PM UTC) | Sync fixtures desde API-Football     |
| generate_predictions | Cada 6h                     | Genera predicciones para fixtures NS |
| sync_results         | Cada 3h                     | Actualiza scores FT de últimas 36h   |

### Seguridad

- [x] Tokens hardcodeados removidos de todos los scripts Python/PS
- [x] Variables de entorno en Railway + Vercel
- [x] `.gitignore` protegiendo `.env` y `.env.local`
- [x] RLS activado en Supabase para watchlists

---

## 4. ❌ LO QUE FALTA (priorizado)

### 🔴 Crítico

1. **Git history cleanup** — JWT del proyecto antiguo `REMOVED_JWT` (no activo) sigue en git history. Usar BFG Repo Cleaner o `git filter-repo` para reescribir historia.
2. **Player Props con datos reales** — El tab "Player Props" existe en frontend pero no tiene datos reales. API-Football Pro incluye player stats; falta implementar el endpoint y componente.

### 🟡 Importante

3. **Dixon-Coles extendido a Over/Under** — Actualmente O/U usa Poisson independiente. Extender la correlación bivariate a Over/Under daría +2-4% accuracy. (ver `ANALISIS_PROFUNDO` archivado)
4. **BTTS en backtest** — El mercado BTTS no está incluido en el backtest de 1,000 fixtures. Bivariate Poisson mejora BTTS significativamente pero no está validado.
5. **Más fixtures** — 133 fixtures es poco para ligas LATAM. Ampliar: Liga MX (262), Brasileirão (71), Libertadores (13), Sudamericana (11).

### 🟢 Mejoras futuras

6. **Autenticación de usuarios** — Supabase Auth + watchlist flow completo en frontend (schema ya tiene RLS listo)
7. **Paginación** — Frontend carga todos los fixtures en memoria. Con más ligas necesita infinite scroll o paginación server-side
8. **Live scores** — APScheduler job para fixtures LIVE (no solo FT)
9. **Tests automatizados** — Cero tests end-to-end o unitarios actualmente
10. **FIFA datos reales** — Reemplazar datos mock con API oficial de SoFIFA o FutDB para ratings actualizados

---

## 5. PRÓXIMOS PASOS (en orden de prioridad)

```
[ ] 1. Ampliar fixtures LATAM (Liga MX, Brasileirão, Libertadores, Sudamericana)
        → apps/worker/app/routes/jobs.py: agregar league_ids al sync
        → apps/web/components/LeagueFilter.tsx: agregar LATAM pills

[ ] 2. Dixon-Coles extendido a Over/Under
        → apps/worker/app/ml/multi_market_predictor.py
        → Cambiar P(O/U) de Poisson independiente a Bivariate con rho=-0.15
        → Esperar +2-4% accuracy en 6 mercados O/U

[ ] 3. Backtest BTTS con Bivariate Poisson
        → apps/worker/run_validation_backtest.py (agregar mercado BTTS)
        → Regenerar backtest_results.json con BTTS incluido

[ ] 4. Player Props con datos reales
        → apps/worker/app/routes/ : nuevo endpoint /player-props/{fixture_id}
        → apps/web/components/PlayerPropsSection.tsx: conectar a datos reales
        → API-Football endpoint: /players?fixture={id}

[ ] 5. Autenticación de usuarios (Supabase Auth)
        → apps/web/app/auth/: páginas login/signup
        → apps/web/lib/supabase.ts: client-side auth
        → Conectar watchlist a usuario autenticado

[ ] 6. Git history cleanup
        → Instalar: npm install -g bfg-repo-cleaner o pip install git-filter-repo
        → Identificar commits con credenciales antiguas
        → PRECAUCIÓN: operación destructiva — hacer backup primero
```

---

## 6. TODO MAESTRO (E2E)

### P0 — Datos y modelos (mercados core)

- [ ] Priorizar mercados y alcance v1: corners, cards, fouls, BTTS, 1st half totals, offsides, tackles, player score/assist
- [ ] Inventario de fuentes y campos por mercado (API-Football endpoints, referee data, player stats)
- [ ] Expandir fixtures LATAM y ligas faltantes (Liga MX, Brasileirao, Libertadores, Sudamericana)
- [ ] Completar coverage de odds_snapshots para nuevos mercados
- [ ] Features comunes: form, pace, home/away, referee bias, schedule congestion
- [ ] Corners: compound Poisson / NegBin con clustering temporal
- [ ] Cards + fouls: count regression + referee effects + rivalry intensity
- [ ] BTTS: bivariate Poisson con correlacion y ajuste de draws
- [ ] 1st half totals: split HT/FT, features de early tempo y xG por minutos
- [ ] Offsides + tackles: count regression con overdispersion
- [ ] Player score/assist: xG por jugador + minutos proyectados + role/position
- [ ] Calibracion de probas (Platt/Isotonic) y mapping a grades A/B/C/D
- [ ] Backtest por mercado con Brier, log loss, calibration, ROI y EV

### P1 — Backend y pipeline

- [ ] Extender generate_predictions para nuevos mercados en `multi_market_predictor.py`
- [ ] Endpoint `/player-props/{fixture_id}` con datos reales
- [ ] Endpoint `/market-confidence` por mercado y liga
- [ ] Job de sync de player stats y referee stats
- [ ] Tabla/registro de versiones de modelo y features usados
- [ ] Cache y rate limits por endpoint

### P1 — Frontend

- [ ] UI de filtros por mercado y halves
- [ ] UI de player props con desglose de probas y minutos
- [ ] Mostrar cobertura de mercados por fixture
- [ ] Mejorar list view para 60/120 picks con paginacion o virtual list

### P2 — Calidad, observabilidad, compliance

- [ ] Quality gate por mercado (min samples, odds coverage, drift)
- [ ] Alertas para jobs fallidos y drops de data
- [ ] Tests unitarios y smoke tests E2E
- [ ] Git history cleanup por tokens antiguos

### P2 — Documentacion y release

- [ ] Actualizar FASE_5_IMPLEMENTATION_SUMMARY y FASE_5_QUICK_REFERENCE
- [ ] Anadir runbook de jobs y recovery
- [ ] Checklist de deploy + rollback

### Plan operativo (listo para ejecutar)

Orden v1 de mercados (prioridad):

1. Corners
2. Cards + fouls
3. BTTS
4. 1st half totals
5. Offsides
6. Tackles
7. Player score
8. Player assist

Estimacion: S = 1-2 dias, M = 3-5 dias, L = 1-2 semanas

Definition of done (DoD) por ticket:

- Modelo entrenado + calibrado
- Backtest con Brier/log loss + ROI/EV
- Endpoint y UI conectados
- Documentacion minima actualizada

| ID  | Ticket                          | Entregable                         | Est | Dep         |
| --- | ------------------------------- | ---------------------------------- | --- | ----------- |
| T01 | Alcance v1 + KPIs               | Spec v1 + KPIs por mercado         | S   | -           |
| T02 | Inventario data + gaps          | Data map + faltantes               | S   | T01         |
| T03 | Expandir fixtures LATAM         | Ligas LATAM activas + UI filtro    | M   | T02         |
| T04 | Coverage odds_snapshots         | Odds para nuevos markets           | M   | T02         |
| T05 | Feature set comun               | Features base + pipeline           | M   | T02         |
| T06 | Job sync referee + player stats | Jobs + tablas actualizadas         | M   | T02         |
| T07 | Modelo corners                  | Prob corners + O/U + team corners  | M   | T05,T04     |
| T08 | Modelo cards + fouls            | Prob cards/fouls + referee effects | M   | T05,T06,T04 |
| T09 | Modelo BTTS                     | Bivariate Poisson calibrado        | M   | T05         |
| T10 | Modelo 1st half totals          | HT O/U + split tempo               | M   | T05         |
| T11 | Modelo offsides                 | Count regression + overdispersion  | M   | T05         |
| T12 | Modelo tackles                  | Count regression + overdispersion  | M   | T05         |
| T13 | Player score/assist             | xG jugador + minutos proyectados   | L   | T06,T05     |
| T14 | Calibracion + grades            | Platt/Isotonic + mapping A/B/C/D   | S   | T07-T13     |
| T15 | Backtest por mercado            | Reportes por mercado               | M   | T07-T14     |
| T16 | Endpoints markets               | /market-confidence + /player-props | M   | T07-T15     |
| T17 | UI filtros markets/halves       | Filtros + coverage por fixture     | M   | T16         |
| T18 | UI player props                 | Player props list + detalle        | M   | T16         |
| T19 | Paginacion/virtual list         | List view escalable                | S   | T17         |
| T20 | Quality gate + alertas          | Reglas + alerting jobs             | M   | T15         |
| T21 | Docs + runbook                  | Runbook jobs + recovery            | S   | T20         |
| T22 | Release checklist               | Checklist deploy/rollback          | S   | T21         |
| T23 | Git history cleanup             | Historia limpia de secretos        | M   | -           |

---

## 7. QUICK REFERENCE

### URLs de producción

```
Frontend:  https://galaxyparlay.vercel.app
Backend:   https://galaxyparlay-production.up.railway.app
Supabase:  https://pqswprhhgpsvhvhsxscw.supabase.co
```

### Comandos frecuentes

```powershell
# Instalar dependencias
cd c:\Users\gm_me\GalaxyParlay
pnpm install

# Desarrollo local frontend
cd apps/web && pnpm dev

# Desarrollo local backend
cd apps/worker
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Supabase CLI
Set-Alias -Name supabase -Value "$env:USERPROFILE\supabase-cli\supabase.exe"
supabase db push                          # aplicar migraciones
supabase db diff --schema public          # ver cambios pendientes

# Deploy
git add -A
git commit -m "feat: descripción"
git push origin main                      # Railway auto-redeploy (~3min)
vercel --prod --yes                       # Vercel frontend deploy

# Ejecutar script Python manual
cd apps/worker
.\venv\Scripts\python.exe nombre_script.py

# Python venv: activar en PowerShell
.\venv\Scripts\Activate.ps1
```

### Endpoints backend principales

```
GET  /health                                       Healthcheck
GET  /api/fixtures?status=NS&limit=100             Fixtures próximos
GET  /api/fixtures/{id}                            Fixture por ID
GET  /jobs/scheduler-status                        Estado APScheduler
POST /jobs/sync-fixtures                           Sync manual desde API-Football
POST /jobs/run-predictions                         Genera predicciones
POST /jobs/sync-results                            Actualiza resultados FT
GET  /jobs/backtest-results                        Stats de backtesting
POST /parlay/validate                              Valida parlay (correlación)
GET  /parlay/recommend/{fixture_id}               Recomendaciones low-correlation
GET  /market-confidence                            Badges de confianza por mercado
```

### Tablas Supabase clave

```sql
leagues             -- ligas activas (league_id, name, country, season)
fixtures            -- partidos (id, league_id, kickoff_time, status, teams, scores)
model_predictions   -- predicciones ML (fixture_id, market_key, home_win, draw, away_win, grade, confidence)
odds_snapshots      -- odds de bookmakers (fixture_id, market_key, odds_data jsonb)
watchlists          -- favoritos por usuario (user_id, fixture_id)
```

### Formato de odds en DB

```json
// match_winner:
{"home": 2.25, "draw": 3.8, "away": 2.88}

// over_under_2.5:
{"over 2.5": 1.4, "under 2.5": 3.0}

// Nota: market_key en predictions usa underscore (over_under_2_5)
//       market_key en odds_snapshots usa punto    (over_under_2.5)
```

### IDs de ligas (API-Football)

```
39  = Premier League        140 = La Liga
78  = Bundesliga            135 = Serie A
61  = Ligue 1               88  = Eredivisie
2   = UEFA Champions League  3  = UEFA Europa League
848 = Conference League
262 = Liga MX               71  = Brasileirão
13  = Libertadores          11  = Sudamericana
128 = Argentina Primera
253 = MLS
```

---

## 7. MODELO ML — RESUMEN TÉCNICO

### Arquitectura del modelo

```
Input features (por fixture):
  - Elo ratings: home_elo, away_elo, h2h_elo, recent_form
  - xG histórico: últimos 5 partidos home/away
  - FIFA ratings: overall, attack, defense, pace, physical
  - Liga config: home_advantage, calibration_factor
  - Árbitro: card_rate_home, card_rate_away (para cards markets)

Modelos:
  - XGBoost → match_winner, BTTS
  - Dixon-Coles Bivariate Poisson → Over/Under goals, BTTS
  - Negative Binomial → Corners markets
  - Gradient Boosting → Cards markets
  - Ensemble (80% modelo / 20% histórico base)

Calibración:
  - Platt Scaling implementado
  - Blend weights: 80/20 (modelo vs histórico)
  - Dixon-Coles rho: -0.15 (empirico)
  - Contextual Elo K-factor: 32
```

### 35 Mercados activos

```
Goals (6):      over_under_0_5 → over_under_5_5
Corners (6):    corners_over_under_7_5 → corners_over_under_12_5
Cards (5):      cards_over_under_2_5 → cards_over_under_6_5
Shots (5):      shots_on_target_over_under_6_5 → shots_on_target_over_under_10_5
Offsides (4):   offsides_over_under_3_5 → offsides_over_under_6_5
Team Goals (6): home/away_team_over_under_0_5 → 2_5
Core (3):       match_winner, both_teams_score, first_half_over_under_0_5
```

---

## 8. SEGURIDAD

### Estado actual

- ✅ Tokens hardcodeados removidos del código fuente (Feb 2026)
- ✅ Railway env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `APIFOOTBALL_API_KEY`
- ✅ Vercel env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- ✅ `.gitignore` protege `.env`, `.env.local`, `.env.vercel`
- ⚠️ JWT del proyecto **antiguo** (`REMOVED_JWT`) sigue en git history — ese proyecto ya no es el activo pero debería limpiarse
- ✅ Proyecto activo: `pqswprhhgpsvhvhsxscw` — keys solo en env vars

### Si necesitas rotar keys del proyecto activo

1. Supabase Dashboard → Settings → API → Regenerate keys
2. Actualizar Railway env vars: `railway variables set KEY=nuevo_valor`
3. Actualizar Vercel env vars: Dashboard → Settings → Environment Variables
4. Re-deploy ambos servicios

---

## 9. ARQUITECTURA DE DATOS

```
API-Football Pro (7,500 req/día)
         │
         ▼
[APScheduler Jobs - Railway]
  ├── load_fixtures (12h)  ──────► fixtures table (Supabase)
  ├── generate_predictions (6h) ──► model_predictions table
  └── sync_results (3h) ─────────► fixtures.status / scores update
                                         │
                              ┌──────────┴──────────┐
                              ▼                      ▼
                    [Next.js Frontend]        [odds_snapshots]
                    lib/api.ts                (Bet365 odds reales)
                         │                          │
                         └──────── getValueBets ────┘
                                  (EV real calculado)
```

---

_Documento mantenido en: `PLAN_MAESTRO.md` en la raíz del proyecto._  
_Para historial completo de implementación ver commits de git desde Enero 2026._

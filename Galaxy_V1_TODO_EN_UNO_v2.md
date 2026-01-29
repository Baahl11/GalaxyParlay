# GALAXY V1 — Plan Maestro “TODO EN UNO” (PRD + Fases + Checklists + Prompts IA)
**Proyecto:** Galaxy Calendar Football Probabilities  
**Stack objetivo:** Next.js (Vercel) + Supabase (Postgres/Auth/Storage) + Worker (FastAPI) + (Opcional) Upstash Redis  
**Modo producto:** Analítica deportiva educativa **18+**. Sin integración con casas de apuestas, sin afiliación.

> Este documento está diseñado para que puedas dárselo a una **IA Coder** y que construya el proyecto **por fases** sin omitir nada: incluye PRD, arquitectura, esquema DB, backlog por fases, definition-of-done, y prompts por fase.

---

## 0) Estado actual y cómo usar esto
Ya existe un **starter runnable (Fase 0)** que corre en VS Code:
- `galaxy-v1-starter.zip` (repo con `apps/web`, `apps/worker`, `supabase/schema.sql`, `supabase/rls.sql`)
- Sirve para iniciar local, luego reemplazar los stubs por la implementación real.

**Regla de oro:** cada fase agrega lo necesario. Al final de cada fase hay un checklist “¿Ya quedó completo?” y “¿Qué falta para la siguiente?”.

---

---

# 0.1) Arquitectura del Starter (Fase 0) — repo runnable en VS Code
Este documento asume que partes del **starter runnable** (Fase 0).  
El starter ya trae la base de monorepo y los stubs para que puedas correr web + worker en local y luego completar Fase 1–6.

## Estructura de carpetas (starter)
```text
galaxy-v1-starter/
├─ apps/
│  ├─ web/                 # Next.js (Vercel)
│  │  ├─ app/
│  │  │  ├─ api/health/route.ts
│  │  │  ├─ layout.tsx
│  │  │  ├─ page.tsx       # Lista dummy semanal (placeholder Galaxy)
│  │  │  └─ globals.css
│  │  ├─ lib/
│  │  │  ├─ dummy.ts       # Fixtures dummy
│  │  │  └─ supabase.ts    # Cliente Supabase anon (placeholder)
│  │  ├─ .env.example
│  │  ├─ package.json
│  │  └─ next.config.mjs
│  ├─ worker/              # FastAPI (jobs + ingesta + scoring)
│  │  ├─ app/
│  │  │  ├─ main.py        # /health + /internal/ping (header secret)
│  │  │  ├─ config.py      # dotenv + settings
│  │  │  ├─ api_sports.py  # wrapper httpx (API-Football)
│  │  │  ├─ supabase_client.py
│  │  │  └─ jobs/
│  │  │     └─ sync_fixtures.py  # stub (se completa en Fase 1)
│  │  ├─ requirements.txt
│  │  ├─ .env.example
│  │  └─ package.json
├─ packages/
│  └─ shared/
│     ├─ index.ts          # tipos compartidos (Fixture, QualityGrade, etc.)
│     └─ package.json
├─ supabase/
│  ├─ schema.sql           # tablas mínimas V1
│  └─ rls.sql              # RLS para watchlists
├─ package.json            # workspaces + scripts dev
└─ README.md               # pasos de instalación/corrida
```

## Qué corre en local (starter)
- **Web:** Next.js en `http://localhost:3000`
  - Ruta health: `GET /api/health`
  - Home: muestra fixtures dummy (placeholder Galaxy)
- **Worker:** FastAPI en `http://localhost:8000`
  - Health: `GET /health`
  - Endpoint interno (protegido por header): `POST /internal/ping`
    - Header requerido: `x-worker-secret: <WORKER_SECRET>`

## Variables de entorno del starter
### Web (`apps/web/.env.local`)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- (opcional server-only) `SUPABASE_SERVICE_ROLE_KEY` *(NO exponer al cliente)*

### Worker (`apps/worker/.env`)
- `APIFOOTBALL_BASE_URL` (default `https://v3.football.api-sports.io`)
- `APIFOOTBALL_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `WORKER_SECRET` (por defecto `dev-secret-change-me`)

## DB (Supabase) en starter
El starter incluye SQL mínimo:
- `supabase/schema.sql`: crea tablas clave (`leagues`, `fixtures`, `markets_catalog`, `market_availability`, `model_predictions`, `watchlists`, etc.)
- `supabase/rls.sql`: activa RLS para watchlists y deja fixtures/predicciones en lectura pública (puedes endurecer después)

## Scripts de ejecución (starter)
Desde la raíz:
```bash
npm install
npm run dev
```
Worker (Python venv) en `apps/worker`:
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Importante: el starter **no** implementa fixtures reales todavía (eso es **Fase 1**).  
> La UI en `apps/web/app/page.tsx` es solo placeholder para validar el pipeline y luego reemplazarla con la Galaxy real (Fase 4).

## 1) Resumen ejecutivo (PRD V1)
La app muestra **el calendario semanal** de partidos como una vista tipo **galaxia/blackboard** (zoom/pan).  
Cada partido (nodo) abre un panel con **probabilidades (%)** por mercados (team + player solo cuando la data sea confiable).  
Si un mercado o liga tiene data débil, se muestra **difuminado** con warning (Data Quality Gate A/B/C).  
Retención anti-churn: **watchlist + tracking (“paper”)** de predicciones y resultados, con un dashboard sencillo.

---

## 2) Principios del producto
1) **Calendario primero** (semana como eje).  
2) **Exploración** por vista visual + filtros.  
3) **Transparencia** (nada “seguro”).  
4) **Gating por calidad** (A/B/C).  
5) **Rendimiento** (galaxia rápida + fallback lista).  
6) **Compliance**: app educativa 18+, sin apostar, sin payouts, sin links.

---

## 3) Usuarios
### Novato
- Señales visuales, explicaciones cortas.
- Prefiere presets (ligas/mercados favoritos) y watchlist.

### Avanzado
- Quiere granularidad por mercados, ligas y player-props cuando haya data.
- Quiere tracking y métricas simples (calibración/brier/logloss).

---

## 4) Alcance V1
### Incluye
- Galaxy semanal (nodos por partido) + filtros + minimapa.
- Match Drawer (panel lateral) con mercados y probabilidades.
- Data Quality Gate (A/B/C): markets C difuminados.
- Watchlist.
- Tracking “paper” + resultados post-match + dashboard semanal.

### No incluye (V1)
- Integración con sportsbooks / payouts / afiliados.
- Live completo (solo infra “live-ready”).
- Props ultra raros si no hay coverage estable.

---

## 5) Competiciones V1 (Top 10)
1) Premier League  
2) UEFA Champions League  
3) LaLiga  
4) Serie A  
5) Bundesliga  
6) Ligue 1  
7) Liga MX  
8) Brasileirão Serie A  
9) CONMEBOL Libertadores  
10) MLS  

Expansión posterior según coverage: Portugal, Eredivisie, Argentina, Championship, Sudamericana, etc.

---

## 6) Mercados V1 (selección)
> Regla: **solo** habilitar si pasa Data Quality Gate.

### Team (core)
- 1X2, Doble oportunidad, DNB  
- Over/Under goles (0.5–3.5)  
- BTTS  
- Team totals (si existe)  
- Handicap (si existe)

### Corners / Cards (si feed consistente)
- Corners totales y por equipo O/U  
- Cards totales y por equipo O/U  

### Player-centric (condicional)
- Goleador (sí/no)  
- Tarjeta (sí/no)  
- Shots/SOT (solo si coverage sólido)

---

## 7) Requisitos no funcionales

### Performance
- **First load:** < 2.5s en móvil medio (4G)
- **Time to Interactive (TTI):** < 3.5s
- **Galaxy rendering:** 60 FPS desktop; 30 FPS móvil + fallback lista
- **API response time:** p95 < 500ms para `/api/galaxy`
- **Bundle size:** < 200KB (gzipped) initial JS

### Resiliencia
- **Fallos upstream:** UI degradada sin romper (skeleton loaders)
- **Rate limit hit:** Queue requests + retry exponencial
- **DB timeout:** Fallback a cache stale (max 1h)
- **Circuit breaker:** Auto-recovery tras 5 min

### Seguridad
- **API keys:** Solo server-side (service role)
- **RLS activo:** Todas las tablas user-facing
- **CORS:** Whitelist de dominios
- **Headers:** CSP, HSTS, X-Frame-Options
- **Secrets rotation:** Cada 90 días (automated)

### Observabilidad (NUEVO)
- **Logging:** Estructurado JSON (Pino/structlog)
- **APM:** Sentry (web) + Prometheus (worker)
- **Métricas clave:**
  - Request rate/latency (p50, p95, p99)
  - Error rate por endpoint
  - Job success/failure rate
  - API quota usage
  - Model prediction latency
  - Data quality scores por liga
- **Alerting:** Slack/Discord webhooks
  - API quota > 90% → warning
  - Job failure 3x consecutivo → critical
  - Error rate > 5% → warning
  - DB connections > 80% → warning
- **Dashboards:** Grafana para worker, Vercel Analytics para web

### Testing (NUEVO)
- **Coverage mínimo:** 70% worker, 60% web
- **Test types:**
  - Unit tests (fast, isolados)
  - Integration tests (DB + APIs)
  - E2E tests (flujos críticos)
- **CI/CD:** GitHub Actions
  - Lint + Type check
  - Tests paralelos
  - Build validation
  - Auto-deploy staging

---

## 8) Arquitectura (alto nivel)
**Servicios**
- Web: Next.js (Vercel)  
- DB/Auth/Storage: Supabase  
- Worker: FastAPI (jobs + ingesta + scoring)  
- Cache opcional: Redis (Upstash)

**Flujo**
API-Football → Worker ingest (snapshots) → DB → Worker scoring → DB predictions → Web consume (read-heavy)

---

## 9) Data Layer (API-Football) — estrategia operativa
> Pre-match ahora; LIVE después.

### Ventanas por kickoff
- T-7d → T-24h: refresco 6–12h  
- T-24h → T-2h: refresco 1–3h  
- T-90m → kickoff: refresco 5–10m (lineups)  
- LIVE futuro: 1/min SOLO watchlist

### Caching (obligatorio)
- Cache por `league/day` y `fixture`.  
- En DB guarda “snapshots” para auditoría.- **TTL dinámico:** más corto cuando el partido se acerca
- **Invalidación inteligente:** cuando hay lineup confirmado

### Rate Limiting (CRÍTICO)
- **Free tier:** 100 req/day → Circuit breaker a 90 req
- **Pro tier:** 3000 req/day → usar token bucket
- **Retry strategy:** Exponential backoff (2s, 4s, 8s, 16s, 60s max)
- **Circuit breaker:** Abrir tras 3 fallos consecutivos, cerrar tras 5 min
- **Queue prioritization:** Fixtures próximos > fixtures lejanos
---

## 10) Data Quality Gate (A/B/C)
**Score 0–100 por (liga, mercado)**  
- Coverage % (con odds/stats)  
- Sample size N  
- Missingness  
- Drift (últimas semanas)  
- Latencia / consistencia de llegada

**Grades**
- A: 80–100 (visible normal)  
- B: 60–79 (visible con warning)  
- C: <60 (difuminado/disabled + toggle “experimental”)

---

## 11) Modelado (V1) — robusto y calibrado
**Objetivo V1:** probabilidades calibradas y estables.

### Modelos Base
- **Goles:** Poisson / Dixon-Coles (baseline) + XGBoost (ensemble)
- **Corners/Cards:** Negative Binomial (mejor para overdispersion)
- **Player props:** Solo con coverage A + modelo de minutos esperados
- **Sistema Elo:** Rating adaptado para fútbol (componentes ataque/defensa)

### Ensemble Strategy (Aumenta precisión 8-12%)
```
┌─────────────────────────────────────────┐
│  Modelos Base (5)                       │
├─────────────────────────────────────────┤
│  1. Dixon-Coles (teórico)               │
│  2. XGBoost (no-linealidades)           │
│  3. LightGBM (velocidad)                │
│  4. Random Forest (diversidad)          │
│  5. Elo adaptado (rating-based)         │
└─────────────┬───────────────────────────┘
              │
              ▼
      ┌───────────────┐
      │ Meta-Learner  │ (Stacking)
      │ (GradientBoost)│
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │  Calibración  │ (por liga/mercado)
      └───────┬───────┘
              │
              ▼
    Final Predictions
```

### Feature Engineering (170+ features)

#### Categorías de Features
1. **Contextuales (40):** Forma reciente, H2H, posición tabla, descanso
2. **Plantilla (25):** Valor mercado, lesiones, experiencia, edad
3. **Estilo de juego (35):** Posesión, pressing, tiros, set pieces
4. **Expected Metrics (20):** xG for/against, xGA, xPTS
5. **Venue-specific (15):** Rendimiento casa/fuera, travel distance
6. **Temporal (10):** Fase temporada, racha, presión competitiva
7. **Market-specific (25):** Por mercado (corners, cards, player props)

**Ejemplo features críticos:**
- `home_xg_for_l10` - xG generado últimos 10
- `away_xga_conceded_l10` - xG concedido últimos 10
- `h2h_btts_pct_l5` - % BTTS en últimos 5 H2H
- `squad_value_ratio` - Ratio valor plantillas
- `key_players_missing_minutes_pct` - % minutos ausentes
- `days_rest_advantage` - Diferencia días descanso
- `home_corners_for_vs_away_corners_against` - Matchup corners

**Calibración (obligatoria)**
- **Método:** Isotonic Regression (monótona, evita overfitting)
- **Granularidad:** Por (liga, mercado, model_version)
- **Mínimo samples:** 30 partidos para calibrar
- **Fallback:** Calibrador global si no hay suficiente data
- **Clipping:** Probabilidades entre [0.01, 0.99] (evitar extremos)

**Métricas**
- **Primarias:** LogLoss (optimización), Brier Score (calibración)
- **Secundarias:** ROC-AUC, Precision@K, F1
- **Calibración:** Reliability diagram (10 bins), ECE (Expected Calibration Error)
- **Validación:** Walk-forward (5 folds, 4 semanas test)
- **Sharpe Ratio:** Para evaluar betting value (simulación paper)

**Gating por performance**
- Si LogLoss > umbral liga → baja a B/C
- Si Brier > 0.30 → warning
- Si calibration error > 0.15 → difuminado
- **Auto-ajuste:** Re-entrenar cada 2 semanas con data nueva

---

## 12) Correlación (sin builder de payouts)
V1: warnings cuando el usuario guarda/selecciona múltiples legs correlacionadas (mismo partido o combinaciones típicas).

- Regla simple: si 2+ legs de mismo fixture → warning “alta correlación”.
- Lista heurística: (Over 2.5 + BTTS), (Corners altos + tiros equipo), etc.
V2: copula/simulación.

---

## 13) UX: Galaxy Calendar
### Home Galaxy
- Semana por defecto  
- Nodos por partido  
- Clusters por día + filtros por liga/mercado/calidad  
- Zoom/pan + minimapa

### Match Drawer
- Header: equipos + hora + liga + estado  
- Mercados agrupados (Team/Corners/Cards/Player)  
- Cada mercado: prob %, badge A/B/C, tooltip “why warning”  
- CTA: Watchlist

### Fallback Lista (móvil)
- Vista lista por día/hora, con mini indicators de calidad.

---

## 14) Anti-churn (recomendación fuerte)
Para evitar churn, **sí** incluye desde V1:
- Watchlist  
- Tracking “paper” (guardas predicción y luego outcome)  
- Dashboard semanal (simple): accuracy + brier/logloss básico + bins

Esto crea hábito (regreso a ver resultados), y confianza.

---

## 15) Áreas de oportunidad (integradas)
A) Coverage Map (por liga: % A/B/C)  
B) Model Card (transparencia del modelo)  
C) Onboarding (3 pantallas máximo)  
D) Personalización (ligas/mercados/jugadores favoritos)  
E) Toggle “Experimental” (mostrar C)  
F) Guardrails lenguaje (sin “seguro/garantizado”)  
G) Performance: Canvas/WebGL + LOD + prefetch  
H) Observabilidad: panel admin jobs + missingness + drift

---

# 16) ÁREAS DE MEJORA TÉCNICA (CRÍTICAS)

## 16.1) Testing Strategy (P0 - CRÍTICO)
### Objetivo
Asegurar calidad de código y reducir bugs en producción con cobertura mínima del 70% (worker) y 60% (web).

### Estructura de Testing

#### Worker (Python)
```python
# tests/
├─ unit/
│  ├─ test_sync_fixtures.py       # Jobs de ingesta
│  ├─ test_scoring.py              # Modelos y scoring
│  ├─ test_calibration.py          # Calibración
│  └─ test_quality_gate.py         # Quality scoring
├─ integration/
│  ├─ test_api_football.py         # Llamadas externas
│  ├─ test_supabase_ops.py         # DB operations
│  └─ test_end_to_end_flow.py      # Flujo completo
└─ fixtures/
   └─ sample_responses.json        # Mock data
```

**Frameworks:**
- `pytest` (unit + integration)
- `pytest-cov` (coverage)
- `pytest-mock` (mocking)
- `freezegun` (time manipulation)
- `responses` (HTTP mocking)

**Ejemplo test crítico:**
```python
import pytest
from app.jobs.sync_fixtures import sync_fixtures_week
from datetime import datetime

@pytest.mark.asyncio
async def test_sync_fixtures_idempotent(mock_supabase, mock_api_football):
    """Verificar que correr 2 veces no duplica fixtures"""
    week = datetime(2026, 1, 20)
    
    # Primera ejecución
    result1 = await sync_fixtures_week(week)
    fixtures_count1 = await mock_supabase.count('fixtures')
    
    # Segunda ejecución (idempotencia)
    result2 = await sync_fixtures_week(week)
    fixtures_count2 = await mock_supabase.count('fixtures')
    
    assert fixtures_count1 == fixtures_count2
    assert result2['duplicates'] == fixtures_count1
```

#### Web (TypeScript/Next.js)
```typescript
// __tests__/
├─ unit/
│  ├─ lib/
│  │  ├─ supabase.test.ts
│  │  └─ galaxy-utils.test.ts
│  └─ components/
│     ├─ MatchDrawer.test.tsx
│     └─ QualityBadge.test.tsx
├─ integration/
│  ├─ api/
│  │  ├─ galaxy.test.ts
│  │  └─ watchlist.test.ts
│  └─ flows/
│     └─ watchlist-flow.test.ts
└─ e2e/
   ├─ galaxy-navigation.spec.ts
   └─ match-details.spec.ts
```

**Frameworks:**
- `Vitest` (unit + integration, más rápido que Jest)
- `React Testing Library` (componentes)
- `Playwright` (E2E)
- `MSW` (Mock Service Worker para APIs)

**Ejemplo test E2E crítico:**
```typescript
import { test, expect } from '@playwright/test';

test('Usuario puede agregar partido a watchlist', async ({ page }) => {
  await page.goto('/galaxy?week=2026-01-20');
  
  // Esperar que Galaxy cargue
  await expect(page.locator('.galaxy-canvas')).toBeVisible();
  
  // Click en nodo de partido
  await page.click('[data-fixture-id="12345"]');
  
  // Drawer debe abrir
  await expect(page.locator('.match-drawer')).toBeVisible();
  
  // Agregar a watchlist
  await page.click('button:has-text("Add to Watchlist")');
  
  // Toast de confirmación
  await expect(page.locator('.toast-success')).toBeVisible();
  
  // Verificar en DB (via API)
  const watchlist = await page.request.get('/api/watchlist');
  const data = await watchlist.json();
  expect(data.fixtures).toContainEqual(
    expect.objectContaining({ fixture_id: 12345 })
  );
});
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  worker-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r apps/worker/requirements.txt
      - run: pytest apps/worker/tests --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          
  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run test:coverage
      - run: npm run test:e2e
```

---

## 16.2) Observabilidad y Monitoreo (P1 - IMPORTANTE)

### Logging Estructurado

#### Worker (Python)
```python
import structlog
from app.config import settings

# Configuración global
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Ejemplo de uso
async def sync_fixtures_week(week: datetime):
    logger.info(
        "sync_fixtures_started",
        week=week.isoformat(),
        leagues=len(target_leagues),
        job_id=job_id
    )
    
    try:
        result = await _fetch_and_upsert(week)
        
        logger.info(
            "sync_fixtures_completed",
            fixtures_inserted=result['inserted'],
            fixtures_updated=result['updated'],
            duration_ms=result['duration'],
            job_id=job_id
        )
        
    except Exception as e:
        logger.error(
            "sync_fixtures_failed",
            error=str(e),
            week=week.isoformat(),
            job_id=job_id,
            exc_info=True
        )
        raise
```

#### Web (Next.js)
```typescript
// lib/logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  ...(process.env.NODE_ENV === 'production'
    ? {}
    : {
        transport: {
          target: 'pino-pretty',
          options: {
            colorize: true,
          },
        },
      }),
});

// Uso en API route
export async function GET(request: Request) {
  const requestId = crypto.randomUUID();
  
  logger.info({
    msg: 'galaxy_request_started',
    requestId,
    url: request.url,
    method: request.method,
  });
  
  try {
    const data = await fetchGalaxyData();
    
    logger.info({
      msg: 'galaxy_request_completed',
      requestId,
      fixtures_count: data.length,
      duration_ms: performance.now() - startTime,
    });
    
    return Response.json(data);
  } catch (error) {
    logger.error({
      msg: 'galaxy_request_failed',
      requestId,
      error: error.message,
      stack: error.stack,
    });
    throw error;
  }
}
```

### Métricas y APM

#### Worker Metrics (Prometheus + Grafana)
```python
from prometheus_client import Counter, Histogram, Gauge

# Definir métricas
api_requests_total = Counter(
    'api_football_requests_total',
    'Total API-Football requests',
    ['endpoint', 'status']
)

job_duration = Histogram(
    'job_duration_seconds',
    'Job execution time',
    ['job_name', 'status']
)

fixtures_synced = Gauge(
    'fixtures_synced_total',
    'Total fixtures in DB'
)

model_prediction_errors = Counter(
    'model_prediction_errors_total',
    'Prediction errors by market',
    ['league', 'market']
)

# Uso
@job_duration.labels(job_name='sync_fixtures', status='success').time()
async def sync_fixtures_week(week):
    # ... código ...
    api_requests_total.labels(endpoint='fixtures', status='200').inc()
    fixtures_synced.set(total_fixtures)
```

**Dashboard Grafana:**
- Panel 1: Request rate por endpoint
- Panel 2: Job durations (p50, p95, p99)
- Panel 3: Error rate por job
- Panel 4: API quota usage (% consumido)
- Panel 5: Model prediction latency
- Panel 6: Data quality scores por liga

#### Web Observability (Vercel Analytics + Sentry)
```typescript
// lib/monitoring.ts
import * as Sentry from '@sentry/nextjs';
import { Analytics } from '@vercel/analytics/react';

// Sentry para errores
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1, // 10% sampling
  environment: process.env.NODE_ENV,
  beforeSend(event, hint) {
    // Filtrar errores irrelevantes
    if (event.exception) {
      const error = hint.originalException;
      if (error?.message?.includes('ResizeObserver')) {
        return null; // Ignorar error conocido
      }
    }
    return event;
  },
});

// Custom metrics
export function trackGalaxyPerformance(metrics: {
  loadTime: number;
  nodesRendered: number;
  interactions: number;
}) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'galaxy_performance', {
      load_time_ms: metrics.loadTime,
      nodes_count: metrics.nodesRendered,
      user_interactions: metrics.interactions,
    });
  }
}
```

### Alerting (Webhooks a Slack/Discord)
```python
# app/alerting.py
import httpx
from app.config import settings

async def send_alert(
    severity: str,  # 'info' | 'warning' | 'critical'
    title: str,
    message: str,
    context: dict = None
):
    """Enviar alerta a Slack"""
    color_map = {
        'info': '#36a64f',
        'warning': '#ff9900',
        'critical': '#ff0000'
    }
    
    payload = {
        "attachments": [{
            "color": color_map[severity],
            "title": f"[{severity.upper()}] {title}",
            "text": message,
            "fields": [
                {"title": k, "value": str(v), "short": True}
                for k, v in (context or {}).items()
            ],
            "footer": "Galaxy Worker",
            "ts": int(datetime.now().timestamp())
        }]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(settings.SLACK_WEBHOOK_URL, json=payload)

# Uso en jobs críticos
if api_quota_usage > 0.9:
    await send_alert(
        'warning',
        'API Quota High Usage',
        f'API-Football quota at {api_quota_usage*100:.1f}%',
        context={
            'requests_today': requests_count,
            'quota_limit': quota_limit,
            'time_until_reset': time_until_reset
        }
    )
```

---

## 16.3) Rate Limiting y Caching Estratégico (P0 - CRÍTICO)

### Circuit Breaker Pattern
```python
# app/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception=Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                "circuit_breaker_opened",
                failures=self.failure_count
            )
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
        )

# Uso con API-Football
api_circuit = CircuitBreaker(failure_threshold=3, timeout=300)

async def fetch_fixtures_safe(league_id: int, date: str):
    return await api_circuit.call(
        _fetch_fixtures_from_api,
        league_id,
        date
    )
```

### Queue System con Backoff Exponencial
```python
# app/queue.py
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    before_sleep=lambda retry_state: logger.info(
        "retrying_api_call",
        attempt=retry_state.attempt_number,
        wait_seconds=retry_state.next_action.sleep
    )
)
async def fetch_with_retry(url: str, headers: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
```

### Cache Inteligente por Contexto
```python
# app/cache.py
from functools import wraps
import hashlib
import json
from typing import Optional
import aioredis

class SmartCache:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
    
    def cache(
        self,
        ttl_func: callable,  # Función que calcula TTL dinámico
        key_prefix: str
    ):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generar cache key
                cache_key = self._make_key(key_prefix, args, kwargs)
                
                # Intentar obtener de cache
                cached = await self.redis.get(cache_key)
                if cached:
                    logger.debug("cache_hit", key=cache_key)
                    return json.loads(cached)
                
                # Cache miss: ejecutar función
                result = await func(*args, **kwargs)
                
                # Calcular TTL dinámico
                ttl = ttl_func(*args, **kwargs)
                
                # Guardar en cache
                await self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(result)
                )
                
                logger.debug("cache_miss", key=cache_key, ttl=ttl)
                return result
            return wrapper
        return decorator
    
    def _make_key(self, prefix: str, args, kwargs) -> str:
        # Hash de argumentos
        args_str = json.dumps([args, kwargs], sort_keys=True)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return f"{prefix}:{args_hash}"

# Uso con TTL dinámico basado en kickoff
cache = SmartCache(settings.REDIS_URL)

def calculate_fixture_ttl(league_id: int, date: str) -> int:
    """TTL más corto cuando el partido se acerca"""
    kickoff = datetime.fromisoformat(date)
    time_until = (kickoff - datetime.now()).total_seconds()
    
    if time_until < 3600:  # < 1 hora
        return 300  # 5 min
    elif time_until < 86400:  # < 1 día
        return 3600  # 1 hora
    elif time_until < 604800:  # < 1 semana
        return 21600  # 6 horas
    else:
        return 86400  # 24 horas

@cache.cache(ttl_func=calculate_fixture_ttl, key_prefix="fixtures")
async def fetch_fixtures(league_id: int, date: str):
    return await _fetch_from_api(league_id, date)
```

### Rate Limiter con Token Bucket
```python
# app/rate_limiter.py
import asyncio
import time

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Recargar tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # Calcular tiempo de espera
            wait_time = (tokens - self.tokens) / self.rate
            logger.warning(
                "rate_limit_waiting",
                wait_seconds=wait_time,
                tokens_available=self.tokens
            )
            
            await asyncio.sleep(wait_time)
            self.tokens = 0
            return True

# Configuración por plan API-Football
# Free: 100 requests/day = 0.00116 req/sec
# Pro: 3000 requests/day = 0.0347 req/sec
api_limiter = TokenBucket(
    rate=0.03,  # ~2500 req/day con margen
    capacity=10  # Burst de 10 requests
)

async def api_call_with_limit(endpoint: str):
    await api_limiter.acquire()
    return await _make_api_call(endpoint)
```

---

# 17) TÉCNICAS AVANZADAS PARA AUMENTAR PRECISIÓN

## 17.1) Feature Engineering Avanzado

### Features Contextuales
```python
# app/features/contextual.py
from dataclasses import dataclass
from typing import List

@dataclass
class ContextualFeatures:
    """Features que capturan contexto del partido"""
    
    # Forma reciente (weighted by recency)
    home_form_l5: float  # Últimos 5 (más peso a recientes)
    away_form_l5: float
    home_form_l10: float
    away_form_l10: float
    
    # Head-to-head
    h2h_home_wins_pct: float  # % victorias local en H2H
    h2h_goals_home_avg: float
    h2h_goals_away_avg: float
    h2h_btts_pct: float  # % partidos con ambos anotan
    
    # Contexto de liga
    home_position: int  # Posición en tabla
    away_position: int
    home_points_per_game: float
    away_points_per_game: float
    
    # Descanso y viajes
    home_days_rest: int
    away_days_rest: int
    away_travel_distance_km: float  # Distancia viaje
    
    # Momento de temporada
    matchweek: int
    season_phase: str  # 'early' | 'mid' | 'late' | 'finale'
    
    # Presión competitiva
    home_relegation_risk: bool  # En zona descenso
    away_relegation_risk: bool
    home_title_contender: bool  # Top 4
    away_title_contender: bool
    
    # Racha
    home_unbeaten_streak: int
    away_unbeaten_streak: int
    home_winless_streak: int
    away_winless_streak: int
    
    # Rendimiento por venue
    home_home_ppg: float  # Points per game en casa
    away_away_ppg: float  # Points per game fuera
    
    # Goles esperados (si disponible)
    home_xg_for_avg: float  # xG generado promedio
    home_xg_against_avg: float  # xG concedido promedio
    away_xg_for_avg: float
    away_xg_against_avg: float
    
    # Disciplina
    home_yellow_cards_avg: float
    away_yellow_cards_avg: float
    home_red_cards_total: int
    away_red_cards_total: int
    
    # Corners (predictivo para overs)
    home_corners_for_avg: float
    home_corners_against_avg: float
    away_corners_for_avg: float
    away_corners_against_avg: float
```

### Features de Plantilla
```python
@dataclass
class SquadFeatures:
    """Features basadas en plantilla y alineación"""
    
    # Valor de mercado (Transfermarkt)
    home_squad_value_m: float  # Millones EUR
    away_squad_value_m: float
    squad_value_ratio: float  # home / away
    
    # Edad promedio
    home_avg_age: float
    away_avg_age: float
    
    # Experiencia
    home_avg_caps: float  # Partidos internacionales
    away_avg_caps: float
    home_avg_league_apps: float  # Partidos en liga
    away_avg_league_apps: float
    
    # Injuries/Suspensions
    home_key_players_missing: int  # Titulares ausentes
    away_key_players_missing: int
    home_minutes_missing_pct: float  # % minutos jugados ausentes
    away_minutes_missing_pct: float
    
    # Lineup predictivo
    home_lineup_strength: float  # Rating ponderado XI
    away_lineup_strength: float
    home_bench_strength: float  # Calidad banco
    away_bench_strength: float
```

### Features de Estilo de Juego
```python
@dataclass
class StyleFeatures:
    """Estilo táctico del equipo"""
    
    # Posesión
    home_possession_avg: float
    away_possession_avg: float
    
    # Intensidad
    home_passes_per_game: int
    away_passes_per_game: int
    home_pass_accuracy: float
    away_pass_accuracy: float
    
    # Pressing
    home_tackles_per_game: float
    away_tackles_per_game: float
    home_interceptions_per_game: float
    away_interceptions_per_game: float
    
    # Ofensiva
    home_shots_per_game: float
    away_shots_per_game: float
    home_shots_on_target_pct: float
    away_shots_on_target_pct: float
    
    # Set pieces
    home_goals_from_setpieces_pct: float
    away_goals_from_setpieces_pct: float
    
    # Contraataques
    home_counterattack_goals_pct: float
    away_counterattack_goals_pct: float
```

---

## 17.2) Modelos Ensemble (Mayor Precisión)

### Stack de Modelos Base
```python
# app/models/ensemble.py
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier
)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import numpy as np

class EnsemblePredictor:
    """Ensemble de modelos para mayor robustez"""
    
    def __init__(self):
        # Modelo 1: Poisson/Dixon-Coles (teórico)
        self.poisson_model = DixonColesModel()
        
        # Modelo 2: Gradient Boosting (captura no-linealidades)
        self.xgb_model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8
        )
        
        # Modelo 3: LightGBM (rápido + efectivo)
        self.lgbm_model = LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31
        )
        
        # Modelo 4: Random Forest (diversidad)
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10
        )
        
        # Modelo 5: Rating-based (Elo adaptado)
        self.elo_model = FootballEloModel()
        
        # Meta-learner (stacking)
        self.meta_model = GradientBoostingClassifier(
            n_estimators=50,
            max_depth=3
        )
    
    def fit(self, X_train, y_train, X_val, y_val):
        """Entrenar ensemble con validación"""
        
        # Train base models
        self.poisson_model.fit(X_train, y_train)
        self.xgb_model.fit(X_train, y_train)
        self.lgbm_model.fit(X_train, y_train)
        self.rf_model.fit(X_train, y_train)
        self.elo_model.fit(X_train, y_train)
        
        # Generate meta-features (out-of-fold predictions)
        meta_features = self._get_meta_features(X_val)
        
        # Train meta-model
        self.meta_model.fit(meta_features, y_val)
    
    def predict_proba(self, X):
        """Predicción ensemble con pesos optimizados"""
        
        # Predicciones de modelos base
        base_predictions = [
            self.poisson_model.predict_proba(X),
            self.xgb_model.predict_proba(X),
            self.lgbm_model.predict_proba(X),
            self.rf_model.predict_proba(X),
            self.elo_model.predict_proba(X)
        ]
        
        # Stack predictions
        meta_features = np.column_stack(base_predictions)
        
        # Meta-predicción
        final_probs = self.meta_model.predict_proba(meta_features)
        
        return final_probs
    
    def _get_meta_features(self, X):
        """Generar features para meta-learner"""
        predictions = []
        for model in [self.poisson_model, self.xgb_model, 
                      self.lgbm_model, self.rf_model, self.elo_model]:
            preds = model.predict_proba(X)
            predictions.append(preds)
        return np.column_stack(predictions)
```

### Calibración Avanzada
```python
# app/models/calibration.py
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
import numpy as np

class MultiCalibrator:
    """Calibración por liga y mercado"""
    
    def __init__(self):
        self.calibrators = {}  # {(league, market): calibrator}
    
    def fit(self, predictions, outcomes, leagues, markets):
        """Entrenar calibradores por contexto"""
        
        for league in np.unique(leagues):
            for market in np.unique(markets):
                mask = (leagues == league) & (markets == market)
                
                if mask.sum() < 30:  # Mínimo de muestras
                    continue
                
                X = predictions[mask].reshape(-1, 1)
                y = outcomes[mask]
                
                # Isotonic Regression (monótona)
                calibrator = IsotonicRegression(
                    out_of_bounds='clip'
                )
                calibrator.fit(X.ravel(), y)
                
                self.calibrators[(league, market)] = calibrator
    
    def calibrate(self, prediction, league, market):
        """Aplicar calibración específica"""
        
        key = (league, market)
        
        if key not in self.calibrators:
            # Fallback: usar calibrador global o devolver sin cambios
            return prediction
        
        calibrator = self.calibrators[key]
        calibrated = calibrator.transform([prediction])[0]
        
        return np.clip(calibrated, 0.01, 0.99)  # Evitar extremos
```

---

## 17.3) Sistema de Rating Elo Adaptado

```python
# app/models/elo_football.py
import numpy as np
from dataclasses import dataclass

@dataclass
class TeamElo:
    team_id: int
    rating: float = 1500.0
    home_advantage: float = 100.0
    attack_rating: float = 0.0  # Desviación ofensiva
    defense_rating: float = 0.0  # Desviación defensiva

class FootballEloSystem:
    """Sistema Elo adaptado para fútbol"""
    
    def __init__(
        self,
        k_factor: float = 40.0,
        home_advantage: float = 100.0,
        goal_diff_multiplier: float = 1.5
    ):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.goal_diff_multiplier = goal_diff_multiplier
        self.teams = {}  # {team_id: TeamElo}
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Probabilidad de victoria usando fórmula logística"""
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(
        self,
        home_id: int,
        away_id: int,
        home_goals: int,
        away_goals: int
    ):
        """Actualizar ratings post-match"""
        
        # Obtener o crear ratings
        home = self.teams.get(home_id, TeamElo(home_id))
        away = self.teams.get(away_id, TeamElo(away_id))
        
        # Expected scores
        home_expected = self.expected_score(
            home.rating + self.home_advantage,
            away.rating
        )
        away_expected = 1 - home_expected
        
        # Actual scores (con draws = 0.5)
        if home_goals > away_goals:
            home_actual, away_actual = 1.0, 0.0
        elif away_goals > home_goals:
            home_actual, away_actual = 0.0, 1.0
        else:
            home_actual, away_actual = 0.5, 0.5
        
        # Goal difference multiplier (mayor K para goleadas)
        goal_diff = abs(home_goals - away_goals)
        margin_multiplier = self._margin_multiplier(goal_diff)
        
        # Actualizar ratings
        k_effective = self.k_factor * margin_multiplier
        
        home.rating += k_effective * (home_actual - home_expected)
        away.rating += k_effective * (away_actual - away_expected)
        
        # Actualizar componentes ataque/defensa
        self._update_attack_defense(home, away, home_goals, away_goals)
        
        self.teams[home_id] = home
        self.teams[away_id] = away
    
    def _margin_multiplier(self, goal_diff: int) -> float:
        """Ajuste por diferencia de goles"""
        if goal_diff <= 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        else:
            return (11 + goal_diff) / 8
    
    def _update_attack_defense(
        self,
        home: TeamElo,
        away: TeamElo,
        home_goals: int,
        away_goals: int
    ):
        """Actualizar componentes ataque/defensa"""
        alpha = 0.1  # Learning rate
        
        # Home attack vs Away defense
        home.attack_rating += alpha * (home_goals - 1.5)  # 1.5 = media liga
        away.defense_rating += alpha * (home_goals - 1.5)
        
        # Away attack vs Home defense
        away.attack_rating += alpha * (away_goals - 1.2)  # Visiting teams score less
        home.defense_rating += alpha * (away_goals - 1.2)
    
    def predict_match(self, home_id: int, away_id: int) -> dict:
        """Predecir resultado usando Elo"""
        
        home = self.teams.get(home_id, TeamElo(home_id))
        away = self.teams.get(away_id, TeamElo(away_id))
        
        # Ajustar por componentes
        home_strength = home.rating + self.home_advantage + home.attack_rating - home.defense_rating
        away_strength = away.rating + away.attack_rating - away.defense_rating
        
        # Probabilidades
        home_win_prob = self.expected_score(home_strength, away_strength)
        
        # Modelo simplificado para 1X2
        draw_prob = 0.27  # Baseline draw rate
        away_win_prob = 1 - home_win_prob - draw_prob
        
        # Ajustar si negativo
        if away_win_prob < 0:
            away_win_prob = 0.05
            home_win_prob = 1 - draw_prob - away_win_prob
        
        return {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
            'expected_goals_home': 1.5 + (home.attack_rating / 100),
            'expected_goals_away': 1.2 + (away.attack_rating / 100)
        }
```

---

## 17.4) Validación Temporal (Walk-Forward)

```python
# app/models/validation.py
from sklearn.model_selection import TimeSeriesSplit
import pandas as pd
import numpy as np

def walk_forward_validation(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
    n_splits: int = 5,
    test_size_weeks: int = 4
):
    """
    Validación temporal para series de tiempo
    Entrena en pasado, predice en futuro inmediato
    """
    
    results = []
    
    # Ordenar por fecha
    sort_idx = dates.argsort()
    X_sorted = X.iloc[sort_idx]
    y_sorted = y.iloc[sort_idx]
    dates_sorted = dates.iloc[sort_idx]
    
    # Time series split
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X_sorted)):
        
        X_train = X_sorted.iloc[train_idx]
        y_train = y_sorted.iloc[train_idx]
        X_test = X_sorted.iloc[test_idx]
        y_test = y_sorted.iloc[test_idx]
        
        # Entrenar
        model.fit(X_train, y_train)
        
        # Predecir
        y_pred_proba = model.predict_proba(X_test)
        
        # Métricas
        from sklearn.metrics import log_loss, brier_score_loss
        
        logloss = log_loss(y_test, y_pred_proba)
        brier = brier_score_loss(y_test, y_pred_proba[:, 1])
        
        # Calibration curve
        calibration = compute_calibration_bins(y_test, y_pred_proba[:, 1])
        
        results.append({
            'fold': fold,
            'train_start': dates_sorted.iloc[train_idx[0]],
            'train_end': dates_sorted.iloc[train_idx[-1]],
            'test_start': dates_sorted.iloc[test_idx[0]],
            'test_end': dates_sorted.iloc[test_idx[-1]],
            'n_train': len(train_idx),
            'n_test': len(test_idx),
            'log_loss': logloss,
            'brier_score': brier,
            'calibration': calibration
        })
        
        logger.info(
            "walk_forward_fold_completed",
            fold=fold,
            log_loss=logloss,
            brier=brier
        )
    
    return pd.DataFrame(results)

def compute_calibration_bins(y_true, y_pred, n_bins=10):
    """Calibration reliability curve"""
    bins = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_pred, bins) - 1
    
    calibration_data = []
    
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            predicted_prob = y_pred[mask].mean()
            actual_freq = y_true[mask].mean()
            count = mask.sum()
            
            calibration_data.append({
                'bin': i,
                'predicted': predicted_prob,
                'actual': actual_freq,
                'count': count,
                'error': abs(predicted_prob - actual_freq)
            })
    
    return calibration_data
```

---

# 18) FASES — "TODO LO NECESARIO" (con checklists)
Cada fase incluye:
- Objetivo  
- Entradas (inputs)  
- Salidas (artifacts)  
- Tareas detalladas  
- Archivos/rutas  
- Tests/verificación  
- Checklist “Completo”  
- Prompt para IA Coder

---

## Fase 0 — Scaffolding + Infra + Schema base (Starter)
### Objetivo
Tener un repo que **corra en VS Code** y tenga DB base creada.

### Inputs
- Supabase project creado
- API key de API-Football (todavía no usada en stubs)

### Artifacts/Salidas
- Repo con:
  - `apps/web` Next.js
  - `apps/worker` FastAPI
  - `supabase/schema.sql`, `supabase/rls.sql`
- Deploy local y health endpoints

### Tareas (mínimas)
1) Crear monorepo (workspaces)  
2) Next.js app router + health route  
3) Worker FastAPI health + internal ping (header secret)  
4) SQL schema + RLS watchlist  

### Verificación
- `npm run dev`  
- Web: `/api/health` ok  
- Worker: `/health` ok y `/internal/ping` ok con header

### Checklist Fase 0 — COMPLETO
- [ ] El repo abre y corre en VS Code  
- [ ] Hay `.env.example` para web y worker  
- [ ] Schema y RLS corren sin error en Supabase  
- [ ] No hay keys en frontend

### Prompt IA (Fase 0)
(Usar el “Prompt Maestro” al final, sección por fase)

---

## Fase 1 — Ingesta real de fixtures + leagues (semana actual/próxima)
### Objetivo
Poblar DB con ligas y fixtures reales para la semana con rate limiting, caching y observabilidad.

### Inputs
- `APIFOOTBALL_API_KEY`
- Lista de ligas V1 (Top 10) y seasons (actual)
- Supabase service role key en worker
- Redis URL (cache)
- Slack webhook (alertas)

### Salidas
- `leagues` y `fixtures` pobladas  
- Endpoint web: `GET /api/galaxy?week=...&leagues=...` leyendo de Supabase  
- UI: lista semanal real (antes de Galaxy canvas)
- **NUEVO:** Rate limiter configurado
- **NUEVO:** Circuit breaker implementado
- **NUEVO:** Cache con TTL dinámico
- **NUEVO:** Tests unitarios + integración

### Tareas detalladas

#### 1) Worker - Infra
   - **Rate Limiter:** Token bucket (0.03 req/s para Pro tier)
   - **Circuit Breaker:** 3 fallos → open, 5 min → half-open
   - **Cache:** Redis con TTL dinámico por proximidad a kickoff
   - **Logging:** structlog con JSON output
   - **Alerting:** Slack webhook para fallos críticos

#### 2) Worker - Jobs
   - Implementar `sync_leagues`:
     ```python
     # apps/worker/app/jobs/sync_leagues.py
     @rate_limited
     @with_circuit_breaker
     async def sync_leagues(league_ids: List[int]):
         """Sync leagues con retry y logging"""
         logger.info("sync_leagues_started", count=len(league_ids))
         
         for league_id in league_ids:
             try:
                 await api_limiter.acquire()
                 league_data = await fetch_league(league_id)
                 await upsert_league(league_data)
                 
             except Exception as e:
                 logger.error("sync_league_failed", 
                             league_id=league_id, error=str(e))
                 if should_alert(e):
                     await send_alert('warning', 
                                     f'League sync failed: {league_id}')
                 raise
     ```
   
   - Implementar `sync_fixtures_week`:
     ```python
     # apps/worker/app/jobs/sync_fixtures.py
     @cached(ttl_func=calculate_ttl, key_prefix="fixtures")
     @retry(stop=stop_after_attempt(5), wait=wait_exponential())
     async def sync_fixtures_week(week: datetime, leagues: List[int]):
         """Sync fixtures con cache y retry"""
         logger.info("sync_fixtures_started", 
                    week=week.isoformat(), leagues_count=len(leagues))
         
         fixtures = []
         for league_id in leagues:
             await api_limiter.acquire()
             
             league_fixtures = await fetch_fixtures(
                 league_id=league_id,
                 date_from=week,
                 date_to=week + timedelta(days=7)
             )
             fixtures.extend(league_fixtures)
         
         # Upsert idempotente
         result = await bulk_upsert_fixtures(fixtures)
         
         logger.info("sync_fixtures_completed",
                    inserted=result['inserted'],
                    updated=result['updated'])
         
         return result
     ```

#### 3) Worker - Tests
   ```python
   # apps/worker/tests/unit/test_sync_fixtures.py
   @pytest.mark.asyncio
   async def test_sync_fixtures_idempotent(mock_db, mock_api):
       """Verificar idempotencia"""
       week = datetime(2026, 1, 20)
       
       # Primera ejecución
       result1 = await sync_fixtures_week(week, [39])  # Premier
       count1 = await mock_db.count('fixtures')
       
       # Segunda ejecución
       result2 = await sync_fixtures_week(week, [39])
       count2 = await mock_db.count('fixtures')
       
       assert count1 == count2
       assert result2['duplicates'] == count1
   
   @pytest.mark.asyncio
   async def test_rate_limiter_enforced(mock_api):
       """Verificar que rate limiter funciona"""
       start = time.time()
       
       # Hacer 5 requests (burst capacity = 10, rate = 0.03)
       for _ in range(5):
           await api_limiter.acquire()
       
       elapsed = time.time() - start
       assert elapsed < 1.0  # Burst permitido
       
       # Request 11 debe esperar
       for _ in range(6):
           await api_limiter.acquire()
       
       elapsed = time.time() - start
       assert elapsed > 1.0  # Tuvo que esperar
   ```

#### 4) Web - API Route
   ```typescript
   // apps/web/app/api/galaxy/route.ts
   import { logger } from '@/lib/logger';
   import * as Sentry from '@sentry/nextjs';
   
   export async function GET(request: Request) {
     const requestId = crypto.randomUUID();
     const startTime = performance.now();
     
     logger.info({
       msg: 'galaxy_request_started',
       requestId,
       url: request.url,
     });
     
     try {
       const { searchParams } = new URL(request.url);
       const week = searchParams.get('week') || getCurrentWeek();
       const leagues = searchParams.get('leagues')?.split(',') || [];
       
       const fixtures = await fetchFixtures(week, leagues);
       
       logger.info({
         msg: 'galaxy_request_completed',
         requestId,
         fixtures_count: fixtures.length,
         duration_ms: performance.now() - startTime,
       });
       
       return Response.json({
         fixtures,
         metadata: {
           week,
           leagues,
           count: fixtures.length,
         },
       });
       
     } catch (error) {
       logger.error({
         msg: 'galaxy_request_failed',
         requestId,
         error: error.message,
         stack: error.stack,
       });
       
       Sentry.captureException(error, {
         tags: { requestId, endpoint: 'galaxy' },
       });
       
       return Response.json(
         { error: 'Internal server error' },
         { status: 500 }
       );
     }
   }
   ```

#### 5) Web - Tests E2E
   ```typescript
   // apps/web/__tests__/e2e/galaxy.spec.ts
   import { test, expect } from '@playwright/test';
   
   test('Galaxy API devuelve fixtures de la semana', async ({ request }) => {
     const response = await request.get('/api/galaxy?week=2026-01-20');
     expect(response.ok()).toBeTruthy();
     
     const data = await response.json();
     expect(data.fixtures).toBeDefined();
     expect(data.fixtures.length).toBeGreaterThan(0);
     expect(data.metadata.week).toBe('2026-01-20');
   });
   ```

### Archivos/rutas
```
apps/worker/
├─ app/
│  ├─ jobs/
│  │  ├─ sync_leagues.py          ⭐ NUEVO
│  │  └─ sync_fixtures.py          ⭐ NUEVO
│  ├─ rate_limiter.py              ⭐ NUEVO
│  ├─ circuit_breaker.py           ⭐ NUEVO
│  ├─ cache.py                     ⭐ NUEVO
│  └─ alerting.py                  ⭐ NUEVO
└─ tests/
   ├─ unit/
   │  ├─ test_sync_fixtures.py     ⭐ NUEVO
   │  └─ test_rate_limiter.py      ⭐ NUEVO
   └─ integration/
      └─ test_api_football.py      ⭐ NUEVO

apps/web/
├─ app/api/galaxy/route.ts         ⭐ MODIFICADO
└─ __tests__/
   └─ e2e/galaxy.spec.ts           ⭐ NUEVO
```

### Verificación
1. **Unit tests pasan:** `pytest apps/worker/tests/unit -v`
2. **Integration tests pasan:** `pytest apps/worker/tests/integration -v`
3. **E2E tests pasan:** `npm run test:e2e`
4. **Idempotencia:** Correr job 2 veces, verificar count fixtures
5. **Rate limiting:** Logs muestran "rate_limit_waiting" cuando corresponde
6. **Circuit breaker:** Simular 3 fallos API, verificar "circuit_breaker_opened"
7. **Alertas:** Verificar que llegan a Slack en fallos
8. **Métricas:** Verificar en Grafana/Vercel Analytics

### Checklist Fase 1 — COMPLETO
- [ ] Fixtures de semana actual y próxima están en DB  
- [ ] Upserts idempotentes (correr 2 veces no duplica)  
- [ ] API keys nunca salen al cliente  
- [ ] UI muestra fixtures reales por día
- [ ] **Rate limiter configurado y testeado**  ⭐ NUEVO
- [ ] **Circuit breaker funcional**  ⭐ NUEVO
- [ ] **Cache con TTL dinámico**  ⭐ NUEVO
- [ ] **Logging estructurado (JSON)**  ⭐ NUEVO
- [ ] **Alertas Slack configuradas**  ⭐ NUEVO
- [ ] **Tests unitarios pasan (>70% coverage)**  ⭐ NUEVO
- [ ] **Tests E2E pasan**  ⭐ NUEVO
- [ ] **CI/CD pipeline funcional**  ⭐ NUEVO

---

## Fase 2 — Catálogo de mercados + odds snapshots (pre-match)
### Objetivo
Descubrir mercados disponibles y guardar snapshots de odds.

### Inputs
- Ligas y fixtures ya poblados
- Definir “bookmakers base” (top N) para almacenar

### Salidas
- `markets_catalog` poblado (desde upstream)
- `odds_snapshots` guardando odds pre-match
- `market_availability` inicial (coverage-based)

### Tareas detalladas
1) Worker:
   - Sync `markets_catalog`:
     - Descubrir bet types/markets disponibles
     - Normalizar `key` (stable)
   - Sync odds:
     - Para fixtures próximos (T-14d a T-0)
     - Guardar snapshots con timestamp
     - Rate limit + caching
2) Quality Gate (versión 1):
   - Calcular coverage por (liga, mercado):
     - % fixtures con odds disponibles
   - Asignar A/B/C con umbrales iniciales

### DB changes (si faltan)
- Asegurar tabla `odds_snapshots` y campos necesarios

### Checklist Fase 2 — COMPLETO
- [ ] Markets catalog estable y versionable  
- [ ] Odds snapshots guardadas con timestamp  
- [ ] Rate limiting/caching para no saturar  
- [ ] `market_availability` calculada y aplicada en UI (difuminado)

---

## Fase 3 — Modelo baseline + scoring + calibración + gating por performance
### Objetivo
Generar probabilidades por mercado con modelos base calibrados.

### Inputs
- Históricos suficientes por liga/mercado (mínimo temporadas)
- Outcomes post-match (si aún no existen, crear pipeline de outcomes)

### Salidas
- `model_versions` y `model_predictions` pobladas
- Dashboard interno (mínimo) de métricas por mercado/liga
- Ajuste de `market_availability` con performance gate (no solo coverage)

### Tareas detalladas
1) Outcomes:
   - Worker job para “settle outcomes” post-match
   - Mapear resultados a mercados (O/U, 1X2, etc.)
2) Features:
   - Construir dataset: últimos N partidos, fuerza ofensiva/defensiva, etc.
3) Model:
   - Implementar baseline (Poisson / Dixon-Coles)
   - Implementar calibración
4) Scoring:
   - Para cada fixture upcoming: generar p por mercado
   - Guardar en DB con model_version
5) Performance Gate:
   - Si Brier/LogLoss mal → bajar grade

### Checklist Fase 3 — COMPLETO
- [ ] Probabilidades para mercados core aparecen en UI  
- [ ] Calibración aplicada por liga/mercado  
- [ ] Outcomes y backtest temporal corren  
- [ ] Performance gate actualiza availability

---

## Fase 4 — Galaxy UI (Canvas/WebGL) + Match Drawer completo
### Objetivo
Reemplazar la lista por la vista “galaxia” usable y rápida.

### Inputs
- Fixtures + probabilities disponibles
- Quality grades A/B/C

### Salidas
- Galaxy interactiva (zoom/pan, clusters por día)
- Match Drawer con mercados agrupados, badges, tooltips
- Fallback lista móvil y “low-performance mode”

### Tareas detalladas
1) Elegir renderer:
   - PixiJS (2D rápido) recomendado para V1
2) Diseño:
   - Layout por semana (clusters por día)
   - Encodings: size/halo/opacities
3) Perf:
   - LOD: menos detalle al alejar zoom
   - Virtualización de labels

### Checklist Fase 4 — COMPLETO
- [ ] Galaxy usable en desktop y móvil  
- [ ] Drawer rápido y claro  
- [ ] Difuminado de mercados C funcional  
- [ ] Fallback lista disponible

---

## Fase 5 — Watchlist + Tracking + Dashboard anti-churn
### Objetivo
Agregar loop de retención: guardar, revisar, comparar con outcomes.

### Inputs
- Auth Supabase (login básico)
- Outcomes settling en worker

### Salidas
- CRUD Watchlist (fixtures/markets/players)
- Tracking: registro de predicciones guardadas
- Dashboard semanal por usuario

### Tareas detalladas
1) Auth:
   - Login (email OTP o magic link)
2) Watchlist UI:
   - “Mis seguimientos”
3) Tracking:
   - Guardar {fixture, market, p, model_version, timestamp}
4) Dashboard:
   - 7d/30d: accuracy + brier/logloss simple + bins

### Checklist Fase 5 — COMPLETO
- [ ] Usuarios pueden guardar y ver seguimiento  
- [ ] Se registran outcomes y se reflejan  
- [ ] Dashboard semanal funciona  
- [ ] Esto reduce churn (medible: retención D7)

---

## Fase 6 (V1.1) — Alertas + “Coverage Map” + Model Card
### Objetivo
Completar áreas de oportunidad top para confianza y retención.

### Salidas
- Alertas (lineups/injury/partido por iniciar)
- Coverage Map por liga/mercado
- Model Card público (versión + métricas)

### Checklist Fase 6 — COMPLETO
- [ ] Alertas configurables  
- [ ] Coverage map visible  
- [ ] Model card reduce quejas/churn  

---

# 17) PROMPT MAESTRO IA CODER (TODO)
Copia/pega esto para que la IA construya **todo** por fases sin omitir.

## Instrucciones globales
Eres un **Senior Full-Stack Engineer + Data Engineer**. Construye “Galaxy Calendar Football Probabilities” como app educativa 18+ sin integración de apuestas.  
Entregables por fase:
1) Código completo (archivos completos) con rutas exactas  
2) Comandos de instalación y dónde ejecutarlos  
3) Variables `.env.example` por servicio  
4) Migraciones SQL (Supabase) si se agregan tablas/indices  
5) Tests básicos y pasos de verificación  
6) Checklist “Definition of Done” por fase  
7) Sin exponer API keys al cliente  
8) Implementar caching y rate-limit interno

## Stack
- Web: Next.js + TypeScript strict + zod
- UI: Tailwind + shadcn/ui (o UI simple al inicio)
- DB/Auth: Supabase Postgres + RLS
- Worker: FastAPI (Python)
- Cache opcional: Upstash Redis

## Repo
Preferir monorepo:
- `apps/web`
- `apps/worker`
- `packages/shared`
- `supabase/`

---

## Prompt Fase 0 (Scaffolding)
Construye repo con Next.js y FastAPI, health endpoints, SQL schema base y RLS para watchlist.  
Entrega todos los archivos y rutas. Incluye README con pasos en Windows (PowerShell) y Mac/Linux.

## Prompt Fase 1 (Fixtures reales)
Implementa:
- Jobs en worker: `sync_leagues`, `sync_fixtures_week` (semana actual y próxima)
- Persistir a Supabase con upsert idempotente
- Web API: `/api/galaxy`
- UI lista semanal real
Incluye rate limit, retries y logging estructurado.

## Prompt Fase 2 (Markets + odds snapshots)
Implementa:
- Markets catalog desde upstream
- Odds snapshots pre-match con timestamp
- Quality gate coverage-based (A/B/C)
- UI: difuminado para C y warning para B
Incluye caching (por fixture/market) y límites de requests.

## Prompt Fase 3 (Modelo + calibración + outcomes)
Implementa:
- Settling outcomes post-match (markets core)
- Dataset simple + baseline Poisson/Dixon-Coles
- Calibración por liga/mercado
- Scoring upcoming fixtures → `model_predictions`
- Métricas: brier/logloss + bins
- Performance gate que actualiza availability

## Prompt Fase 4 (Galaxy UI)
Implementa:
- Galaxy canvas (PixiJS recomendado)
- Zoom/pan + clusters por día
- Match drawer con mercados + badges + tooltips
- Fallback lista móvil y modo bajo rendimiento
Optimiza performance (LOD + virtualización).

## Prompt Fase 5 (Watchlist + Tracking)
Implementa:
- Auth Supabase
- Watchlist CRUD
- Tracking y dashboard semanal por usuario
- UI “Mis seguimientos” + filtros

## Prompt Fase 6 (Alertas + Coverage Map + Model Card)
Implementa:
- Alertas (lineups/injury/partido por iniciar)
- Coverage Map por liga/mercado
- Model Card (versión, datos, métricas)
- Panel admin jobs/missingness

---

# 18) ¿Hace falta agregar algo más?
**No** para “tenerlo todo listo como guía”.  
**Sí** para ejecutar cada fase: se necesita implementar el código de cada fase (que la IA generará usando este documento).  
Este archivo es el “manual maestro” para que ninguna fase quede incompleta.

---

## 19) Checklist global “antes de pasar a producción”
- [ ] Age gate 18+ + responsible messaging  
- [ ] No links/afiliación a casas  
- [ ] Legal pages (TOS/Privacy)  
- [ ] Rate limiting + caching robusto  
- [ ] Secrets en server only  
- [ ] Observabilidad (logs + alertas jobs)  
- [ ] Model Card + Coverage Map publicados  
- [ ] “Experimental toggle” para markets C  

---

**Fin del documento.**

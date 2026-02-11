# PRÓXIMOS PASOS - GALAXYPARLAY

**Fecha de creación:** 6 de febrero de 2026  
**Estado del proyecto:** Backend funcionando ✅ | Frontend mostrando solo 2 partidos (bug) ❌

---

## 📊 ESTADO ACTUAL DEL SISTEMA

### ✅ COMPLETADO Y FUNCIONANDO:

#### 1. Backend Railway

- **URL:** https://galaxyparlay-production.up.railway.app
- **Estado:** HTTP 200 ✅ Funcionando perfectamente
- **Tecnología:** FastAPI + Python 3.11
- **Características activas:**
  - FIFA Scraper: ✅ 215 teams synced
  - Predicciones: ✅ 6,895 generadas para 500 fixtures
  - Scheduler: ✅ APScheduler corriendo (jobs cada 6h y 12h)
  - Endpoint principal: `/api/fixtures?status=NS&limit=100` devuelve 100+ partidos con predicciones completas

#### 2. Frontend Vercel

- **URL:** https://galaxyparlay.vercel.app
- **Estado:** HTTP 200 ✅ Cargando correctamente
- **Tecnología:** Next.js 14+
- **Problema:** Solo muestra 2 partidos cuando deberían aparecer cientos ❌

#### 3. Base de Datos Supabase

- **Proyecto:** jssjwjsuqmkzidigipwj.supabase.co
- **Estado:** Operacional ✅
- **Datos actuales:**
  - 500 fixtures cargados (próximos 7-14 días)
  - 6,895 predictions generadas (todas listas)
  - Distribución de calidad:
    - Grade A: 1,861 predicciones (27%)
    - Grade B: 1,745 predicciones (25%)
    - Grade C: 2,085 predicciones (30%)
    - Grade D: 1,204 predicciones (17%)

#### 4. Seguridad

- ✅ Tokens hardcoded removidos de todos los archivos
- ✅ Variables de entorno configuradas en Railway
- ✅ Variables de entorno configuradas en Vercel
- ✅ SECURITY_INCIDENT.md documentado
- ✅ .gitignore protegiendo archivos sensibles

#### 5. Scheduler Automático

- ✅ Job 1: Load fixtures cada 12 horas (6 AM, 6 PM UTC)
- ✅ Job 2: Generate predictions cada 6 horas
- ✅ Próxima ejecución visible en: `/jobs/scheduler-status`

---

## 🚨 PROBLEMA ACTUAL - URGENTE

### El frontend solo muestra 2 partidos cuando deberían aparecer cientos

**Síntomas:**

- UI renderiza únicamente 2 matches
- Backend tiene 500 fixtures con 6,895 predicciones listas
- Endpoint del backend funciona perfectamente

**Causa raíz identificada:**
El frontend está llamando a un endpoint INCORRECTO, con URL mal configurada, o con filtros demasiado restrictivos.

**Evidencia técnica:**

```bash
# Backend devuelve 100 fixtures correctamente:
GET https://galaxyparlay-production.up.railway.app/api/fixtures?status=NS&limit=100
Response: 200 OK, 100 fixtures con predictions completas

# Endpoint que podría estar usando el frontend NO EXISTE:
GET https://galaxyparlay-production.up.railway.app/api/matches/today
Response: 404 Not Found
```

---

## 🎯 PLAN DE ACCIÓN DETALLADO

### FASE 1: LOCALIZAR LA LLAMADA API EN EL FRONTEND

**Archivos a revisar (en orden de prioridad):**

1. **`apps/web/app/page.tsx`**
   - Es la página principal
   - Probablemente contiene el fetch inicial

2. **`apps/web/components/`**
   - Buscar componentes que rendericen fixtures/matches
   - Nombres posibles: `FixtureList`, `MatchCard`, `PredictionView`, etc.

3. **`apps/web/lib/`**
   - Funciones de API calls
   - Nombres posibles: `api.ts`, `fetcher.ts`, `fixtures.ts`, etc.

**Comandos para buscar:**

```powershell
cd c:\Users\gm_me\GalaxyParlay

# Buscar llamadas fetch
grep -r "fetch.*api" apps/web/app/
grep -r "fetch.*fixtures" apps/web/
grep -r "fetch.*matches" apps/web/

# Buscar imports de axios u otros clientes HTTP
grep -r "axios" apps/web/
grep -r "import.*fetch" apps/web/

# Buscar URLs hardcoded
grep -r "galaxyparlay" apps/web/
grep -r "railway.app" apps/web/
grep -r "api/matches" apps/web/
```

**Patrones a buscar en el código:**

```typescript
// ❌ Posibles llamadas INCORRECTAS:
fetch("/api/matches/today");
fetch("/api/matches");
fetch("https://...railway.app/api/matches/...");
fetch("...fixtures?limit=10"); // límite demasiado bajo
fetch("...fixtures?days=1"); // solo un día

// ✅ Lo que DEBERÍA ser:
fetch(
  "https://galaxyparlay-production.up.railway.app/api/fixtures?status=NS&limit=100",
);
```

---

### FASE 2: CORREGIR LA LLAMADA API

**Cambio a implementar:**

```typescript
// ANTES (ejemplo de lo que podría estar mal):
const response = await fetch("/api/matches/today");
const data = await response.json();

// DESPUÉS (corrección):
const response = await fetch(
  "https://galaxyparlay-production.up.railway.app/api/fixtures?status=NS&limit=100",
);
const data = await response.json();

// Ahora data.fixtures contiene array de 100 fixtures con todas sus predictions
```

**Parámetros importantes del endpoint:**

- `status=NS` → Not Started (partidos que no han comenzado)
- `limit=100` → Máximo 100 resultados (límite del backend)
- Si necesitas más de 100, hacer múltiples requests o implementar paginación

**Estructura de datos que devuelve el backend:**

```typescript
interface BackendResponse {
  fixtures: Fixture[];
  total: number; // Total de fixtures que cumplen el filtro
  count: number; // Cantidad devuelta en esta respuesta
  filters: {
    league_id: number | null;
    status: string;
    limit: number;
  };
}

interface Fixture {
  id: number;
  league_id: number;
  league_name: string;
  season: number;
  kickoff_time: string; // ISO 8601 timestamp
  status: string; // "NS", "LIVE", "FT", etc.
  home_team_id: number;
  home_team_name: string;
  away_team_id: number;
  away_team_name: string;
  home_score: number | null;
  away_score: number | null;
  predictions: Prediction[]; // Array de ~14 predicciones por fixture
  quality_scores: any[];
  odds: any[];
}

interface Prediction {
  id: string; // UUID
  fixture_id: number;
  model_version: string; // "v1.1.0"
  model_name: string; // "ensemble_xgb_elo_historical"
  market_key: string; // "over_under_2_5", "match_winner", etc.
  prediction: Record<string, number>; // {"over": 0.55, "under": 0.45}
  confidence_score: number; // 0.0 - 1.0
  quality_grade: "A" | "B" | "C" | "D";
  predicted_at: string;
  features_used: Record<string, any>;
  created_at: string;
}
```

---

### FASE 3: VERIFICAR RENDERIZADO DE COMPONENTES

**Asegurar que el componente itera correctamente:**

```typescript
// En el componente que renderiza la lista:
{data?.fixtures?.map((fixture) => (
  <FixtureCard
    key={fixture.id}
    fixture={fixture}
    predictions={fixture.predictions}
  />
))}

// O si usas un componente de lista:
<FixtureList fixtures={data.fixtures} />
```

**Validaciones a agregar:**

```typescript
// Manejar estados de carga y error
if (isLoading) return <LoadingSpinner />
if (error) return <ErrorMessage error={error} />
if (!data?.fixtures?.length) return <EmptyState message="No fixtures available" />

return (
  <div>
    <h2>Total: {data.total} fixtures</h2>
    <div className="fixtures-grid">
      {data.fixtures.map((fixture) => (
        <FixtureCard key={fixture.id} fixture={fixture} />
      ))}
    </div>
  </div>
)
```

---

### FASE 4: TESTING LOCAL (ANTES DE DEPLOY)

**Comandos de desarrollo:**

```bash
cd c:\Users\gm_me\GalaxyParlay\apps\web

# Instalar dependencias (si es necesario)
pnpm install

# Correr en modo desarrollo
pnpm dev

# Abrir en navegador: http://localhost:3000
```

**Verificaciones a hacer:**

1. Console del navegador (F12) → Verificar la URL del fetch
2. Network tab → Ver el response del API
3. Contar cuántos fixtures aparecen en la UI
4. Verificar que las predicciones se muestran correctamente

---

### FASE 5: DEPLOY A PRODUCCIÓN

**Una vez confirmado que funciona localmente:**

```bash
cd c:\Users\gm_me\GalaxyParlay\apps\web

# Commit de cambios
git add .
git commit -m "fix: Correct API endpoint to fetch all fixtures from backend"

# Push a GitHub (trigger automático de Vercel)
git push origin main

# O deploy manual con Vercel CLI:
npx vercel --prod
```

**Verificación post-deploy:**

```powershell
# Esperar 1-2 minutos y verificar
Start-Sleep -Seconds 120
Invoke-WebRequest https://galaxyparlay.vercel.app
```

**Abrir en navegador:**
https://galaxyparlay.vercel.app

**Lo que DEBERÍAS ver:**

- 100+ partidos en la pantalla principal
- Partidos de Liga MX para mañana
- Partidos de fin de semana (Premier League, La Liga, etc.)
- Predicciones con Grades A, B, C, D
- Métricas tipo: "500 matches available, 1,861 Grade A predictions"

---

## 📋 INFORMACIÓN TÉCNICA DE REFERENCIA

### Endpoints del Backend Disponibles

| Endpoint                             | Método | Descripción                      | Estado      |
| ------------------------------------ | ------ | -------------------------------- | ----------- |
| `/api/fixtures`                      | GET    | Lista fixtures con predicciones  | ✅ Funciona |
| `/api/fixtures/{id}`                 | GET    | Detalle de un fixture            | ✅ Funciona |
| `/jobs/run-predictions`              | POST   | Generar predicciones manualmente | ✅ Funciona |
| `/jobs/scheduler-status`             | GET    | Estado del scheduler             | ✅ Funciona |
| `/jobs/trigger-load-fixtures`        | POST   | Cargar fixtures manualmente      | ✅ Funciona |
| `/jobs/trigger-generate-predictions` | POST   | Generar predictions manualmente  | ✅ Funciona |
| `/api/matches/today`                 | GET    | ❌ **NO EXISTE**                 | 404 Error   |

### Variables de Entorno Configuradas

**Railway (Backend):**

```bash
SUPABASE_URL=https://jssjwjsuqmkzidigipwj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (configurado)
RAILWAY_SERVICE_ROOT_DIRECTORY=apps/worker
API_FOOTBALL_KEY=(configurado)
```

**Vercel (Frontend):**

```bash
NEXT_PUBLIC_SUPABASE_URL=https://jssjwjsuqmkzidigipwj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ... (configurado)
SUPABASE_SERVICE_ROLE_KEY=eyJ... (configurado)
```

### Estructura del Monorepo

```
GalaxyParlay/
├── apps/
│   ├── web/                    # Frontend Next.js - ⚠️ AQUÍ ESTÁ EL PROBLEMA
│   │   ├── app/
│   │   │   ├── page.tsx        # 🎯 Revisar PRIMERO este archivo
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/         # 🎯 Revisar componentes de fixtures/matches
│   │   │   └── [varios].tsx
│   │   ├── lib/                # 🎯 Revisar funciones de API
│   │   │   └── [varios].ts
│   │   ├── package.json
│   │   └── next.config.mjs
│   └── worker/                 # Backend FastAPI - ✅ FUNCIONANDO PERFECTO
│       ├── app/
│       │   ├── main.py
│       │   ├── routes/
│       │   │   ├── galaxy_api.py    # Aquí está /api/fixtures
│       │   │   └── jobs.py
│       │   ├── scheduler_v2.py      # Scheduler activo
│       │   └── services/
│       ├── requirements.txt
│       └── Dockerfile
├── supabase/
│   └── migrations/
├── package.json
├── turbo.json
├── SECURITY_INCIDENT.md
└── PROXIMOS_PASOS.md           # 📄 Este archivo
```

---

## 🔍 COMANDOS ÚTILES PARA DEBUG

### Verificar estado del backend:

```powershell
# Ver fixtures con predicciones (primeros 5)
Invoke-WebRequest "https://galaxyparlay-production.up.railway.app/api/fixtures?status=NS&limit=5" | ConvertFrom-Json | ConvertTo-Json -Depth 3

# Ver estado del scheduler
Invoke-WebRequest "https://galaxyparlay-production.up.railway.app/jobs/scheduler-status" | ConvertFrom-Json | ConvertTo-Json

# Ver logs de Railway
cd c:\Users\gm_me\GalaxyParlay\apps\worker
npx railway logs --tail 50
```

### Buscar código en el frontend:

```powershell
cd c:\Users\gm_me\GalaxyParlay

# Buscar llamadas API
grep -r "fetch" apps/web/app/ | Select-String "api"
grep -r "fetch" apps/web/components/ | Select-String "fixtures|matches"
grep -r "fetch" apps/web/lib/

# Buscar URLs del backend
grep -r "railway.app" apps/web/
grep -r "galaxyparlay-production" apps/web/
```

### Verificar deployment:

```powershell
# Estado del frontend
Invoke-WebRequest https://galaxyparlay.vercel.app

# Verificar que llega al backend correcto
# (abrir DevTools en navegador y ver Network tab)
```

---

## ✅ CRITERIOS DE ÉXITO

**Después de aplicar la corrección, deberías ver:**

1. **En la UI:**
   - ✅ 100+ partidos listados (no solo 2)
   - ✅ Cada partido muestra múltiples predicciones
   - ✅ Predicciones con Grade A, B, C, D visibles
   - ✅ Partidos de Liga MX para mañana aparecen
   - ✅ Partidos de fin de semana (Premier League, La Liga, Serie A, etc.)

2. **Métricas esperadas:**
   - ✅ "500 matches available"
   - ✅ "1,861 Grade A predictions"
   - ✅ "6,895 total predictions"

3. **Funcionalidad:**
   - ✅ Filtros funcionan (por liga, por fecha, etc.)
   - ✅ Click en partido muestra detalles
   - ✅ Predicciones se actualizan automáticamente cada 6 horas

---

## 🚨 NOTAS IMPORTANTES Y ADVERTENCIAS

### ⚠️ NO TOCAR (Ya funciona correctamente):

1. **Backend Railway** - No modificar código de FastAPI
2. **Scheduler** - Ya está corriendo automáticamente
3. **Predicciones en DB** - Ya están generadas (6,895)
4. **Variables de entorno** - Ya están configuradas correctamente

### ✅ SOLO MODIFICAR:

- **Frontend**: Corregir la llamada API en `apps/web/`
- **Nada más**

### 🔴 Errores comunes a EVITAR:

1. No cambiar la URL del backend en producción
2. No modificar el límite a menos de 50 fixtures
3. No olvidar el parámetro `status=NS`
4. No hardcodear credenciales (usar env vars)
5. No deployar sin probar localmente primero

---

## 📞 INFORMACIÓN DE CONTACTO Y RECURSOS

### URLs del Proyecto:

- Frontend: https://galaxyparlay.vercel.app
- Backend: https://galaxyparlay-production.up.railway.app
- Supabase: https://supabase.com/dashboard/project/jssjwjsuqmkzidigipwj
- GitHub: https://github.com/Baahl11/GalaxyParlay

### Documentación relacionada:

- `SECURITY_INCIDENT.md` - Incidente de seguridad resuelto
- `IMPLEMENTATION_LOG.md` - Log de implementación
- `FASE_5_IMPLEMENTATION_SUMMARY.md` - Resumen de Fase 5
- `README.md` - Documentación general del proyecto

---

## 🎯 SIGUIENTE ACCIÓN INMEDIATA

**EJECUTA ESTE COMANDO AHORA:**

```powershell
cd c:\Users\gm_me\GalaxyParlay
grep -r "fetch" apps/web/app/ | Select-String "api"
```

**Una vez encuentres el archivo con el fetch:**

1. Ábrelo en VS Code
2. Localiza la línea con el `fetch()`
3. Verifica la URL que está usando
4. Compárala con: `https://galaxyparlay-production.up.railway.app/api/fixtures?status=NS&limit=100`
5. Corrige si es diferente
6. Guarda el archivo
7. Prueba localmente con `pnpm dev`
8. Si funciona, haz commit y push

---

## 📊 PROGRESO DEL PROYECTO

### Fases Completadas:

- ✅ Fase 1: Modelo de predicción multi-mercado
- ✅ Fase 2: Integración de frontend
- ✅ Fase 3: Deploy a producción (Railway + Vercel)
- ✅ Fase 4: Sistema de background automático (Scheduler)
- ✅ Fase 5: FIFA scraper y mejoras de calidad

### Fase Actual:

- 🔄 **Fase 6: Debugging y optimización**
  - Subtarea actual: Corregir visualización de fixtures en frontend

### Próximas Fases:

- ⏳ Fase 7: Sistema de alertas y notificaciones
- ⏳ Fase 8: Análisis de resultados y mejora continua del modelo
- ⏳ Fase 9: Monetización y escalabilidad

---

## 💡 TIPS FINALES

1. **Usa DevTools del navegador** - Network tab te mostrará exactamente qué endpoint se está llamando
2. **Console.log es tu amigo** - Agrega logs para ver qué datos llegan del backend
3. **Verifica la estructura de datos** - Asegúrate de que `data.fixtures` es un array
4. **Prueba con Postman/curl** - Verifica el endpoint del backend antes de usarlo en frontend
5. **Lee los errores** - Los mensajes de error suelen indicar exactamente qué está mal

---

**¡Buena suerte! El sistema está 95% completo. Solo falta conectar correctamente el frontend al backend que ya funciona perfecto.**

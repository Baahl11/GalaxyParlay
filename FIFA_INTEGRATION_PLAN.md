# 🎯 FIFA INTEGRATION ROADMAP

**Plan de Integración Completa de FIFA Stats en Sistema de Predicciones**

---

## 📊 MAPEO: FIFA Stats → Betting Markets

### 1. **CORNERS** (Over/Under 7.5, 8.5, 9.5, 10.5, 11.5, 12.5)

#### FIFA Stats a Utilizar:

```python
# Attack pressure (más ataques = más corners)
- avg_attack: Equipos 85+ attack → +1.2 corners
- avg_pace: Pace 85+ → +0.8 corners (ataques rápidos, más presión)

# Height advantage (equipos altos ganan más corners defensivos)
- avg_height: Diferencia >5cm → +0.5 corners para equipo más bajo (más saques de esquina contra)

# Technical quality (más dribblings = más corners)
- avg_skill_moves: 3.5+ skill → +0.6 corners (más regates exitosos)
- avg_dribbling: 85+ → +0.5 corners

# Playing style
- physical_advantage: Equipo más físico → -0.4 corners (menos finesse, más fuerza)
```

#### Fórmula Integrada:

```python
base_corners = dixon_coles_prediction(home, away)

# FIFA adjustments
home_fifa = get_team_ratings(home_team)
away_fifa = get_team_ratings(away_team)

fifa_corner_boost = (
    (home_fifa.avg_pace - 80) * 0.08 +  # Pace effect
    (away_fifa.avg_pace - 80) * 0.08 +
    (home_fifa.avg_skill_moves - 2.5) * 0.4 +  # Technical
    (away_fifa.avg_skill_moves - 2.5) * 0.4 +
    height_disadvantage * 0.5  # Height effect
)

final_corners = base_corners + fifa_corner_boost
```

---

### 2. **1X2 (MATCH WINNER)** - Home/Draw/Away

#### FIFA Stats a Utilizar:

```python
# Overall quality gap (dominio claro)
- quality_advantage: >5 points → 15% boost to favorite probability
- quality_advantage: >8 points → 25% boost to favorite probability

# Star player impact (jugadores 85+ rating)
- star_players_count: 5+ stars vs 2- stars → +8% win probability

# Squad value (depth matters for injuries/subs)
- total_value_millions: Diferencia >€300M → +5% win probability

# Age/Experience (big matches)
- avg_age: >28 años vs <25 → +3% in high-pressure games (CL, derbies)

# Home advantage modifier
- physical: Equipo más físico en casa → +2% home win probability
```

#### Fórmula Integrada:

```python
# Base Dixon-Coles probabilities
p_home, p_draw, p_away = dixon_coles.predict_match(home_id, away_id)

# FIFA quality adjustment
quality_gap = home_fifa.avg_overall - away_fifa.avg_overall

if quality_gap > 5:
    # Boost favorite, reduce draw/underdog
    boost_factor = min(0.25, quality_gap * 0.03)  # Max 25% boost
    p_home += boost_factor * p_draw  # Steal from draw
    p_draw *= (1 - boost_factor)

# Star player impact
star_gap = home_fifa.star_players_count - away_fifa.star_players_count
if star_gap > 3:
    p_home += 0.05  # +5% with star advantage
    p_away -= 0.05

# Normalize
total = p_home + p_draw + p_away
p_home, p_draw, p_away = p_home/total, p_draw/total, p_away/total
```

---

### 3. **OVER/UNDER GOALS** (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)

#### FIFA Stats a Utilizar:

```python
# Attack vs Defense mismatch (high-scoring indicator)
- attack_advantage > 6: Over 2.5 gets +12% probability
- attack_advantage < -6: Under 1.5 gets +10% probability

# Combined attack strength (both teams score)
- avg_attack (home + away) > 175: Over 2.5 gets +8%
- avg_attack (home + away) < 155: Under 1.5 gets +10%

# Pace factor (fast games = more goals)
- avg_pace (combined) > 170: Over 2.5 gets +6%
- avg_pace (combined) < 160: Under 2.5 gets +5%

# Defense solidity
- avg_defense > 86: Under 1.5 gets +8% (hard to score against)

# Young attackers (explosive potential)
- avg_age < 25 with attack > 85: Over 2.5 gets +4%
```

#### Fórmula Integrada:

```python
# Base Poisson lambdas
home_lambda, away_lambda = dixon_coles.predict_lambdas(home_id, away_id)

# FIFA attack boost
home_attack_factor = (home_fifa.avg_attack - 80) / 80  # Normalized
away_attack_factor = (away_fifa.avg_attack - 80) / 80

home_lambda *= (1 + home_attack_factor * 0.15)  # Max 15% boost
away_lambda *= (1 + away_attack_factor * 0.15)

# FIFA defense adjustment
home_defense_factor = (away_fifa.avg_defense - 80) / 80  # Opponent defense
away_defense_factor = (home_fifa.avg_defense - 80) / 80

home_lambda *= (1 - home_defense_factor * 0.12)  # Max 12% reduction
away_lambda *= (1 - away_defense_factor * 0.12)

# Pace modifier (fast game = more chances)
combined_pace = (home_fifa.avg_pace + away_fifa.avg_pace) / 2
if combined_pace > 85:
    pace_boost = (combined_pace - 85) * 0.01
    home_lambda *= (1 + pace_boost)
    away_lambda *= (1 + pace_boost)

# Calculate probabilities
total_goals = home_lambda + away_lambda
p_over_2_5 = calculate_poisson_probability(total_goals, '>2.5')
```

---

### 4. **CARDS** (Over/Under 2.5, 3.5, 4.5, 5.5, 6.5)

#### FIFA Stats a Utilizar:

```python
# Physical mismatch (más choques = más tarjetas)
- physical_advantage > 5: +0.6 cards
- physical_advantage < -5: +0.6 cards (ambos casos conflictivos)

# Skill moves vs physical (técnico vs bruto)
- skill_moves_gap > 1.5: +0.8 cards (defensores frustrados)

# Pace differential (juego rápido = más faltas)
- pace_advantage > 8: +0.5 cards (faltas tácticas para frenar)

# Age factor (jugadores jóvenes menos disciplinados)
- avg_age < 25: +0.4 cards (menos experiencia)
- avg_age > 30: -0.3 cards (más disciplina)

# Work rate (H/H teams cometen más faltas)
- Calcular % de jugadores con H/H work rate → cada 10% = +0.2 cards
```

#### Fórmula Integrada:

```python
base_cards = referee_average * league_factor  # Baseline

# FIFA physical clash
physical_mismatch = abs(home_fifa.avg_physical - away_fifa.avg_physical)
if physical_mismatch > 5:
    base_cards += 0.6

# Technical vs Physical clash
skill_gap = abs(home_fifa.avg_skill_moves - away_fifa.avg_skill_moves)
if skill_gap > 1.5:
    base_cards += 0.8  # Frustration fouls

# Pace-based tactical fouls
pace_gap = abs(home_fifa.avg_pace - away_fifa.avg_pace)
if pace_gap > 8:
    base_cards += 0.5

# Age discipline factor
combined_age = (home_fifa.avg_age + away_fifa.avg_age) / 2
if combined_age < 25:
    base_cards += 0.4
elif combined_age > 30:
    base_cards -= 0.3

final_cards = base_cards
```

---

### 5. **SHOTS ON TARGET** (Over/Under 6.5, 7.5, 8.5, 9.5, 10.5)

#### FIFA Stats a Utilizar:

```python
# Shooting accuracy
- avg_shooting > 85: +1.2 shots on target
- avg_shooting < 75: -0.8 shots on target

# Attack pressure
- avg_attack > 88: +1.5 SOT (elite attackers)

# Pace (más ataques = más tiros)
- avg_pace > 85: +1.0 SOT

# Skill moves (dribblings = tiros)
- avg_skill_moves > 3.5: +0.8 SOT
```

---

### 6. **OFFSIDES** (Over/Under 3.5, 4.5, 5.5, 6.5)

#### FIFA Stats a Utilizar:

```python
# Pace (jugadores rápidos = más offsides)
- avg_pace > 85: +1.2 offsides
- avg_pace < 78: -0.8 offsides

# Young attackers (menos timing)
- avg_age < 24 with pace > 85: +1.5 offsides

# Skill moves (dribblers = menos offsides, pasan más)
- avg_skill_moves > 3.5: -0.6 offsides
```

---

### 7. **BTTS (Both Teams to Score)** - Yes/No

#### FIFA Stats a Utilizar:

```python
# Both teams with strong attack
if home_fifa.avg_attack > 82 AND away_fifa.avg_attack > 82:
    btts_yes_probability += 0.15

# Both teams with weak defense
if home_fifa.avg_defense < 78 AND away_fifa.avg_defense < 78:
    btts_yes_probability += 0.12

# Quality mismatch (one team dominates)
if abs(quality_advantage) > 8:
    btts_no_probability += 0.10  # One-sided game
```

---

## 🎮 PLAYER PROPS - ¿QUÉ NECESITAMOS?

### ❌ **LO QUE NO TENEMOS:**

```
❌ Datos de jugadores individuales específicos
   - Haaland, Salah, Mbappé, etc.
   - Goals per game individual
   - Shots per game individual
   - Assists, passes, tackles per game

❌ Form reciente del jugador
   - Last 5 games performance
   - Hot/cold streaks

❌ Matchup específico jugador vs defensa
   - Haaland vs Arsenal defense histórico
```

### ✅ **LO QUE SÍ TENEMOS (y podemos usar):**

```python
# Team-level player props (aproximaciones)
- Top Player Rating: Identificar estrella del equipo
- Star Players Count: Probabilidad de gol de estrella
- Avg Shooting: Calidad de finalizadores
- Avg Skill Moves: Jugadores con alta probabilidad de asistir

# Ejemplo de uso:
if team.top_player_rating >= 90:
    # Probablemente Haaland, Mbappé, Salah nivel
    anytime_goalscorer_probability = 0.65  # Alta
elif team.star_players_count >= 5:
    # Varios jugadores peligrosos
    first_goalscorer_spread = "balanced"  # No clear favorite
else:
    # Team goal focus
    anytime_goalscorer_probability = 0.45  # Menor individual
```

### 🔮 **PARA PROPS REALES NECESITAMOS:**

**Opción 1: API-Football Player Stats**

```python
# API-Football tiene endpoint: /players
# Devuelve por jugador:
- goals, assists (season)
- shots_on_target, shots_total
- passes, dribbles
- minutes_played, games_started

# Cost: 1 request per player = 22 players per game = cara
```

**Opción 2: Web Scraping - FBref.com**

```python
# FBref tiene stats detalladas:
- Expected goals (xG) per player
- Shot conversion rate
- Key passes, expected assists (xA)
- Defensive actions

# FREE pero requiere scraping
```

**Opción 3: Database Manual - Top 100 Players**

```python
# Crear database de top 100 players manualmente
# Stats desde Transfermarkt + Whoscored
# Update semanal

TOP_PLAYERS = {
    'Erling Haaland': {
        'team': 'Manchester City',
        'position': 'ST',
        'goals_per_game': 0.94,  # Insane
        'shots_per_game': 4.2,
        'anytime_scorer_prob': 0.68,
        'first_scorer_prob': 0.28
    },
    'Mohamed Salah': {
        'team': 'Liverpool',
        'position': 'RW',
        'goals_per_game': 0.72,
        'shots_per_game': 3.8,
        'assists_per_game': 0.45,
        'anytime_scorer_prob': 0.58
    },
    # ... 98 more players
}
```

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### **FASE 1: Core Markets (Esta sesión)**

```bash
1. ✅ FIFA Database creado (100+ teams)
2. ⏳ Integrar en dixon_coles.py (1X2, Over/Under Goals)
3. ⏳ Integrar en multi_market_predictor.py (Corners, Cards, Shots, Offsides)
4. ⏳ Validation backtest (medir accuracy improvement)
```

### **FASE 2: Player Props (Next week)**

```bash
1. Crear top_players_database.py (100 jugadores elite)
2. Scraper de FBref.com para stats actualizadas
3. Player props predictor (Anytime Scorer, First Scorer, Assists)
4. Integration en galaxy_api.py (nuevos endpoints)
```

### **FASE 3: Advanced Features (Future)**

```bash
1. Formation analysis (4-3-3 vs 4-4-2 matchups)
2. Manager tactics integration
3. Injury/suspension real-time impact
4. Weather conditions (FIFA physical stats + rain)
```

---

## 📝 CÓDIGO DE INTEGRACIÓN (Ejemplos)

### **Example 1: dixon_coles.py - FIFA Quality Boost**

```python
def predict_match(self, home_team_id, away_team_id, league_id):
    # Existing Dixon-Coles prediction
    p_home, p_draw, p_away = self._calculate_base_probabilities(...)

    # NEW: FIFA integration
    from app.services.fifa_scraper import fifa_scraper

    home_team_name = get_team_name(home_team_id)
    away_team_name = get_team_name(away_team_id)

    home_fifa = fifa_scraper.get_team_ratings(home_team_name)
    away_fifa = fifa_scraper.get_team_ratings(away_team_name)

    if home_fifa and away_fifa:
        quality_gap = home_fifa.avg_overall - away_fifa.avg_overall

        # Adjust probabilities based on quality
        if quality_gap > 5:
            boost = min(0.15, quality_gap * 0.02)
            p_home += boost * p_draw
            p_draw *= (1 - boost)

        # Normalize
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home/total, p_draw/total, p_away/total

    return p_home, p_draw, p_away
```

### **Example 2: multi_market_predictor.py - FIFA Corners**

```python
def predict_corners(self, home_team_id, away_team_id):
    # Existing corners prediction
    base_corners = self._calculate_base_corners(...)

    # NEW: FIFA pace/skill boost
    home_fifa = fifa_scraper.get_team_ratings(get_team_name(home_team_id))
    away_fifa = fifa_scraper.get_team_ratings(get_team_name(away_team_id))

    if home_fifa and away_fifa:
        # Pace effect
        pace_boost = (
            (home_fifa.avg_pace - 80) * 0.08 +
            (away_fifa.avg_pace - 80) * 0.08
        )

        # Skill effect
        skill_boost = (
            (home_fifa.avg_skill_moves - 2.5) * 0.4 +
            (away_fifa.avg_skill_moves - 2.5) * 0.4
        )

        # Height disadvantage = more corners against
        height_diff = abs(home_fifa.avg_height - away_fifa.avg_height)
        height_boost = (height_diff / 10) * 0.5 if height_diff > 5 else 0

        final_corners = base_corners + pace_boost + skill_boost + height_boost

    return final_corners
```

---

## 📊 EXPECTED ACCURACY IMPROVEMENTS

```
Market              Current    With FIFA    Improvement
---------------------------------------------------------
1X2 (Match Winner)    68%        71-73%      +3-5%
Over/Under Goals      71%        74-76%      +3-5%
Corners              68%        72-74%      +4-6%
Cards                64%        70-74%      +6-10% 🔥
Shots on Target      69%        72-74%      +3-5%
Offsides             66%        69-71%      +3-5%
BTTS                 70%        73-75%      +3-5%

OVERALL              68.7%      72-74%      +3.3-5.3%
```

**Cards = BIGGEST IMPACT** porque FIFA physical/skill/age stats son MUY predictivos de discipline

---

## ✅ NEXT STEPS

1. **Implementar integraciones** en dixon_coles.py y multi_market_predictor.py
2. **Run validation backtest** (cuando API resetee)
3. **Medir accuracy improvements** por market
4. **Iterate**: Ajustar weights de FIFA features basado en backtest results
5. **Player Props Phase**: Crear top_players_database.py

¿Empezamos con la implementación de Fase 1?

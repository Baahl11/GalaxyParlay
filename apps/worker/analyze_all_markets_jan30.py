"""
Análisis COMPLETO de Predicciones del 30 de Enero 2026
Analiza los 35 mercados disponibles
"""

import json
import os
from datetime import datetime

from app.services.database import db_service


def analyze_all_markets():
    print("=" * 80)
    print("ANÁLISIS COMPLETO - TODOS LOS MERCADOS - 30 DE ENERO 2026")
    print("=" * 80)

    # 1. Obtener fixtures del 30 de enero con resultados
    print("\n1️⃣ Cargando fixtures del 30 de enero...")
    fixtures_response = (
        db_service.client.table("fixtures")
        .select(
            "id,kickoff_time,home_team_name,away_team_name,home_score,away_score,status,"
            + "corners_home,corners_away,cards_home,cards_away,"
            + "shots_on_target_home,shots_on_target_away,offsides_home,offsides_away,"
            + "half_time_home_score,half_time_away_score"
        )
        .gte("kickoff_time", "2026-01-30T00:00:00")
        .lt("kickoff_time", "2026-01-31T00:00:00")
        .execute()
    )

    all_fixtures = fixtures_response.data
    print(f"   Total fixtures del día: {len(all_fixtures)}")

    # Filtrar solo finalizados
    finished_fixtures = [f for f in all_fixtures if f.get("status") == "FT"]
    print(f"   Partidos finalizados: {len(finished_fixtures)}")

    if not finished_fixtures:
        print("\n⚠️  No hay partidos finalizados aún. Esperando resultados...")
        return

    # 2. Obtener predicciones para esos fixtures
    print("\n2️⃣ Cargando predicciones...")
    fixture_ids = [f["id"] for f in finished_fixtures]
    predictions_response = (
        db_service.client.table("model_predictions")
        .select("fixture_id,market_key,prediction,confidence_score,quality_grade")
        .in_("fixture_id", fixture_ids)
        .execute()
    )

    predictions = predictions_response.data
    print(f"   Total predicciones: {len(predictions)}")

    # Agrupar predicciones por fixture
    predictions_by_fixture = {}
    for pred in predictions:
        fid = pred["fixture_id"]
        if fid not in predictions_by_fixture:
            predictions_by_fixture[fid] = []
        predictions_by_fixture[fid].append(pred)

    # 3. Analizar aciertos por mercado
    print("\n3️⃣ Analizando aciertos por mercado...")

    market_stats = {}

    for fixture in finished_fixtures:
        fid = fixture["id"]
        preds = predictions_by_fixture.get(fid, [])

        for pred in preds:
            market_key = pred["market_key"]
            prediction_probs = pred["prediction"]

            if not prediction_probs:
                continue

            if market_key not in market_stats:
                market_stats[market_key] = {"total": 0, "correct": 0, "examples": []}

            best_prediction = max(prediction_probs.items(), key=lambda x: x[1])[0]
            best_confidence = prediction_probs[best_prediction]

            market_stats[market_key]["total"] += 1

            is_correct = check_prediction(fixture, market_key, best_prediction)

            # Solo contar si pudimos verificar (no es None)
            if is_correct is None:
                # No podemos verificar este mercado sin datos adicionales
                continue

            if is_correct:
                market_stats[market_key]["correct"] += 1
                if len(market_stats[market_key]["examples"]) < 3:
                    market_stats[market_key]["examples"].append(
                        {
                            "home": fixture["home_team_name"],
                            "away": fixture["away_team_name"],
                            "prediction": best_prediction,
                            "confidence": best_confidence,
                            "grade": pred.get("quality_grade", "N/A"),
                        }
                    )

    # 4. Mostrar resultados
    print("\n" + "=" * 80)
    print("📊 RESULTADOS POR MERCADO")
    print("=" * 80)

    total_preds = sum(s["total"] for s in market_stats.values())
    total_correct = sum(s["correct"] for s in market_stats.values())

    print(
        f"\n🎯 PRECISIÓN GENERAL: {total_correct}/{total_preds} = {(total_correct/total_preds*100):.1f}%"
    )

    # Ordenar por número de predicciones
    sorted_markets = sorted(market_stats.items(), key=lambda x: -x[1]["total"])

    print("\n📈 TODOS LOS MERCADOS:")
    print("-" * 80)

    # Agrupar por categoría
    categories = {
        "Resultado del Partido": ["match_winner"],
        "Goles Totales (Over/Under)": [
            k
            for k, _ in sorted_markets
            if k.startswith("over_under_")
            and not any(x in k for x in ["corners", "cards", "shots", "offsides"])
        ],
        "Goles por Equipo": [k for k, _ in sorted_markets if "team_over_under" in k],
        "Primera Mitad": [k for k, _ in sorted_markets if "first_half" in k],
        "Ambos Anotan (BTTS)": [k for k, _ in sorted_markets if k == "both_teams_score"],
        "Corners": [k for k, _ in sorted_markets if "corners" in k],
        "Tarjetas": [k for k, _ in sorted_markets if "cards" in k],
        "Tiros al Arco": [k for k, _ in sorted_markets if "shots_on_target" in k],
        "Fuera de Juego": [k for k, _ in sorted_markets if "offsides" in k],
    }

    for category, markets in categories.items():
        matching_markets = [(k, v) for k, v in sorted_markets if k in markets]
        if matching_markets:
            print(f"\n{'='*80}")
            print(f"📌 {category}")
            print(f"{'='*80}")

            for market_key, data in matching_markets:
                if data["total"] > 0:
                    accuracy = (data["correct"] / data["total"]) * 100
                    status = "✅" if accuracy >= 55 else "⚠️" if accuracy >= 50 else "❌"
                    print(f"\n{status} {market_key.replace('_', ' ').upper()}")
                    print(f"   Predicciones: {data['total']}")
                    print(f"   Aciertos: {data['correct']}")
                    print(f"   Precisión: {accuracy:.1f}%")

                    if data["examples"] and accuracy >= 55:
                        print(f"   Ejemplo:")
                        ex = data["examples"][0]
                        print(
                            f"      ✓ {ex['home']} vs {ex['away']} → {ex['prediction']} ({ex['confidence']:.1%}) [Grade: {ex['grade']}]"
                        )

    # 5. Análisis por grado de calidad
    print("\n" + "=" * 80)
    print("⭐ ANÁLISIS POR GRADO DE CALIDAD (TODOS LOS MERCADOS)")
    print("=" * 80)

    grade_stats = {
        "A": {"total": 0, "correct": 0},
        "B": {"total": 0, "correct": 0},
        "C": {"total": 0, "correct": 0},
        "D": {"total": 0, "correct": 0},
    }

    for fixture in finished_fixtures:
        fid = fixture["id"]
        preds = predictions_by_fixture.get(fid, [])

        for pred in preds:
            grade = pred.get("quality_grade", "D")
            if grade not in grade_stats:
                grade_stats[grade] = {"total": 0, "correct": 0}

            market_key = pred["market_key"]
            prediction_probs = pred["prediction"]

            if not prediction_probs:
                continue

            best_prediction = max(prediction_probs.items(), key=lambda x: x[1])[0]
            grade_stats[grade]["total"] += 1

            is_correct = check_prediction(fixture, market_key, best_prediction)

            # Solo contar si pudimos verificar
            if is_correct is None:
                continue

            if is_correct:
                grade_stats[grade]["correct"] += 1

    for grade in ["A", "B", "C", "D"]:
        if grade in grade_stats and grade_stats[grade]["total"] > 0:
            data = grade_stats[grade]
            accuracy = (data["correct"] / data["total"]) * 100
            status = "✅" if accuracy >= 55 else "⚠️" if accuracy >= 50 else "❌"
            print(f"\n{status} Grade {grade}:")
            print(f"   Total: {data['total']}")
            print(f"   Aciertos: {data['correct']}")
            print(f"   Precisión: {accuracy:.1f}%")

    # 6. Top 10 mejores mercados
    print("\n" + "=" * 80)
    print("🏆 TOP 10 MEJORES MERCADOS")
    print("=" * 80)

    markets_with_accuracy = [
        (k, v, (v["correct"] / v["total"] * 100) if v["total"] > 0 else 0)
        for k, v in market_stats.items()
    ]
    top_markets = sorted(markets_with_accuracy, key=lambda x: -x[2])[:10]

    for i, (market, data, accuracy) in enumerate(top_markets, 1):
        print(f"\n{i}. {market.replace('_', ' ').upper()}")
        print(f"   Precisión: {accuracy:.1f}% ({data['correct']}/{data['total']})")

    print("\n" + "=" * 80)
    print("✅ Análisis completado")
    print("=" * 80)


def check_prediction(fixture, market_key, prediction):
    """Verifica si una predicción fue correcta según el mercado"""

    home_score = fixture.get("home_score")
    away_score = fixture.get("away_score")

    if home_score is None or away_score is None:
        return False

    total_goals = home_score + away_score

    # Match Winner
    if market_key == "match_winner":
        if prediction == "home_win":
            return home_score > away_score
        elif prediction == "away_win":
            return away_score > home_score
        elif prediction == "draw":
            return home_score == away_score

    # Over/Under Goals
    elif market_key.startswith("over_under_"):
        line = float(market_key.split("_")[-1].replace("_", "."))
        if prediction == "over":
            return total_goals > line
        elif prediction == "under":
            return total_goals < line

    # Home Team Goals
    elif market_key.startswith("home_team_over_under_"):
        line = float(market_key.split("_")[-1].replace("_", "."))
        if prediction == "over":
            return home_score > line
        elif prediction == "under":
            return home_score < line

    # Away Team Goals
    elif market_key.startswith("away_team_over_under_"):
        line = float(market_key.split("_")[-1].replace("_", "."))
        if prediction == "over":
            return away_score > line
        elif prediction == "under":
            return away_score < line

    # First Half
    elif market_key.startswith("first_half_"):
        ht_home = fixture.get("half_time_home_score")
        ht_away = fixture.get("half_time_away_score")
        if ht_home is None or ht_away is None:
            return None

        line = float(market_key.split("_")[-1].replace("_", "."))
        ht_total = ht_home + ht_away

        if prediction == "over":
            return ht_total > line
        elif prediction == "under":
            return ht_total < line

    # BTTS
    elif market_key == "both_teams_score":
        btts_happened = home_score > 0 and away_score > 0
        if prediction == "yes":
            return btts_happened
        elif prediction == "no":
            return not btts_happened

    # Corners
    elif market_key.startswith("corners_over_under_"):
        corners_home = fixture.get("corners_home")
        corners_away = fixture.get("corners_away")
        if corners_home is None or corners_away is None:
            return None

        total_corners = corners_home + corners_away
        line = float(market_key.split("_")[-1].replace("_", "."))

        if prediction == "over":
            return total_corners > line
        elif prediction == "under":
            return total_corners < line

    # Cards
    elif market_key.startswith("cards_over_under_"):
        cards_home = fixture.get("cards_home")
        cards_away = fixture.get("cards_away")
        if cards_home is None or cards_away is None:
            return None

        total_cards = cards_home + cards_away
        line = float(market_key.split("_")[-1].replace("_", "."))

        if prediction == "over":
            return total_cards > line
        elif prediction == "under":
            return total_cards < line

    # Shots on Target
    elif market_key.startswith("shots_on_target_over_under_"):
        shots_home = fixture.get("shots_on_target_home")
        shots_away = fixture.get("shots_on_target_away")
        if shots_home is None or shots_away is None:
            return None

        total_shots = shots_home + shots_away
        line = float(market_key.split("_")[-1].replace("_", "."))

        if prediction == "over":
            return total_shots > line
        elif prediction == "under":
            return total_shots < line

    # Offsides
    elif market_key.startswith("offsides_over_under_"):
        offsides_home = fixture.get("offsides_home")
        offsides_away = fixture.get("offsides_away")
        if offsides_home is None or offsides_away is None:
            return None

        total_offsides = offsides_home + offsides_away
        line = float(market_key.split("_")[-1].replace("_", "."))

        if prediction == "over":
            return total_offsides > line
        elif prediction == "under":
            return total_offsides < line

    return None


if __name__ == "__main__":
    analyze_all_markets()

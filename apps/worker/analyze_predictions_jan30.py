"""
Análisis de Predicciones del 30 de Enero 2026
Compara predicciones vs resultados reales
"""

import json
import os
from datetime import datetime

from app.services.database import db_service


def analyze_predictions():
    print("=" * 80)
    print("ANÁLISIS DE PREDICCIONES - 30 DE ENERO 2026")
    print("=" * 80)

    # 1. Obtener fixtures del 30 de enero con resultados
    print("\n1️⃣ Cargando fixtures del 30 de enero...")
    fixtures_response = (
        db_service.client.table("fixtures")
        .select("id,kickoff_time,home_team_name,away_team_name,home_score,away_score,status")
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

    # 3. Analizar aciertos por tipo de mercado
    print("\n3️⃣ Analizando aciertos...")

    stats = {
        "match_winner": {"total": 0, "correct": 0, "fixtures": []},
        "over_under_2.5": {"total": 0, "correct": 0, "fixtures": []},
        "btts": {"total": 0, "correct": 0, "fixtures": []},
        "double_chance": {"total": 0, "correct": 0, "fixtures": []},
    }

    for fixture in finished_fixtures:
        fid = fixture["id"]
        home_score = fixture.get("home_score")
        away_score = fixture.get("away_score")

        if home_score is None or away_score is None:
            continue

        preds = predictions_by_fixture.get(fid, [])

        for pred in preds:
            market_key = pred["market_key"]
            prediction_probs = pred["prediction"]  # JSONB con probabilidades

            # Obtener la predicción con mayor probabilidad
            if not prediction_probs:
                continue

            best_prediction = max(prediction_probs.items(), key=lambda x: x[1])[0]

            # Verificar acierto según mercado
            is_correct = False
            market_type = None

            if market_key == "match_winner":
                market_type = "match_winner"
                if best_prediction == "home_win" and home_score > away_score:
                    is_correct = True
                elif best_prediction == "away_win" and away_score > home_score:
                    is_correct = True
                elif best_prediction == "draw" and home_score == away_score:
                    is_correct = True

            elif "over_under" in market_key:
                market_type = "over_under_2.5"
                total_goals = home_score + away_score
                if best_prediction == "over" and total_goals > 2.5:
                    is_correct = True
                elif best_prediction == "under" and total_goals < 2.5:
                    is_correct = True

            elif market_key == "btts":
                market_type = "btts"
                btts_happened = home_score > 0 and away_score > 0
                if best_prediction == "yes" and btts_happened:
                    is_correct = True
                elif best_prediction == "no" and not btts_happened:
                    is_correct = True

            elif "double_chance" in market_key:
                market_type = "double_chance"
                if best_prediction == "home_draw" and home_score >= away_score:
                    is_correct = True
                elif best_prediction == "away_draw" and away_score >= home_score:
                    is_correct = True
                elif best_prediction == "home_away" and home_score != away_score:
                    is_correct = True

            if market_type and market_type in stats:
                stats[market_type]["total"] += 1

                if is_correct:
                    stats[market_type]["correct"] += 1
                    stats[market_type]["fixtures"].append(
                        {
                            "home": fixture["home_team_name"],
                            "away": fixture["away_team_name"],
                            "score": f"{home_score}-{away_score}",
                            "prediction": best_prediction,
                            "confidence": prediction_probs.get(best_prediction, 0),
                            "grade": pred.get("quality_grade", "N/A"),
                        }
                    )

    # 4. Mostrar resultados
    print("\n" + "=" * 80)
    print("📊 RESULTADOS")
    print("=" * 80)

    total_preds = sum(s["total"] for s in stats.values())
    total_correct = sum(s["correct"] for s in stats.values())

    print(
        f"\n🎯 PRECISIÓN GENERAL: {total_correct}/{total_preds} = {(total_correct/total_preds*100):.1f}%"
    )

    print("\n📈 DESGLOSE POR MERCADO:")
    print("-" * 80)

    for market_type, data in stats.items():
        if data["total"] > 0:
            accuracy = (data["correct"] / data["total"]) * 100
            print(f"\n{market_type.upper().replace('_', ' ')}")
            print(f"   Predicciones: {data['total']}")
            print(f"   Aciertos: {data['correct']}")
            print(f"   Precisión: {accuracy:.1f}%")

            if data["fixtures"]:
                print(f"   Ejemplos de aciertos (primeros 3):")
                for example in data["fixtures"][:3]:
                    conf = example.get("confidence", 0)
                    print(
                        f"      ✓ {example['home']} vs {example['away']} ({example['score']}) - {example['prediction']} ({conf:.1%}) [Grade: {example['grade']}]"
                    )

    # 5. Análisis por calidad
    print("\n" + "=" * 80)
    print("⭐ ANÁLISIS POR GRADO DE CALIDAD")
    print("=" * 80)

    grade_stats = {
        "A": {"total": 0, "correct": 0},
        "B": {"total": 0, "correct": 0},
        "C": {"total": 0, "correct": 0},
    }

    for fixture in finished_fixtures:
        fid = fixture["id"]
        home_score = fixture.get("home_score")
        away_score = fixture.get("away_score")

        if home_score is None or away_score is None:
            continue

        preds = predictions_by_fixture.get(fid, [])

        for pred in preds:
            grade = pred.get("quality_grade", "C")
            if grade not in grade_stats:
                continue

            market_key = pred["market_key"]
            prediction_probs = pred["prediction"]

            if not prediction_probs:
                continue

            best_prediction = max(prediction_probs.items(), key=lambda x: x[1])[0]
            grade_stats[grade]["total"] += 1

            is_correct = False

            # Match Winner
            if market_key == "match_winner":
                if best_prediction == "home_win" and home_score > away_score:
                    is_correct = True
                elif best_prediction == "away_win" and away_score > home_score:
                    is_correct = True
                elif best_prediction == "draw" and home_score == away_score:
                    is_correct = True

            # Over/Under
            elif "over_under" in market_key:
                total_goals = home_score + away_score
                if best_prediction == "over" and total_goals > 2.5:
                    is_correct = True
                elif best_prediction == "under" and total_goals < 2.5:
                    is_correct = True

            # BTTS
            elif market_key == "btts":
                btts_happened = home_score > 0 and away_score > 0
                if best_prediction == "yes" and btts_happened:
                    is_correct = True
                elif best_prediction == "no" and not btts_happened:
                    is_correct = True

            # Double Chance
            elif "double_chance" in market_key:
                if best_prediction == "home_draw" and home_score >= away_score:
                    is_correct = True
                elif best_prediction == "away_draw" and away_score >= home_score:
                    is_correct = True
                elif best_prediction == "home_away" and home_score != away_score:
                    is_correct = True

            if is_correct:
                grade_stats[grade]["correct"] += 1

    for grade in ["A", "B", "C"]:
        data = grade_stats[grade]
        if data["total"] > 0:
            accuracy = (data["correct"] / data["total"]) * 100
            print(f"\nGrade {grade}:")
            print(f"   Total: {data['total']}")
            print(f"   Aciertos: {data['correct']}")
            print(f"   Precisión: {accuracy:.1f}%")

    print("\n" + "=" * 80)
    print("✅ Análisis completado")
    print("=" * 80)


if __name__ == "__main__":
    analyze_predictions()

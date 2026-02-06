"""
AI Match Analysis using Claude Haiku

Generates intelligent narrative analysis for betting predictions
combining all model outputs into a coherent summary.
"""
from typing import Dict, List, Any, Optional
import httpx
import os
import structlog

logger = structlog.get_logger()

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
HAIKU_MODEL = "claude-3-5-haiku-20241022"


async def generate_match_analysis(
    fixture: Dict[str, Any],
    elo_data: Optional[Dict[str, Any]] = None,
    dixon_coles: Optional[Dict[str, Any]] = None,
    value_bets: Optional[List[Dict[str, Any]]] = None,
    kelly_results: Optional[Dict[str, Any]] = None,
    language: str = "es"
) -> str:
    """
    Generate AI-powered match analysis using Claude Haiku.
    
    Args:
        fixture: Fixture data (teams, kickoff, etc.)
        elo_data: Elo ratings for both teams
        dixon_coles: Dixon-Coles prediction
        value_bets: Value betting opportunities
        kelly_results: Kelly Criterion bet sizing
        language: Output language ("es" for Spanish, "en" for English)
        
    Returns:
        Narrative analysis text
    """
    if not ANTHROPIC_API_KEY:
        return _generate_fallback_analysis(fixture, dixon_coles, value_bets, language)
    
    # Build context for the AI
    context = _build_analysis_context(
        fixture, elo_data, dixon_coles, value_bets, kelly_results
    )
    
    # Create prompt
    if language == "es":
        system_prompt = """Eres un analista experto de apuestas deportivas. 
Tu trabajo es proporcionar análisis concisos y útiles basados en datos estadísticos y modelos predictivos.
Responde en español. Sé directo y objetivo. No uses disclaimers legales.
Formato: 2-3 párrafos máximo, enfocándote en las oportunidades de valor."""
    else:
        system_prompt = """You are an expert sports betting analyst.
Your job is to provide concise, useful analysis based on statistical data and predictive models.
Be direct and objective. No legal disclaimers.
Format: 2-3 paragraphs max, focusing on value opportunities."""
    
    user_prompt = f"""Analiza este partido basándote en los siguientes datos:

{context}

Proporciona:
1. Un resumen rápido del enfrentamiento
2. Las mejores oportunidades de apuesta según los modelos
3. Una recomendación clara (si hay value bet o no)"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": HAIKU_MODEL,
                    "max_tokens": 500,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                logger.warning("Haiku API error", status=response.status_code)
                return _generate_fallback_analysis(fixture, dixon_coles, value_bets, language)
                
    except Exception as e:
        logger.error("Haiku analysis failed", error=str(e))
        return _generate_fallback_analysis(fixture, dixon_coles, value_bets, language)


def _build_analysis_context(
    fixture: Dict[str, Any],
    elo_data: Optional[Dict[str, Any]],
    dixon_coles: Optional[Dict[str, Any]],
    value_bets: Optional[List[Dict[str, Any]]],
    kelly_results: Optional[Dict[str, Any]]
) -> str:
    """Build context string for AI analysis."""
    lines = []
    
    # Match info
    home = fixture.get('home_team_name', 'Local')
    away = fixture.get('away_team_name', 'Visitante')
    lines.append(f"**Partido:** {home} vs {away}")
    lines.append(f"**Liga:** {fixture.get('league_id', 'N/A')}")
    
    # Elo ratings
    if elo_data:
        home_elo = elo_data.get('home_elo', 1500)
        away_elo = elo_data.get('away_elo', 1500)
        lines.append(f"\n**Elo Ratings:** {home}: {home_elo} | {away}: {away_elo}")
    
    # Dixon-Coles prediction
    if dixon_coles and 'prediction' in dixon_coles:
        pred = dixon_coles['prediction']
        mw = pred.get('match_winner', {})
        lines.append("\n**Dixon-Coles Prediction:**")
        lines.append(f"- Victoria local: {mw.get('home_win', 0):.1%}")
        lines.append(f"- Empate: {mw.get('draw', 0):.1%}")
        lines.append(f"- Victoria visitante: {mw.get('away_win', 0):.1%}")
        
        ou = pred.get('over_under_2_5', {})
        if ou:
            lines.append(f"- Over 2.5: {ou.get('over', 0):.1%}")
        
        btts = pred.get('btts', {})
        if btts:
            lines.append(f"- BTTS: {btts.get('yes', 0):.1%}")
        
        eg = pred.get('expected_goals', {})
        if eg:
            lines.append(f"- Goles esperados: {eg.get('home', 0):.1f} - {eg.get('away', 0):.1f}")
    
    # Value bets
    if value_bets:
        lines.append(f"\n**Value Bets detectadas:** {len(value_bets)}")
        for vb in value_bets[:3]:  # Top 3
            lines.append(f"- {vb.get('market', 'N/A')}: Edge {vb.get('edge', 0):.1%}, EV {vb.get('ev', 0):.1%}")
    
    # Kelly sizing
    if kelly_results:
        lines.append("\n**Kelly Criterion:**")
        for market, result in kelly_results.items():
            if hasattr(result, 'is_value_bet') and result.is_value_bet:
                lines.append(f"- {market}: {result.recommendation}")
    
    return "\n".join(lines)


def _generate_fallback_analysis(
    fixture: Dict[str, Any],
    dixon_coles: Optional[Dict[str, Any]],
    value_bets: Optional[List[Dict[str, Any]]],
    language: str
) -> str:
    """Generate simple analysis without AI when API is unavailable."""
    home = fixture.get('home_team_name', 'Local')
    away = fixture.get('away_team_name', 'Visitante')
    
    if language == "es":
        analysis = f"**{home} vs {away}**\n\n"
        
        if dixon_coles and 'prediction' in dixon_coles:
            pred = dixon_coles['prediction']
            mw = pred.get('match_winner', {})
            
            # Find favorite
            home_prob = mw.get('home_win', 0)
            away_prob = mw.get('away_win', 0)
            
            if home_prob > away_prob:
                favorite = home
                fav_prob = home_prob
            else:
                favorite = away
                fav_prob = away_prob
            
            analysis += f"El modelo Dixon-Coles favorece a **{favorite}** con {fav_prob:.0%} de probabilidad. "
            
            eg = pred.get('expected_goals', {})
            if eg:
                total = eg.get('total', 0)
                if total > 2.5:
                    analysis += f"Se esperan {total:.1f} goles (favorable al Over 2.5). "
                else:
                    analysis += f"Partido con pocos goles esperados ({total:.1f}). "
        
        if value_bets and len(value_bets) > 0:
            best = value_bets[0]
            analysis += f"\n\n**Mejor oportunidad:** {best.get('market', 'N/A')} con edge de {best.get('edge', 0):.1%}."
        else:
            analysis += "\n\nNo se detectaron value bets significativas para este partido."
    else:
        analysis = f"**{home} vs {away}**\n\n"
        analysis += "Analysis generated from model predictions."
    
    return analysis


async def generate_daily_summary(
    matches: List[Dict[str, Any]],
    language: str = "es"
) -> str:
    """
    Generate AI summary for all matches of the day.
    
    Args:
        matches: List of match analysis results
        language: Output language
        
    Returns:
        Daily summary text
    """
    if not ANTHROPIC_API_KEY:
        return _generate_fallback_daily_summary(matches, language)
    
    # Build summary context
    context_lines = [f"Total de partidos: {len(matches)}\n"]
    
    value_bet_count = 0
    top_picks = []
    
    for match in matches:
        fixture = match.get('fixture', {})
        value_bets = match.get('value_bets', [])
        
        if value_bets:
            value_bet_count += len(value_bets)
            best = value_bets[0]
            top_picks.append({
                'match': f"{fixture.get('home_team_name')} vs {fixture.get('away_team_name')}",
                'market': best.get('market'),
                'edge': best.get('edge', 0)
            })
    
    # Sort by edge
    top_picks.sort(key=lambda x: x['edge'], reverse=True)
    
    context_lines.append(f"Value bets encontradas: {value_bet_count}")
    context_lines.append("\nTop picks del día:")
    for pick in top_picks[:5]:
        context_lines.append(f"- {pick['match']}: {pick['market']} (edge {pick['edge']:.1%})")
    
    context = "\n".join(context_lines)
    
    if language == "es":
        system_prompt = """Eres un analista de apuestas deportivas. 
Proporciona un resumen ejecutivo de las mejores oportunidades del día.
Sé conciso y directo. Máximo 3 párrafos."""
    else:
        system_prompt = """You are a sports betting analyst.
Provide an executive summary of the best opportunities of the day.
Be concise and direct. Maximum 3 paragraphs."""
    
    user_prompt = f"Resume las mejores oportunidades de apuesta del día:\n\n{context}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": HAIKU_MODEL,
                    "max_tokens": 600,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                return _generate_fallback_daily_summary(matches, language)
                
    except Exception as e:
        logger.error("Daily summary generation failed", error=str(e))
        return _generate_fallback_daily_summary(matches, language)


def _generate_fallback_daily_summary(matches: List[Dict[str, Any]], language: str) -> str:
    """Generate simple daily summary without AI."""
    total = len(matches)
    value_bets_total = sum(len(m.get('value_bets', [])) for m in matches)
    
    if language == "es":
        return f"""**Resumen del Día**

📊 {total} partidos analizados
🎯 {value_bets_total} value bets detectadas

Los modelos Dixon-Coles y Elo han identificado oportunidades de valor en varios mercados. 
Revisa cada partido individualmente para ver los detalles de las predicciones."""
    else:
        return f"""**Daily Summary**

📊 {total} matches analyzed
🎯 {value_bets_total} value bets detected

Dixon-Coles and Elo models have identified value opportunities across several markets.
Review each match individually for prediction details."""

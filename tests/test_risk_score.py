from app.application.use_cases.calculate_risk_score import CalculateRiskScoreUseCase
from app.application.use_cases.generate_action_recommendations import GenerateActionRecommendationsUseCase


def test_risk_score_for_password_and_email_is_critical():
    result = CalculateRiskScoreUseCase.execute(["password", "email"])

    assert result["pontuacao_total"] == 130
    assert result["nivel_exposicao"] == "Crítico"
    assert len(result["analise_engenharia_social"]) == 2


def test_recommendations_are_actionable_and_deduplicated():
    result = GenerateActionRecommendationsUseCase.execute(["password", "email", "password"])

    titles = [item["title"] for item in result]
    assert "Rotacione credenciais reutilizadas" in titles
    assert "Fortaleça o canal de recuperação de contas" in titles
    assert titles.count("Rotacione credenciais reutilizadas") == 1

from app.application.use_cases.calculate_risk_score import CalculateRiskScoreUseCase
from app.application.use_cases.generate_action_recommendations import GenerateActionRecommendationsUseCase
from app.core.config import settings
from app.core.errors import ServiceUnavailableError


class CheckPhoneUseCase:
    @staticmethod
    async def execute(target_phone: str) -> dict:
        if not settings.ENABLE_PHONE_LOOKUP:
            raise ServiceUnavailableError("Phone lookup desabilitado.")

        if not settings.PHONE_LOOKUP_USE_MOCK:
            raise ServiceUnavailableError("Provider real de telefone não configurado.")

        mock_sites = ["Carrier Exposure Dataset (Mock)", "Messaging App Leak (Mock)"]
        mock_data_types = ["phone", "name"]
        risk_summary = CalculateRiskScoreUseCase.execute(mock_data_types)
        recommendations = GenerateActionRecommendationsUseCase.execute(mock_data_types)

        return {
            "status": "MOCK_SUCCESS",
            "is_leaked": True,
            "sites": mock_sites,
            "leaked_data_types": mock_data_types,
            "risk_score": risk_summary,
            "recommendations": recommendations,
            "action": "[!] CONSULTA DE TELEFONE EM MODO MOCK CONTROLADO",
        }

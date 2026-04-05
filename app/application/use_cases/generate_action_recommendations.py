from typing import List, Dict


class GenerateActionRecommendationsUseCase:
    RECOMMENDATION_RULES = {
        "password": {
            "title": "Rotacione credenciais reutilizadas",
            "priority": "high",
            "description": "Troque senhas expostas, priorize e-mail principal e habilite 2FA por aplicativo autenticador.",
        },
        "senha": {
            "title": "Rotacione credenciais reutilizadas",
            "priority": "high",
            "description": "Troque senhas expostas, priorize e-mail principal e habilite 2FA por aplicativo autenticador.",
        },
        "email": {
            "title": "Fortaleça o canal de recuperação de contas",
            "priority": "medium",
            "description": "Revise filtros anti-phishing, aliases públicos e métodos de recuperação vinculados ao e-mail monitorado.",
        },
        "phone": {
            "title": "Reduza risco de clonagem e vishing",
            "priority": "high",
            "description": "Ative PIN da operadora e verificação em duas etapas em mensageria para dificultar engenharia social.",
        },
        "telefone": {
            "title": "Reduza risco de clonagem e vishing",
            "priority": "high",
            "description": "Ative PIN da operadora e verificação em duas etapas em mensageria para dificultar engenharia social.",
        },
        "cpf": {
            "title": "Monitore fraude de identidade",
            "priority": "high",
            "description": "Acompanhe abertura de contas, validações cadastrais e serviços financeiros associados ao documento exposto.",
        },
    }

    @classmethod
    def execute(cls, leaked_data_types: List[str]) -> List[Dict[str, str]]:
        recommendations: List[Dict[str, str]] = []
        seen_titles = set()

        for data_type in leaked_data_types:
            normalized = data_type.lower().strip()
            for key, payload in cls.RECOMMENDATION_RULES.items():
                if key in normalized and payload["title"] not in seen_titles:
                    recommendations.append(payload)
                    seen_titles.add(payload["title"])

        if not recommendations:
            recommendations.append(
                {
                    "title": "Mantenha monitoramento contínuo",
                    "priority": "low",
                    "description": "Continue monitorando o e-mail e revise periodicamente senhas, 2FA e exposição pública de dados.",
                }
            )

        return recommendations

from typing import List, Dict, Any


class CalculateRiskScoreUseCase:
    RISK_WEIGHTS = {
        "senha": 100,
        "password": 100,
        "cpf": 80,
        "ssn": 80,
        "telefone": 50,
        "phone": 50,
        "celular": 50,
        "endereço": 40,
        "address": 40,
        "email": 30,
        "data de nascimento": 20,
        "dob": 20,
        "nome": 10,
        "name": 10
    }

    SCAM_PSYCHOLOGY = {
        "senha": "O criminoso tentará realizar o 'Credential Stuffing', que consiste em testar essa mesma senha no seu email principal, banco e redes sociais sabendo que usuários reciclam senhas.",
        "password": "O criminoso tentará realizar o 'Credential Stuffing', que consiste em testar essa mesma senha no seu email principal, banco e redes sociais sabendo que usuários reciclam senhas.",
        "cpf": "Abertura de contas digitais falsas, fraudes de financiamento e crime de Roubo de Identidade profunda.",
        "telefone": "Alto risco de Vishing (Golpes por chamada de voz simulando o seu gerente bancário), tentativas de clonagem de WhatsApp e Smishing (SMS maliciosos contendo Phishing).",
        "phone": "Alto risco de Vishing (Golpes por chamada de voz simulando o seu gerente bancário), tentativas de clonagem de WhatsApp e Smishing (SMS maliciosos contendo Phishing).",
        "endereço": "Pode ser utilizado para Doxing (extorsão pública) ou para validar a credibilidade de um golpista em ligações ativas ('Estou vendo que o senhor mora na Rua X').",
        "address": "Pode ser utilizado para Doxing (extorsão pública) ou para validar a credibilidade de um golpista em ligações ativas ('Estou vendo que o senhor mora na Rua X').",
        "email": "Vetores para envio de links maliciosos contínuos. Hackers tentarão direcionar ransomwares ou páginas de captura falsas direto à sua caixa de entrada.",
        "data de nascimento": "Muitas empresas utilizam as datas de nascimento associadas aos últimos quatro dígitos de um cartão ou telefone como 'Chave de Bypass' para resgatar contas por call-center.",
        "nome": "Dados básicos são usados para personalizar os e-mails falsos (Spear Phishing), fazendo parecer que uma companhia legítima está falando diretamente com você."
    }

    @classmethod
    def execute(cls, leaked_data_types: List[str]) -> Dict[str, Any]:
        total_score = 0
        psychological_alerts = []
        processed_types = set()

        for data_type in leaked_data_types:
            normalized_type = data_type.lower().strip()
            weight_applied = 0
            scam_alert = ""

            for key in cls.RISK_WEIGHTS.keys():
                if key in normalized_type and key not in processed_types:
                    weight_applied = cls.RISK_WEIGHTS[key]
                    scam_alert = cls.SCAM_PSYCHOLOGY.get(key, "")
                    processed_types.add(key)
                    break

            if weight_applied == 0:
                weight_applied = 5

            total_score += weight_applied

            if scam_alert:
                psychological_alerts.append({
                    "dado_vazado": data_type,
                    "alerta_psicologico": scam_alert,
                    "pontos_risco": weight_applied
                })

        if total_score < 30:
            exposure_level = "Baixo"
        elif 30 <= total_score < 100:
            exposure_level = "Médio"
        else:
            exposure_level = "Crítico"

        return {
            "pontuacao_total": total_score,
            "nivel_exposicao": exposure_level,
            "analise_engenharia_social": psychological_alerts,
        }

import html
from typing import List

class DigitalHygieneReportGenerator:
    """
    Camada de Casos de Uso (Domínio/Aplicação): 
    Este serviço elabora relatórios customizados no formato HTML com estilização brutalista nativa embutida.
    Ele permite ao frontend receber uma 'String HTML' crua e forçar um download ou um pop-up interativo.
    """
    
    @classmethod
    def generate_html_report(cls, user_name: str, detected_leaks: List[str]) -> str:
        """Gera a estrutura brutalista de Plano de Ação Personalizado."""
        checklist_items = ""
        leaks_joined = " ".join(detected_leaks).lower()
        has_critical = False
        safe_user_name = html.escape(user_name.upper(), quote=True)
        safe_detected_leaks = [html.escape(item, quote=True) for item in detected_leaks]
        
        # Injeção Dinâmica de Lógica (Checklists técnicos embasados no vazamento)
        if any(leak in leaks_joined for leak in ["senha", "password", "email", "credential", "credenciais"]):
            has_critical = True
            checklist_items += cls._build_task(
                "ROTAÇÃO DE CREDENCIAIS DE ALTO IMPACTO",
                "Ativar Autenticação de 2 Fatores (2FA) baseada em TOTP (Google Authenticator/Authy). Descarte SMS. Rotacione senhas de contas listadas nos relatórios HIBP usando um Gerenciador."
            )
        
        if any(leak in leaks_joined for leak in ["telefone", "celular", "whatsapp", "phone"]):
            has_critical = True
            checklist_items += cls._build_task(
                "DEFESA ATIVA CONTRA VISHING E CLONAGEM",
                "Configure o PIN de dupla garantia no seu WhatsApp. Instrua seus contatos familiares próximos que nenhuma emergência médica ou financeira será gerida via mensagem."
            )
            
        if any(leak in leaks_joined for leak in ["gps", "exif", "imagem", "foto", "location"]):
            checklist_items += cls._build_task(
                "DESCONTAMINAÇÃO DE DADOS MÍDIAS (EXIF)",
                "Desativar tags de localização geográfica no seu App nativo de Câmera (OS). Ferramentas OSINT podem mapear sua padronização de trilhas rodoviárias. Processe imagens em lote contra metadados antes de arquivá-las."
            )
            
        # Medidas Preventivas Básicas Injetadas Padrão
        checklist_items += cls._build_task(
            "CRITPOGRAFIA END-TO-END NO SSH",
            "Abandone acesso à servidores e instâncias na nuvem via senhas padrão ou chaves antigas RSA insuficientes. Produza criptografia de Curvas Elípticas gerando chaves 'Ed25519' hoje mesmo."
        )

        template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>PLANO DE AÇÃO: I-SAFE // {safe_user_name}</title>
    <style>
        /* CSS Brutalista Injetado Nativamente para Exportação Desacoplada */
        :root {{
            --bg: #111;
            --text: #fff;
            --accent: #ccff00;
            --danger: #ff003c;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        h1 {{
            font-size: 3.5rem;
            text-transform: uppercase;
            border-bottom: 5px solid var(--text);
            padding-bottom: 1rem;
            text-shadow: 4px 4px 0px var(--danger);
            margin-bottom: 2rem;
        }}
        .leak-list {{
            background: #000;
            border: 4px solid {'var(--danger)' if has_critical else 'var(--accent)'};
            padding: 1.5rem;
            margin-bottom: 3rem;
            box-shadow: 8px 8px 0px {'var(--danger)' if has_critical else 'var(--accent)'};
        }}
        .task-card {{
            background: #000;
            border: 3px dashed var(--text);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            cursor: pointer;
        }}
        .task-card:hover {{
            background: #222;
            border-style: solid;
            border-color: var(--accent);
            box-shadow: 6px 6px 0px var(--accent);
        }}
        input[type="checkbox"] {{
            transform: scale(2);
            margin-right: 20px;
            accent-color: var(--accent);
        }}
        label {{ 
            cursor: pointer; 
            font-weight: 800; 
            font-size: 1.3rem; 
            text-transform: uppercase;
        }}
        p.task-desc {{ 
            margin-left: 3rem; 
            margin-top: 0.5rem;
            font-size: 1rem; 
            opacity: 0.85; 
        }}
        
        button.print-btn {{
            background: var(--text);
            color: #000;
            font-size: 1.5rem;
            padding: 1.5rem;
            font-family: inherit;
            font-weight: 800;
            border: 4px solid #000;
            cursor: pointer;
            text-transform: uppercase;
            margin-top: 3rem;
            width: 100%;
            transition: 0.1s;
        }}
        button.print-btn:hover {{
            background: var(--accent);
            border-color: var(--text);
        }}
        button.print-btn:active {{
            transform: translate(4px, 4px);
        }}

        /* Regras seguras para permitir ao navegador imprimir um PDF Elegante e Fiel */
        @media print {{
            body {{ background-color: #fff; color: #000; }}
            .task-card, .leak-list {{ box-shadow: none; border-color: #000; background: #fff; color: #000; }}
            h1 {{ text-shadow: none; }}
            button.print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <h1>HIGIENE DIGITAL // I-SAFE</h1>
    
    <div class="leak-list">
        <h2>[!] VETORES EM RISCO IDENTIFICADOS</h2>
        <p>Baseado na varredura OSINT de hoje, as seguintes esferas foram sinalizadas em vazamentos atrelados ao usuário: <strong>{", ".join(safe_detected_leaks).upper() if safe_detected_leaks else "SISTEMA LIMPO"}</strong></p>
    </div>

    <h2>CHECKLIST DE REMEDIAÇÃO TÁTICA</h2>
    <div id="tasks">
        {checklist_items}
    </div>

    <button class="print-btn" onclick="window.print()">SALVAR RELATÓRIO COMO PDF LOCAL</button>
</body>
</html>"""
        return template

    @staticmethod
    def _build_task(title: str, description: str) -> str:
        safe_title = html.escape(title, quote=True)
        safe_description = html.escape(description, quote=True)
        unique_id = (
            title.replace(" ", "_").lower().replace("ã", "a").replace("ç", "c").replace("/", "_")
        )
        return f"""
        <div class="task-card">
            <input type="checkbox" id="{unique_id}">
            <label for="{unique_id}">[{safe_title}]</label>
            <p class="task-desc">{safe_description}</p>
        </div>"""

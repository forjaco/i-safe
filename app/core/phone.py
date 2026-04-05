import re


E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone_number(raw_phone: str) -> str:
    value = str(raw_phone or "").strip()
    if not value:
        raise ValueError("Telefone ausente.")

    cleaned = re.sub(r"[^\d+]", "", value)

    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"

    if cleaned.count("+") > 1 or ("+" in cleaned and not cleaned.startswith("+")):
        raise ValueError("Telefone inválido.")

    if not cleaned.startswith("+"):
        raise ValueError("Telefone deve estar em formato internacional E.164.")

    if not E164_PATTERN.fullmatch(cleaned):
        raise ValueError("Telefone inválido.")

    return cleaned

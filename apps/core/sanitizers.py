"""
Input sanitization utilities.
All user-supplied text passes through here before being stored.
"""
import re
import bleach


ALLOWED_TAGS: list[str] = []
ALLOWED_ATTRIBUTES: dict = {}


def sanitize_text(value: str | None) -> str:
    """Remove tags HTML completas (tag + conteúdo interno de tags perigosas) e colapsa espaços."""
    if not value:
        return ""
    # Remove tags de script/style junto com seu conteúdo
    cleaned = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', value, flags=re.IGNORECASE | re.DOTALL)
    # Remove todas as outras tags HTML (mantém o texto entre elas)
    cleaned = bleach.clean(cleaned, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    # Colapsa espaços múltiplos
    return re.sub(r"\s+", " ", cleaned).strip()


def sanitize_phone(value: str | None) -> str:
    """Mantém apenas dígitos, +, (, ), - e espaços."""
    if not value:
        return ""
    return re.sub(r"[^\d\s\+\(\)\-]", "", value).strip()


def sanitize_cep(value: str | None) -> str:
    """Mantém apenas dígitos e traço em CEPs brasileiros."""
    if not value:
        return ""
    return re.sub(r"[^\d\-]", "", value).strip()

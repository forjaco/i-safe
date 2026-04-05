class ServiceUnavailableError(Exception):
    """Erro operacional temporário para dependências ou infraestrutura."""


class PersistenceUnavailableError(ServiceUnavailableError):
    """Erro temporário de persistência."""


class AuthenticationError(Exception):
    """Erro base para fluxos de autenticação."""


class InvalidCredentialsError(AuthenticationError):
    """Credenciais inválidas ou usuário inativo."""


class InvalidAccessTokenError(AuthenticationError, ValueError):
    """Access token inválido, expirado ou ausente."""


class InvalidRefreshTokenError(AuthenticationError, ValueError):
    """Refresh token inválido, expirado ou revogado."""


class RefreshTokenReuseDetectedError(InvalidRefreshTokenError):
    """Reuse attack detectado durante a rotação do refresh token."""

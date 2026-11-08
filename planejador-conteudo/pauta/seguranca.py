"""Hash de senha (scrypt, da biblioteca padrão) e tokens JWT."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

_N, _R, _P = 2**14, 8, 1


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def gerar_hash(senha: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(sal)}${_b64(h)}"


def conferir_senha(senha: str, guardado: str) -> bool:
    try:
        _, n, r, p, sal, h = guardado.split("$")
        calculado = hashlib.scrypt(
            senha.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p), dklen=32
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculado, base64.b64decode(h))


# Hash fixo para gastar o mesmo tempo quando o e-mail não existe (evita descobrir contas pelo tempo de resposta).
HASH_FALSO = gerar_hash(secrets.token_urlsafe(16))


def criar_token(usuario_id: str, chave: str, horas: int) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode({"sub": usuario_id, "iat": agora, "exp": agora + timedelta(hours=horas)}, chave, "HS256")


def ler_token(token: str, chave: str) -> str | None:
    try:
        return jwt.decode(token, chave, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        return None

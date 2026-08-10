from functools import lru_cache
from typing import Any, Optional

from composio import Composio
from fastapi import HTTPException, status

from app.config import settings


@lru_cache
def get_composio_client() -> Composio:
    if not settings.COMPOSIO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="COMPOSIO_API_KEY não configurada",
        )
    return Composio(api_key=settings.COMPOSIO_API_KEY)


async def execute_tool(
    slug: str,
    arguments: dict[str, Any],
    user_id: str,
    connected_account_id: Optional[str] = None,
) -> dict[str, Any]:
    client = get_composio_client()
    result = client.tools.execute(
        slug,
        arguments=arguments,
        user_id=user_id,
        connected_account_id=connected_account_id,
    )
    return dict(result)

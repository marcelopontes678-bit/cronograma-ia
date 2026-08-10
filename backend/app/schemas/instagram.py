from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InstagramConnectResponse(BaseModel):
    redirect_url: Optional[str]
    status: str


class InstagramStatusResponse(BaseModel):
    conectado: bool
    status: Optional[str] = None
    connected_at: Optional[datetime] = None

"""x402 Payment Client — bridges Python core to the x402 TypeScript microservice."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Services that require x402 payment
PAID_SERVICES: dict[str, str] = {
    "translate": "translate",
    "premium-nav": "premium-nav",
    "health-analysis": "health-analysis",
}


class X402Client:
    """Client for the x402 payment microservice."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.x402_base_url).rstrip("/")
        self._http: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10.0)
        return self._http

    async def list_services(self) -> list[dict[str, Any]]:
        """List available paid services."""
        client = await self._get_client()
        resp = await client.get(f"{self.base_url}/services")
        resp.raise_for_status()
        return resp.json().get("services", [])

    async def request_payment(self, service: str) -> dict[str, Any]:
        """Request payment requirements for a service (returns 402 body)."""
        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/request-payment",
            json={"service": service},
        )
        # The x402 service returns 402 status with requirements
        return resp.json()

    async def pay_and_settle(self, service: str, payer_wallet: str = "user") -> dict[str, Any]:
        """One-shot payment + settlement for a service."""
        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/pay-and-settle",
            json={"service": service, "payerWallet": payer_wallet},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_payments(self) -> dict[str, Any]:
        """Get payment history."""
        client = await self._get_client()
        resp = await client.get(f"{self.base_url}/payments")
        resp.raise_for_status()
        return resp.json()

    async def get_wallets(self) -> list[dict[str, Any]]:
        """Get mock wallet balances."""
        client = await self._get_client()
        resp = await client.get(f"{self.base_url}/wallets")
        resp.raise_for_status()
        return resp.json().get("wallets", [])

    async def close(self) -> None:
        """Clean up HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None

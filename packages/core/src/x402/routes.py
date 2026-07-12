"""x402 Payment REST API router for WearableAgent Hub backend."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends

from .client import X402Client
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])

# Dependency: create X402Client instance per request
async def get_x402_client() -> X402Client:
    client = X402Client(settings.x402_base_url)
    try:
        yield client
    finally:
        await client.close()


@router.get("/services")
async def list_services(client: X402Client = Depends(get_x402_client)) -> list[dict[str, Any]]:
    """List available paid services."""
    try:
        return await client.list_services()
    except Exception as e:
        logger.exception("Failed to list services")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/request")
async def request_payment(service: str, client: X402Client = Depends(get_x402_client)) -> dict[str, Any]:
    """Request payment requirements for a service."""
    try:
        return await client.request_payment(service)
    except Exception as e:
        logger.exception("Failed to request payment")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/pay")
async def pay_and_settle(service: str, payer_wallet: str = "user", client: X402Client = Depends(get_x402_client)) -> dict[str, Any]:
    """One-shot pay and settle for a service."""
    try:
        return await client.pay_and_settle(service, payer_wallet)
    except Exception as e:
        logger.exception("Payment failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/history")
async def payment_history(client: X402Client = Depends(get_x402_client)) -> dict[str, Any]:
    """Get payment history."""
    try:
        return await client.get_payments()
    except Exception as e:
        logger.exception("Failed to fetch payment history")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/wallets")
async def wallet_balances(client: X402Client = Depends(get_x402_client)) -> list[dict[str, Any]]:
    """Get mock wallet balances."""
    try:
        return await client.get_wallets()
    except Exception as e:
        logger.exception("Failed to fetch wallets")
        raise HTTPException(status_code=502, detail=str(e))

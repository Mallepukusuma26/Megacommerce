"""
MegaCommerce Local Payment Simulators Core
Zero External API Key Compliance Architecture
Supports Simulated Card, UPI, Wallet, NetBanking, and Cash-on-Delivery
"""

import uuid
import datetime
import random
from typing import Dict, Any, Optional


class SimulatedCardGateway:
    @staticmethod
    def process_card(card_number: str, expiry: str, cvv: str, amount: float) -> Dict[str, Any]:
        last4 = card_number[-4:] if len(card_number) >= 4 else "4242"
        is_success = not card_number.endswith("0000")
        return {
            "gateway": "SIMULATED_CARD",
            "transaction_id": f"CARD-SIM-{uuid.uuid4().hex[:12].upper()}",
            "amount": amount,
            "last4": last4,
            "status": "SUCCESS" if is_success else "DECLINED",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }


class SimulatedUPIGateway:
    @staticmethod
    def process_upi(upi_id: str, amount: float) -> Dict[str, Any]:
        is_valid = "@" in upi_id
        return {
            "gateway": "SIMULATED_UPI",
            "transaction_id": f"UPI-SIM-{uuid.uuid4().hex[:12].upper()}",
            "upi_id": upi_id,
            "amount": amount,
            "status": "SUCCESS" if is_valid else "INVALID_VPA",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }


class SimulatedWalletGateway:
    @staticmethod
    def process_wallet(wallet_type: str, user_id: str, amount: float) -> Dict[str, Any]:
        return {
            "gateway": f"SIMULATED_WALLET_{wallet_type.upper()}",
            "transaction_id": f"WLT-SIM-{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "amount": amount,
            "status": "SUCCESS",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }


class SimulatedCODGateway:
    @staticmethod
    def process_cod(order_id: str, amount: float) -> Dict[str, Any]:
        return {
            "gateway": "SIMULATED_COD",
            "transaction_id": f"COD-SIM-{uuid.uuid4().hex[:12].upper()}",
            "order_id": order_id,
            "amount": amount,
            "status": "PENDING_COLLECTION_ON_DELIVERY",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

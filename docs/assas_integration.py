"""
─────────────────────────────────────────────────────────────────────────────
PROPOSTA DE INTEGRAÇÃO COM ASSAS (PAGAMENTOS)
Lacrei Saúde API — apps/payments/assas_client.py
─────────────────────────────────────────────────────────────────────────────

ARQUITETURA:
  Appointment → (ao confirmar) → AssasClient.create_charge()
                                ↓
                           Webhook Assas (/api/v1/payments/webhook/)
                                ↓
                     Appointment.payment_status = CONFIRMED
                                ↓
                    (futuro) Split automático para profissional

FLUXO:
  1. Paciente agenda consulta → status: SCHEDULED
  2. Sistema cria cobrança no Assas (boleto / Pix / cartão)
  3. Assas retorna payment_id e link de pagamento
  4. Paciente paga → Assas envia webhook → status: CONFIRMED
  5. Split: Lacrei retém taxa, repassa ao profissional via Assas Split

VARIÁVEIS DE AMBIENTE NECESSÁRIAS:
  ASSAS_API_KEY=your_assas_api_key
  ASSAS_BASE_URL=https://api.asaas.com/v3          # produção
  # ASSAS_BASE_URL=https://sandbox.asaas.com/api/v3  # sandbox
  ASSAS_WEBHOOK_TOKEN=token-para-validar-webhooks

SPLIT PAYMENTS (Lacrei → Profissional):
  - Assas suporta split automático via "split" no payload da cobrança
  - Cada profissional precisa ter uma conta Assas sub-conta (walletId)
  - Percentual de repasse configurável por profissional
─────────────────────────────────────────────────────────────────────────────
"""

import hmac
import logging
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

import requests
from django.conf import settings

logger = logging.getLogger("lacrei.payments")


class BillingType(str, Enum):
    PIX = "PIX"
    BOLETO = "BOLETO"
    CREDIT_CARD = "CREDIT_CARD"
    UNDEFINED = "UNDEFINED"  # Assas escolhe o melhor método


@dataclass
class ChargeRequest:
    """Representa uma cobrança a ser criada no Assas."""

    customer_id: str  # ID do cliente no Assas
    value: Decimal  # Valor em BRL
    due_date: str  # YYYY-MM-DD
    description: str
    billing_type: BillingType = BillingType.PIX
    external_reference: str = ""  # UUID da consulta (Appointment.id)
    # Split payments
    split_wallet_id: str | None = None  # Assas wallet do profissional
    split_fixed_value: Decimal | None = None
    split_percent_value: Decimal | None = None


@dataclass
class ChargeResponse:
    """Resposta normalizada do Assas."""

    payment_id: str
    status: str
    value: Decimal
    net_value: Decimal
    billing_type: str
    pix_qr_code: str | None = None
    pix_key: str | None = None
    bank_slip_url: str | None = None
    invoice_url: str | None = None


class AssasClient:
    """
    Cliente HTTP para a API do Assas.

    Documentação: https://asaasv3.docs.apiary.io/
    """

    def __init__(self):
        self.api_key = getattr(settings, "ASSAS_API_KEY", "")
        self.base_url = getattr(
            settings, "ASSAS_BASE_URL", "https://sandbox.asaas.com/api/v3"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "access_token": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "LacreisaúdeAPI/1.0",
            }
        )

    def create_or_get_customer(
        self, professional_email: str, name: str, cpf_cnpj: str = ""
    ) -> str:
        """
        Cria ou recupera um cliente no Assas pelo email.
        Retorna o customerId do Assas.
        """
        # Tenta buscar por email primeiro
        resp = self.session.get(
            f"{self.base_url}/customers",
            params={"email": professional_email},
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("totalCount", 0) > 0:
            return data["data"][0]["id"]

        # Cria novo cliente
        payload = {
            "name": name,
            "email": professional_email,
            "cpfCnpj": cpf_cnpj,
            "notificationDisabled": False,
        }
        resp = self.session.post(f"{self.base_url}/customers", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def create_charge(self, charge: ChargeRequest) -> ChargeResponse:
        """
        Cria uma cobrança no Assas com suporte a split payment.
        """
        payload = {
            "customer": charge.customer_id,
            "billingType": charge.billing_type.value,
            "value": float(charge.value),
            "dueDate": charge.due_date,
            "description": charge.description,
            "externalReference": charge.external_reference,
        }

        # Configurar split se o profissional tem wallet Assas
        if charge.split_wallet_id:
            payload["split"] = [
                {
                    "walletId": charge.split_wallet_id,
                    # Repasse fixo OU percentual
                    **(
                        {"fixedValue": float(charge.split_fixed_value)}
                        if charge.split_fixed_value
                        else {}
                    ),
                    **(
                        {"percentualValue": float(charge.split_percent_value)}
                        if charge.split_percent_value
                        else {}
                    ),
                }
            ]

        logger.info(
            "Criando cobrança no Assas",
            extra={
                "external_reference": charge.external_reference,
                "value": str(charge.value),
            },
        )

        resp = self.session.post(f"{self.base_url}/payments", json=payload)
        resp.raise_for_status()
        data = resp.json()

        return ChargeResponse(
            payment_id=data["id"],
            status=data["status"],
            value=Decimal(str(data["value"])),
            net_value=Decimal(str(data.get("netValue", data["value"]))),
            billing_type=data["billingType"],
            pix_qr_code=data.get("pixQrCode", {}).get("payload"),
            bank_slip_url=data.get("bankSlipUrl"),
            invoice_url=data.get("invoiceUrl"),
        )

    def get_charge(self, payment_id: str) -> dict:
        """Consulta o status de uma cobrança."""
        resp = self.session.get(f"{self.base_url}/payments/{payment_id}")
        resp.raise_for_status()
        return resp.json()

    def refund_charge(self, payment_id: str) -> bool:
        """Solicita estorno de uma cobrança (ex.: cancelamento de consulta)."""
        resp = self.session.post(f"{self.base_url}/payments/{payment_id}/refund")
        return resp.status_code in (200, 201)


def validate_assas_webhook(payload: bytes, received_token: str) -> bool:
    """
    Valida que o webhook recebido veio de fato do Assas.
    O Assas envia o token no header 'asaas-access-token'.
    """
    expected = getattr(settings, "ASSAS_WEBHOOK_TOKEN", "")
    return hmac.compare_digest(expected, received_token)


# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK HANDLER (seria adicionado em apps/payments/views.py)
# ─────────────────────────────────────────────────────────────────────────────
#
# class AssasWebhookView(APIView):
#     permission_classes = [AllowAny]  # Assas não envia token JWT
#
#     def post(self, request):
#         token = request.headers.get("asaas-access-token", "")
#         if not validate_assas_webhook(request.body, token):
#             return Response({"error": "Unauthorized"}, status=401)
#
#         event = request.data.get("event")
#         payment = request.data.get("payment", {})
#         external_ref = payment.get("externalReference")  # Appointment UUID
#
#         if event == "PAYMENT_CONFIRMED":
#             Appointment.objects.filter(id=external_ref).update(
#                 payment_status="CONFIRMED"
#             )
#         elif event == "PAYMENT_REFUNDED":
#             Appointment.objects.filter(id=external_ref).update(
#                 payment_status="REFUNDED"
#             )
#
#         return Response({"received": True})

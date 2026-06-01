from sanic import Blueprint, response
from sanic.request import Request

from src.application.dto import PaymentWebhookRequest
from src.application.use_cases.payment import ProcessPaymentWebhookUseCase

payment_bp = Blueprint("payment", url_prefix="/payments")


def setup_payment_routes(
    bp: Blueprint,
    process_payment_use_case: ProcessPaymentWebhookUseCase,
) -> None:
    @bp.post("/webhook")
    async def webhook(request: Request):
        body = PaymentWebhookRequest(**request.json)
        payment = await process_payment_use_case.execute(
            transaction_id=body.transaction_id,
            user_id=body.user_id,
            account_id=body.account_id,
            amount=body.amount,
            signature=body.signature,
        )
        return response.json(payment.model_dump(mode="json"), status=201)

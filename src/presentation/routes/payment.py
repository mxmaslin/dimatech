from sanic import Blueprint, response
from sanic.request import Request

from src.application.dto import PaymentWebhookRequest
from src.application.errors import ValidationError
from src.application.use_cases.payment import ProcessPaymentWebhookUseCase

payment_bp = Blueprint("payment", url_prefix="/payments")


def setup_payment_routes(
    bp: Blueprint,
    process_payment_use_case: ProcessPaymentWebhookUseCase,
) -> None:
    @bp.post("/webhook")
    async def webhook(request: Request):
        body = request.json
        if body is None:
            raise ValidationError("Request body must be valid JSON")
        parsed = PaymentWebhookRequest(**body)
        payment = await process_payment_use_case.execute(
            transaction_id=parsed.transaction_id,
            user_id=parsed.user_id,
            account_id=parsed.account_id,
            amount=parsed.amount,
            signature=parsed.signature,
        )
        return response.json(payment.model_dump(mode="json"), status=201)

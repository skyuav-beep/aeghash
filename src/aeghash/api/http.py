"""FastAPI application wiring for OAuth authentication endpoints."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, UTC
from decimal import Decimal
import time
from typing import Any, Mapping, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from aeghash.adapters.turnstile import TurnstileError
from aeghash.api.auth import AuthenticationAPI, OAuthCallbackPayload
from aeghash.api.signup import SignupAPI, SignupPayload, SignupError, SignupResult
from aeghash.api.login import LoginError, PasswordLoginAPI, PasswordLoginPayload
from aeghash.api.audit import LoginAuditAPI
from aeghash.api.kpi import OrganizationKpiAPI, serialize_summary
from aeghash.api.commerce import (
    AegmallInboundAPI,
    AegmallOrderError,
    AegmallOrderRequest,
    IdempotencyConflict,
    IdempotencyPending,
)
from aeghash.api.withdrawals import WithdrawalApprovalAPI
from aeghash.application import Application, create_application, shutdown_application
from aeghash.core.auth_flow import AuthenticationResult
from aeghash.core.mining_workflow import WithdrawalExecutionError
from aeghash.core.point_wallet import InvalidWithdrawalState, WithdrawalNotFound, WITHDRAWAL_STATUS_APPROVED_STAGE1
from aeghash.infrastructure.database import Base
from aeghash.core.two_factor import TwoFactorService
from aeghash.infrastructure.repositories import SqlAlchemySessionRepository, SqlAlchemyTwoFactorRepository
from aeghash.security.access import AccessContext, AccessPolicy
from aeghash.security.masking import mask_email, mask_identifier, mask_wallet_address
from aeghash.ui.qa_checklist import (
    get_accessibility_checklist,
    render_checklist_page_html,
    serialize_checklist,
)


class OAuthCallbackBody(BaseModel):
    provider: str
    code: str
    state: str
    expected_state: str
    turnstile_token: str | None = None
    two_factor_code: str | None = None


class SignupBody(BaseModel):
    email: str
    password: str
    password_confirm: str
    roles: Optional[list[str]] = None
    turnstile_token: Optional[str] = None


class PasswordLoginBody(BaseModel):
    email: str
    password: str
    turnstile_token: Optional[str] = None
    two_factor_code: Optional[str] = None


class LoginAuditResponse(BaseModel):
    provider: str
    status: str
    subject: Optional[str]
    reason: Optional[str]


class AegmallOrderBody(BaseModel):
    order_id: str
    user_id: str
    total_amount: Decimal
    pv_amount: Decimal
    channel: str
    metadata: dict[str, Any] | None = None
    idempotency_key: str


class AegmallOrderResponseBody(BaseModel):
    status: str
    order_id: str
    bonuses_created: int
    bonus_ids: list[str]


class WithdrawalApproveBody(BaseModel):
    approved_by: str
    finalize: bool = True
    notes: Optional[str] = None
    coin: Optional[str] = None


class WithdrawalResponseBody(BaseModel):
    request_id: str
    wallet_id: str
    amount: Decimal
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class TwoFactorStatusResponse(BaseModel):
    user_id: str
    enabled: bool
    recovery_codes_remaining: int
    updated_at: Optional[datetime] = None


def create_http_app(
    application: Application | None = None,
    *,
    include_two_factor: bool = True,
    shutdown_on_exit: bool | None = None,
) -> FastAPI:
    """Create a FastAPI application serving the OAuth authentication endpoint."""

    created_application = application or create_application()
    Base.metadata.create_all(created_application.container.session_manager.engine)
    auth_api = AuthenticationAPI.from_container(
        created_application.container,
        include_two_factor=include_two_factor,
    )

    app = FastAPI()
    app.state.application = created_application
    signup_api = SignupAPI.from_container(created_application.container)
    password_login_api = PasswordLoginAPI.from_container(created_application.container)
    login_audit_api = LoginAuditAPI.from_container(created_application.container)
    kpi_api = OrganizationKpiAPI.from_container(created_application.container)
    aegmall_api = AegmallInboundAPI.from_container(created_application.container)
    withdrawal_api = WithdrawalApprovalAPI.from_container(created_application.container)

    app.state.auth_api = auth_api
    app.state.signup_api = signup_api
    app.state.password_login_api = password_login_api
    app.state.login_audit_api = login_audit_api
    app.state.kpi_api = kpi_api
    app.state.aegmall_api = aegmall_api
    app.state.withdrawal_api = withdrawal_api

    if shutdown_on_exit is None:
        shutdown_on_exit = application is None

    if shutdown_on_exit:
        @app.on_event("shutdown")
        async def _shutdown() -> None:
            shutdown_application(created_application)

    @app.post("/oauth/callback")
    async def oauth_callback(
        body: OAuthCallbackBody,
        request: Request,
        api: AuthenticationAPI = Depends(_get_auth_api),
    ) -> JSONResponse:
        payload = OAuthCallbackPayload(
            provider=body.provider,
            code=body.code,
            state=body.state,
            expected_state=body.expected_state,
            turnstile_token=body.turnstile_token,
            two_factor_code=body.two_factor_code,
        )
        remote_ip = request.client.host if request.client else None
        try:
            result = api.authenticate(payload, remote_ip=remote_ip)
        except TurnstileError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="OAuth authentication failed") from exc

        return JSONResponse(_result_to_dict(result))

    @app.post("/signup", status_code=201)
    async def signup(
        body: SignupBody,
        request: Request,
        api: SignupAPI = Depends(_get_signup_api),
    ) -> JSONResponse:
        if body.password != body.password_confirm:
            raise HTTPException(status_code=400, detail="password_mismatch")
        payload = SignupPayload(
            email=body.email,
            password=body.password,
            roles=tuple(body.roles) if body.roles else None,
            turnstile_token=body.turnstile_token,
            remote_ip=request.client.host if request.client else None,
        )
        try:
            result = api.register(payload)
        except SignupError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(_signup_result_to_dict(result), status_code=201)

    @app.post("/login/password")
    async def password_login(
        body: PasswordLoginBody,
        request: Request,
        api: PasswordLoginAPI = Depends(_get_password_login_api),
    ) -> JSONResponse:
        payload = PasswordLoginPayload(
            email=body.email,
            password=body.password,
            turnstile_token=body.turnstile_token,
            two_factor_code=body.two_factor_code,
            remote_ip=request.client.host if request.client else None,
        )
        try:
            result = api.login(payload)
        except LoginError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(_result_to_dict(result))

    @app.get("/audit/logins")
    async def list_login_audits(
        request: Request,
        limit: int = 100,
        api: LoginAuditAPI = Depends(_get_login_audit_api),
    ) -> list[LoginAuditResponse]:
        access = _require_access(request, ("audits:view",))
        policy = AccessPolicy(access)
        mask_subjects = not policy.can_view_full_audit_subjects()
        records = api.list_recent(limit=limit)
        return [
            LoginAuditResponse(
                provider=record.provider,
                status=record.status,
                subject=record.subject if not mask_subjects else mask_email(record.subject),
                reason=record.reason,
            )
            for record in records
        ]

    @app.get("/admin/organizations/{tree_type}/{node_id}/kpi")
    async def get_organization_kpi(
        tree_type: str,
        node_id: str,
        request: Request,
        days: int = 7,
        api: OrganizationKpiAPI = Depends(_get_kpi_api),
    ) -> JSONResponse:
        access = _require_access(request, ("kpi:read",))
        summary = api.get_summary(node_id=node_id, tree_type=tree_type, days=days, access=access)
        return JSONResponse(serialize_summary(summary))

    @app.post("/aegmall/orders", status_code=201)
    async def ingest_aegmall_order(
        body: AegmallOrderBody,
        api: AegmallInboundAPI = Depends(_get_aegmall_api),
    ) -> JSONResponse:
        request_payload = AegmallOrderRequest(
            order_id=body.order_id,
            user_id=body.user_id,
            total_amount=body.total_amount,
            pv_amount=body.pv_amount,
            channel=body.channel,
            metadata=body.metadata or {},
            idempotency_key=body.idempotency_key,
        )
        try:
            result = api.process_order(request_payload)
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except IdempotencyPending as exc:
            raise HTTPException(status_code=425, detail=str(exc)) from exc
        except AegmallOrderError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        status_code = 201 if result.status == "created" else 200
        response_body = AegmallOrderResponseBody(
            status=result.status,
            order_id=result.order_id,
            bonuses_created=result.bonuses_created,
            bonus_ids=list(result.bonus_ids),
        )
        return JSONResponse(
            response_body.model_dump(),
            status_code=status_code,
        )

    @app.post("/admin/withdrawals/{request_id}/approve")
    async def approve_withdrawal(
        request_id: str,
        body: WithdrawalApproveBody,
        request: Request,
        api: WithdrawalApprovalAPI = Depends(_get_withdrawal_api),
    ) -> WithdrawalResponseBody:
        access = _require_access(request, ("wallets:approve_withdrawal",))
        try:
            snapshot = api.approve(
                request_id,
                approved_by=body.approved_by,
                notes=body.notes,
                coin=body.coin,
                finalize=body.finalize,
            )
        except WithdrawalNotFound:
            raise HTTPException(status_code=404, detail="withdrawal_not_found") from None
        except InvalidWithdrawalState as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except WithdrawalExecutionError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        metadata = dict(snapshot.metadata) if snapshot.metadata else None
        response = WithdrawalResponseBody(
            request_id=snapshot.request_id,
            wallet_id=snapshot.wallet_id,
            amount=snapshot.amount,
            status=snapshot.status,
            requested_by=snapshot.requested_by,
            approved_by=snapshot.approved_by,
            approved_at=snapshot.approved_at,
            notes=snapshot.notes,
            metadata=metadata,
        )
        status_code = 202 if snapshot.status == WITHDRAWAL_STATUS_APPROVED_STAGE1 else 200
        payload = response.model_dump(mode="json")
        masked_payload = _mask_withdrawal_payload(payload, AccessPolicy(access))
        return JSONResponse(masked_payload, status_code=status_code)

    @app.get("/admin/users/{user_id}/two_factor", response_model=TwoFactorStatusResponse)
    async def get_two_factor_status(user_id: str, request: Request) -> TwoFactorStatusResponse:
        _require_access(request, ("users:two_factor:view",))
        application: Application = request.app.state.application
        container = application.container
        with container.session_manager.session_scope() as session:
            repo = SqlAlchemyTwoFactorRepository(session)
            record = repo.get(user_id)
        if not record:
            return TwoFactorStatusResponse(
                user_id=user_id,
                enabled=False,
                recovery_codes_remaining=0,
                updated_at=None,
            )
        updated_at = None
        if record.updated_at:
            updated_at = datetime.fromtimestamp(record.updated_at, tz=UTC)
        return TwoFactorStatusResponse(
            user_id=user_id,
            enabled=record.enabled,
            recovery_codes_remaining=len(record.recovery_codes),
            updated_at=updated_at,
        )

    @app.post("/admin/users/{user_id}/two_factor/disable", status_code=204)
    async def disable_two_factor(user_id: str, request: Request) -> Response:
        access = _require_access(request, ("users:two_factor:disable",))
        application: Application = request.app.state.application
        container = application.container
        with container.session_manager.session_scope() as session:
            repo = SqlAlchemyTwoFactorRepository(session)
            service = TwoFactorService(repo, event_hook=container.event_hook)
            if not service.disable(user_id, actor_id=access.user_id):
                raise HTTPException(status_code=404, detail="two_factor_not_enabled")
        return Response(status_code=204)

    @app.get("/qa/checklist", response_class=HTMLResponse)
    async def qa_checklist_page() -> str:
        checklist = get_accessibility_checklist()
        return render_checklist_page_html(checklist)

    @app.get("/qa/checklist/data")
    async def qa_checklist_data() -> dict[str, Any]:
        checklist = get_accessibility_checklist()
        return serialize_checklist(checklist)

    return app


def _get_auth_api(request: Request) -> AuthenticationAPI:
    api = getattr(request.app.state, "auth_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("AuthenticationAPI is not configured.")
    return api


def _get_signup_api(request: Request) -> SignupAPI:
    api = getattr(request.app.state, "signup_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("SignupAPI is not configured.")
    return api


def _get_password_login_api(request: Request) -> PasswordLoginAPI:
    api = getattr(request.app.state, "password_login_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("PasswordLoginAPI is not configured.")
    return api


def _get_login_audit_api(request: Request) -> LoginAuditAPI:
    api = getattr(request.app.state, "login_audit_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("LoginAuditAPI is not configured.")
    return api


def _get_kpi_api(request: Request) -> OrganizationKpiAPI:
    api = getattr(request.app.state, "kpi_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("OrganizationKpiAPI is not configured.")
    return api


def _get_aegmall_api(request: Request) -> AegmallInboundAPI:
    api = getattr(request.app.state, "aegmall_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("AegmallInboundAPI is not configured.")
    return api


def _get_withdrawal_api(request: Request) -> WithdrawalApprovalAPI:
    api = getattr(request.app.state, "withdrawal_api", None)
    if api is None:  # pragma: no cover - defensive guard
        raise RuntimeError("WithdrawalApprovalAPI is not configured.")
    return api


def _result_to_dict(result: AuthenticationResult) -> dict[str, Optional[str] | bool | tuple[str, ...]]:
    data = asdict(result)
    # dataclasses.asdict converts tuple -> list; restore tuple where appropriate
    roles = tuple(result.roles)
    data["roles"] = roles
    return data


def _signup_result_to_dict(result: SignupResult) -> dict[str, object]:
    return {
        "user_id": result.user_id,
        "email": result.email,
        "roles": list(result.roles),
    }


def _require_access(request: Request, required_permissions: tuple[str, ...]) -> AccessContext:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")

    application: Application = request.app.state.application
    container = application.container
    with container.session_manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        record = repo.get_session(token)

    if record is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    if record.expires_at <= time.time():
        raise HTTPException(status_code=401, detail="session_expired")

    access = AccessContext.from_session(record)
    policy = AccessPolicy(access)
    if required_permissions and not policy.has_all(required_permissions):
        raise HTTPException(status_code=403, detail="forbidden")
    return access


def _mask_withdrawal_payload(payload: dict[str, Any], policy: AccessPolicy) -> dict[str, Any]:
    if policy.can_view_full_personal_data():
        return payload

    masked = dict(payload)
    masked["wallet_id"] = mask_identifier(str(payload.get("wallet_id", "")) or None)
    masked["requested_by"] = mask_identifier(str(payload.get("requested_by", "")) or None)
    approved_by = payload.get("approved_by")
    if approved_by:
        masked["approved_by"] = mask_identifier(str(approved_by))

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        masked["metadata"] = _mask_sensitive_metadata(metadata)
    return masked


def _mask_sensitive_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            lowered = key.lower()
            if "email" in lowered:
                masked[key] = mask_email(value)
                continue
            if "address" in lowered or "wallet" in lowered:
                masked[key] = mask_wallet_address(value)
                continue
            if "user" in lowered or "account" in lowered:
                masked[key] = mask_identifier(value)
                continue
        masked[key] = value
    return masked

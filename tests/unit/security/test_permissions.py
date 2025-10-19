from aeghash.security.permissions import AuthorizationDecision, PermissionService


def test_permissions_for_roles():
    service = PermissionService()
    perms = service.permissions_for(["admin", "member"])
    assert "dashboard:view" in perms
    assert "users:manage" in perms


def test_authorize_success():
    service = PermissionService()
    decision = service.authorize(["admin"], ["roles:assign"])
    assert isinstance(decision, AuthorizationDecision)
    assert decision.allowed is True


def test_authorize_failure_lists_missing():
    service = PermissionService()
    decision = service.authorize(["member"], ["users:manage"])
    assert decision.allowed is False
    assert decision.missing_permissions == {"users:manage"}

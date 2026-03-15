"""
Role-based permissions with per-user overrides.

Two-tier model:
1. Role defaults — each UserRole maps to a baseline set of permissions (code-defined)
2. Per-user overrides — admins can grant extra permissions via the DB (user_permission table)

Effective permissions = role_defaults ∪ user_overrides
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from app.models import UserRole

if TYPE_CHECKING:
    from app.models import User

# ── Permission registry ──────────────────────────────────────────────────────
# All known permissions with PT-BR labels.
# Adding a new permission = add one entry here + optionally add to a role's defaults.

ALL_PERMISSIONS: dict[str, str] = {
    "manage_permissions": "Gerenciar Permissões",
    "manage_users": "Gerenciar Usuários",
    "manage_clients": "Gerenciar Clientes",
    "manage_services": "Gerenciar Serviços",
    "manage_financeiro": "Gerenciar Financeiro",
    "manage_fornecedores": "Gerenciar Fornecedores",
    "manage_estoque": "Gerenciar Estoque",
    "view_dashboard": "Visualizar Dashboard",
    "view_financeiro": "Visualizar Financeiro",
    "view_fornecedores": "Visualizar Fornecedores",
    "view_estoque": "Visualizar Estoque",
    "view_contas_pagar": "Visualizar Contas a Pagar",
    "view_contas_receber": "Visualizar Contas a Receber",
    "view_well_status": "Visualizar Status do Poço",
    "view_reports": "Visualizar Relatórios",
    "manage_orcamentos": "Gerenciar Orçamentos",
    "view_orcamentos": "Visualizar Orçamentos",
}

# ── Role defaults ─────────────────────────────────────────────────────────────

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.admin: {
        "manage_permissions",
        "manage_users",
        "manage_clients",
        "manage_services",
        "manage_fornecedores",
        "manage_estoque",
        "manage_orcamentos",
        "view_dashboard",
        "view_financeiro",
        "view_fornecedores",
        "view_estoque",
        "view_orcamentos",
    },
    UserRole.finance: {
        "manage_financeiro",
        "manage_orcamentos",
        "view_dashboard",
        "view_financeiro",
        "view_fornecedores",
        "view_estoque",
        "view_contas_pagar",
        "view_contas_receber",
        "view_orcamentos",
    },
    UserRole.client: set(),
}


def get_role_defaults(role: UserRole) -> set[str]:
    """Return the default permission set for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_effective_permissions(session: Session, user: User) -> set[str]:
    """Return role defaults ∪ per-user DB overrides."""
    from app.models import UserPermission

    defaults = get_role_defaults(user.role)
    statement = select(UserPermission.permission).where(
        UserPermission.user_id == user.id
    )
    overrides = set(session.exec(statement).all())
    return defaults | overrides

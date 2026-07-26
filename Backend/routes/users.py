"""
routes/users.py — Users & Teams Blueprint (stub).

Endpoints:
    GET /api/v1/users  — List all members of the authenticated organization.

Matches the UsersTeams.jsx page added in the frontend update.
The page currently uses a local mockUsers array; this endpoint provides
the backend contract so it can be wired up without frontend changes.

User object shape (mirrors UsersTeams.jsx mockUsers):
    {
        "initials": "AR",
        "name":     "Aditi Rao",
        "id":       "INV-2291",
        "role":     "Head of Team" | "Investigator",
        "cases":    4,
        "status":   "Active" | "Inactive"
    }
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response

users_bp = Blueprint("users", __name__)

# ── In-memory stub store (mirrors UsersTeams.jsx mockUsers) ─────────────── #
# TODO (database phase): delete this list and replace every reference with
#     UserService.list(org_id=get_current_user_org())
_MOCK_USERS: list[dict] = [
    {"initials": "AR", "name": "Aditi Rao",     "id": "INV-2291", "role": "Head of Team",  "cases": 4, "status": "Active"},
    {"initials": "VK", "name": "Vikram Kumar",   "id": "INV-2287", "role": "Investigator",  "cases": 3, "status": "Active"},
    {"initials": "RS", "name": "Rahul Sharma",   "id": "INV-2285", "role": "Investigator",  "cases": 2, "status": "Active"},
    {"initials": "AP", "name": "Ananya Patel",   "id": "INV-2280", "role": "Investigator",  "cases": 1, "status": "Active"},
    {"initials": "NK", "name": "Nikhil Kapoor",  "id": "INV-2278", "role": "Investigator",  "cases": 2, "status": "Inactive"},
    {"initials": "SM", "name": "Sneha Mishra",   "id": "INV-2275", "role": "Investigator",  "cases": 3, "status": "Active"},
]


# ── GET /api/v1/users ───────────────────────────────────────────────────── #

@users_bp.get("/users")
def list_users():
    """
    Return all members of the authenticated organization.

    Supports optional query parameters:
        ?search=<string>   — filter by name or ID (case-insensitive)
        ?status=Active|Inactive — filter by status

    TODO (database phase):
        Replace stub data with:
            org_id  = get_current_user_org()
            search  = request.args.get("search", "").strip()
            status  = request.args.get("status", "").strip()
            users   = UserService.list(org_id=org_id, search=search, status=status)
            return success_response(data={
                "users": [u.to_dict() for u in users],
                "total": len(users),
            })

    Response (200):
        {
            "status":  "success",
            "message": "OK",
            "data": {
                "users": [ { ...user objects... } ],
                "total": 6
            }
        }
    """
    search = request.args.get("search", "").strip().lower()
    status = request.args.get("status", "").strip()

    # TODO (database phase): pass search/status to UserService.list()
    result = _MOCK_USERS

    if search:
        result = [
            u for u in result
            if search in u["name"].lower() or search in u["id"].lower()
        ]

    if status:
        result = [u for u in result if u["status"] == status]

    current_app.logger.debug(
        "GET /users  search=%s  status=%s  returning=%d",
        search or "—", status or "All", len(result),
    )

    return success_response(
        data={"users": result, "total": len(result)},
    )

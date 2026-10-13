"""
Portal Home – /portal

Builds tile data for every registered service (Helpdesk, Wiki, hook-based apps).
Guest users are redirected to login.  Errors in any single tile source are
caught, logged, and silently skipped so the page always renders.
"""

import frappe
from frappe import _

no_cache = 1

# ── SVG icons (Lucide-compatible, 24 × 24) ──────────────────────────────────
ICONS = {
    "ticket": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0'
        ' 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>'
        '<path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/></svg>'
    ),
    "plus": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><circle cx="12" cy="12" r="10"/>'
        '<path d="M8 12h8"/><path d="M12 8v8"/></svg>'
    ),
    "book": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5'
        ' 2.5 0 0 1 0-5H20"/></svg>'
    ),
    "box": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7'
        ' 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>'
        '<path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>'
    ),
    "help": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><circle cx="12" cy="12" r="10"/>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
        '<path d="M12 17h.01"/></svg>'
    ),
    "grid": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"'
        ' stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/>'
        '<rect width="7" height="7" x="14" y="3" rx="1"/>'
        '<rect width="7" height="7" x="14" y="14" rx="1"/>'
        '<rect width="7" height="7" x="3" y="14" rx="1"/></svg>'
    ),
}

# Helpdesk URLs – update if your Helpdesk version uses different routes.
HELPDESK_URLS = {
    "my_tickets": "/helpdesk/my-tickets",
    "new_ticket": "/helpdesk/my-tickets/new",
}


def get_context(context):
    """Build the portal home-page context."""

    # ── Guest → login ────────────────────────────────────────────────────────
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/portal"
        raise frappe.Redirect

    user = frappe.session.user
    tiles = []

    # ── Helpdesk tiles ───────────────────────────────────────────────────────
    try:
        tiles.extend(_helpdesk_tiles(user))
    except Exception:
        frappe.log_error("Portal: error building Helpdesk tiles")

    # ── Wiki / SOP tiles ─────────────────────────────────────────────────────
    try:
        tiles.extend(_wiki_tiles(user))
    except Exception:
        frappe.log_error("Portal: error building Wiki tiles")

    # ── Hook-based static tiles ──────────────────────────────────────────────
    for tile in frappe.get_hooks("msp_portal_tiles") or []:
        try:
            if _tile_visible(tile, user):
                tiles.append(_sanitise(tile))
        except Exception:
            frappe.log_error("Portal: error in static hook tile")

    # ── Hook-based dynamic providers ─────────────────────────────────────────
    for path in frappe.get_hooks("msp_portal_tile_providers") or []:
        try:
            fn = frappe.get_attr(path)
            for tile in fn(user) or []:
                tiles.append(_sanitise(tile))
        except Exception:
            frappe.log_error(f"Portal: error in tile provider {path}")

    # ── Sort and inject into context ─────────────────────────────────────────
    tiles.sort(key=lambda t: t.get("order", 100))

    context.tiles = tiles
    context.icons = ICONS
    context.no_cache = 1
    context.show_sidebar = False
    context.title = _("Customer Portal")
    context.no_header = 1
    context.no_breadcrumbs = 1
    context.support_email = frappe.conf.get("portal_support_email", "")
    context.user_fullname = (
        frappe.db.get_value("User", user, "full_name") or user.split("@")[0]
    )


# ── Tile builders ────────────────────────────────────────────────────────────


def _helpdesk_tiles(user):
    """Helpdesk cards – only if the app is installed and user holds an HD role."""
    if "helpdesk" not in frappe.get_installed_apps():
        return []

    hd_roles = {"HD Customer", "HD Customer Manager", "HD Agent", "HD Manager"}
    if not hd_roles.intersection(frappe.get_roles(user)):
        return []

    return [
        {
            "title": _("My Tickets"),
            "description": _("View and track your support tickets."),
            "url": HELPDESK_URLS["my_tickets"],
            "icon": "ticket",
            "order": 10,
            "cta": _("View Tickets"),
        },
        {
            "title": _("Create Ticket"),
            "description": _("Submit a new support request."),
            "url": HELPDESK_URLS["new_ticket"],
            "icon": "plus",
            "order": 20,
            "cta": _("New Ticket"),
        },
    ]


def _wiki_tiles(user):
    """One card per Wiki space the logged-in user may read.

    ``frappe.get_list`` enforces role permissions automatically, so a customer
    can only ever see their own spaces.
    """
    if "wiki" not in frappe.get_installed_apps():
        return []

    spaces = frappe.get_list(
        "Wiki Space",
        fields=["name", "route", "space_name"],
        limit_page_length=12,
        order_by="name asc",
    )

    tiles = []
    for idx, space in enumerate(spaces):
        route = space.get("route", "")
        if not route:
            continue
        label = space.get("space_name") or space.get("name")
        tiles.append({
            "title": label,
            "description": _("Documentation & SOPs"),
            "url": f"/{route}/home",
            "icon": "book",
            "order": 30 + idx,
            "cta": _("Open Docs"),
        })

    return tiles


# ── Helpers ──────────────────────────────────────────────────────────────────


def _tile_visible(tile, user):
    """``True`` if the tile has no role gate or the user holds any listed role."""
    roles = tile.get("roles")
    if not roles:
        return True
    return bool(set(frappe.get_roles(user)) & set(roles))


def _sanitise(tile):
    """Normalise a hook-provided tile dict into a safe shape."""
    url = tile.get("url", "")
    if url and not url.startswith("/") and not url.startswith("https://"):
        url = ""

    return {
        "title": tile.get("title", ""),
        "description": tile.get("description", ""),
        "url": url,
        "icon": tile.get("icon", "grid"),
        "order": tile.get("order", 100),
        "cta": tile.get("cta", _("Open")),
    }

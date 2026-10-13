app_name = "msp_portal"
app_title = "MSP Portal"
app_publisher = "TechMonarch"
app_description = "Customer Portal Home – cards for Helpdesk, Wiki SOPs, and future apps."
app_email = "support@techmonarch.com"
app_license = "MIT"

# JavaScript injected into every Frappe website page (Wiki, portal pages, etc.)
# This renders the floating Home button that returns users to /portal.
web_include_js = "/assets/msp_portal/js/portal_home_button.js"

# ── Third-party app tiles ────────────────────────────────────────────────────
# Static tiles (role-gated). Other apps add entries here via their own hooks.py.
# Example:
#   msp_portal_tiles = [
#       {
#           "title": "My Assets",
#           "description": "View managed equipment.",
#           "url": "/my-assets",
#           "icon": "box",
#           "order": 40,
#           "roles": ["Asset Customer"],
#       }
#   ]
msp_portal_tiles = []

# Dynamic tile providers – dotted paths to callables that receive (user) and
# return a list of tile dicts.  Errors are logged and skipped; they never break
# the page.
msp_portal_tile_providers = []

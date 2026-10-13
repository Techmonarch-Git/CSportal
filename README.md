# MSP Customer Portal (`msp_portal`)

Customer Portal Home for Frappe v16 / TechMonarch MSP.

After logging in, customers land on `/portal`, a clean dashboard with service cards:
- 🎫 **Helpdesk** — My Tickets, Create Ticket
- 📖 **Wiki SOPs** — Only the customer's assigned Wiki space (strict tenant isolation)
- 🏠 **Floating Home Button** — Persistent round orange button on all reader/helpdesk screens that returns users to `/portal`

---

## Architecture & Features

1. **Post-Login Landing (`/portal`)**:
   - `HD Customer` and `HD Customer Manager` roles are automatically directed to `/portal` upon logging in.
   - Built with TechMonarch design system (orange `#FF4C22` branding, responsive grid, empty states).

2. **Wiki Tenant Isolation**:
   - Each customer sees cards *only* for the Wiki spaces they have read access to (e.g. Pressurejet customer sees only Pressurejet SOPs, ISK customer sees only ISK SOPs).
   - Staff/Admins see all assigned spaces.

3. **Floating Home Button (⌂)**:
   - Injected on all website pages, Wiki documentation pages, and Helpdesk SPA.
   - Automatically hidden on `/portal`, login, and desk pages.
   - Shows only for logged-in users.

4. **Zero-Downtime Deployment**:
   - Automated script `deploy_portal.py` enables installation without stopping the server.

---

## One-Command Zero-Downtime Deployment

Inside your Frappe container / bench:
```bash
python3 apps/msp_portal/deploy_portal.py [your-site-name]
```
Or if running directly with Docker on host:
```bash
docker cp apps/msp_portal frappe:/home/frappe/frappe-bench/apps/
docker exec -u frappe frappe python3 /home/frappe/frappe-bench/apps/msp_portal/deploy_portal.py [your-site-name]
```

---

## File Structure

```
msp_portal/
├── deploy_portal.py              # Zero-downtime automated install & config script
├── pyproject.toml                # App packaging configuration
├── README.md
└── msp_portal/
    ├── __init__.py
    ├── hooks.py                  # Injects web_include_js and tile extension hooks
    ├── modules.txt
    ├── patches.txt
    ├── public/
    │   └── js/
    │       └── portal_home_button.js   # Floating Home icon widget
    └── www/
        ├── portal.py             # Context builder & tenant filtering
        └── portal.html           # Portal frontend template
```

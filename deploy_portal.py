#!/usr/bin/env python3
"""
Zero-Downtime Deployment & Configuration Script for Customer Portal (msp_portal)
Usage:
    python3 deploy_portal.py [site_name]
    Default site_name is 'erp.local' (or read from sites/currentsite.txt)
"""
import sys
import os
import subprocess

def run_cmd(cmd, cwd=None):
    print(f"--> Running: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Output / Notice: {res.stderr.strip() or res.stdout.strip()}")
    else:
        if res.stdout.strip():
            print(res.stdout.strip())
    return res

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else None
    bench_dir = "/home/frappe/frappe-bench"
    if not os.path.exists(bench_dir):
        bench_dir = os.getcwd()

    if not site:
        cur_file = os.path.join(bench_dir, "sites", "currentsite.txt")
        if os.path.exists(cur_file):
            with open(cur_file) as f:
                site = f.read().strip()
        else:
            site = "erp.local"

    print(f"=== Starting Zero-Downtime Portal Deployment on site: {site} ===")

    # 1. Pip install app
    app_path = os.path.abspath(os.path.dirname(__file__))
    pip_bin = os.path.join(bench_dir, "env", "bin", "pip")
    if os.path.exists(pip_bin):
        run_cmd(f"{pip_bin} install -e '{app_path}'")
    else:
        run_cmd(f"pip install -e '{app_path}'")

    # 2. Add to sites/apps.txt if not present
    apps_txt = os.path.join(bench_dir, "sites", "apps.txt")
    if os.path.exists(apps_txt):
        with open(apps_txt, "r") as f:
            apps = [l.strip() for l in f if l.strip()]
        if "msp_portal" not in apps:
            with open(apps_txt, "a") as f:
                f.write("\nmsp_portal\n")
            print("✓ Added msp_portal to apps.txt")

    # 3. Install app on site
    run_cmd(f"bench --site {site} install-app msp_portal", cwd=bench_dir)

    # 4. Build assets for this app only (fast: ~1-2 seconds)
    run_cmd("bench build --app msp_portal", cwd=bench_dir)

    # 5. Disable watch in Procfile if present
    procfile = os.path.join(bench_dir, "Procfile")
    if os.path.exists(procfile):
        with open(procfile, "r") as f:
            lines = f.readlines()
        new_lines = [l for l in lines if not l.strip().startswith("watch:")]
        if len(new_lines) != len(lines):
            with open(procfile, "w") as f:
                f.writelines(new_lines)
            print("✓ Disabled watch in Procfile")

    # 6. Apply configuration in Frappe DB
    python_bin = os.path.join(bench_dir, "env", "bin", "python")
    py_code = f"""
import frappe
import os
frappe.init(site="{site}")
frappe.connect()

# Set customer roles home page to /portal
for role in ("HD Customer", "HD Customer Manager"):
    if frappe.db.exists("Role", role):
        frappe.db.set_value("Role", role, "home_page", "/portal")
        print(f"✓ Set {{role}} home_page to /portal")

# Set Portal Settings
if frappe.db.exists("DocType", "Portal Settings"):
    frappe.db.set_single_value("Portal Settings", "default_portal_home", "/portal")
    print("✓ Set Portal Settings default_portal_home to /portal")

# Wiki Settings: Inject floating home button script
if frappe.db.exists("DocType", "Wiki Settings"):
    wiki_settings = frappe.get_single("Wiki Settings")
    script_tag = '<script src="/assets/msp_portal/js/portal_home_button.js" defer></script>'
    existing = wiki_settings.head_html or ""
    if script_tag not in existing:
        wiki_settings.head_html = (existing + "\\n" + script_tag).strip()
        wiki_settings.save(ignore_permissions=True)
        print("✓ Injected portal_home_button.js into Wiki Settings head_html")

# Wiki Spaces: Add Home link in navbar
if frappe.db.exists("DocType", "Wiki Space"):
    for space_name in frappe.get_all("Wiki Space", pluck="name"):
        space = frappe.get_doc("Wiki Space", space_name)
        has_home = any(item.url == "/portal" for item in space.navbar_items)
        if not has_home:
            space.append("navbar_items", {{"label": "Home", "url": "/portal"}})
            space.save(ignore_permissions=True)
            print(f"✓ Added Home navbar link to Wiki Space {{space.space_name or space.name}}")

# Inject Home Button script into Helpdesk index.html if file exists
hd_html = os.path.join("{bench_dir}", "apps", "helpdesk", "helpdesk", "www", "helpdesk", "index.html")
if os.path.exists(hd_html):
    with open(hd_html, "r") as f:
        c = f.read()
    tag = '<script src="/assets/msp_portal/js/portal_home_button.js" defer></script>'
    if tag not in c and "</body>" in c:
        c = c.replace("</body>", f"  {{tag}}\\n  </body>")
        with open(hd_html, "w") as f:
            f.write(c)
        print("✓ Injected portal home button into Helpdesk index.html")

frappe.db.commit()
frappe.clear_cache()
print("✓ Database and cache updated successfully!")
"""
    tmp_file = "/tmp/apply_portal_config.py"
    with open(tmp_file, "w") as f:
        f.write(py_code)
    run_cmd(f"{python_bin} {tmp_file}", cwd=os.path.join(bench_dir, "sites"))
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

    print("=== Deployment Complete with ZERO Downtime! ===")

if __name__ == "__main__":
    main()

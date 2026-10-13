/**
 * Portal Home Button – floating ⌂ icon (bottom-left).
 *
 * Injected via `web_include_js` on every Frappe website page.
 * - Shows for logged-in users only.
 * - Hides itself on /portal, /login, and Desk (/app) pages.
 * - Keyboard-focusable (Tab → Enter).
 */
(function () {
  "use strict";

  // ── Which pages should NOT show the button? ────────────────────────────
  var path = window.location.pathname;

  // Hide on portal itself, login, and desk
  if (
    path === "/portal" ||
    path === "/portal/" ||
    path.indexOf("/login") === 0 ||
    path.indexOf("/app") === 0
  ) {
    return;
  }

  // ── Detect logged-in state ─────────────────────────────────────────────
  // Works for Frappe website pages and Wiki pages.
  function isLoggedIn() {
    // Frappe website pages set window.frappe
    if (window.frappe && window.frappe.session) {
      return window.frappe.session.user !== "Guest";
    }
    // Fallback: check the user_id cookie
    var match = document.cookie.match(/(?:^|;\s*)user_id=([^;]*)/);
    if (match) {
      var uid = decodeURIComponent(match[1]);
      return uid && uid !== "Guest";
    }
    return false;
  }

  // Delay slightly so Frappe has time to set session on the window
  setTimeout(function () {
    if (!isLoggedIn()) return;

    // ── Create the button ──────────────────────────────────────────────
    var btn = document.createElement("a");
    btn.href = "/portal";
    btn.setAttribute("aria-label", "Back to Portal Home");
    btn.setAttribute("title", "Portal Home");
    btn.setAttribute("role", "button");
    btn.id = "msp-portal-home-btn";

    btn.style.cssText = [
      "position:fixed",
      "bottom:24px",
      "left:24px",
      "z-index:99999",
      "width:48px",
      "height:48px",
      "border-radius:50%",
      "background:#FF4C22",
      "color:#fff",
      "display:flex",
      "align-items:center",
      "justify-content:center",
      "box-shadow:0 4px 14px rgba(255,76,34,0.45)",
      "cursor:pointer",
      "text-decoration:none",
      "transition:transform 0.2s ease, box-shadow 0.2s ease",
      "opacity:0",
      "animation:mspFadeIn 0.3s ease 0.5s forwards",
    ].join(";");

    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22"' +
      ' viewBox="0 0 24 24" fill="none" stroke="currentColor"' +
      ' stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>' +
      '<polyline points="9 22 9 12 15 12 15 22"/></svg>';

    btn.addEventListener("mouseenter", function () {
      btn.style.transform = "scale(1.12)";
      btn.style.boxShadow = "0 6px 18px rgba(255,76,34,0.55)";
    });
    btn.addEventListener("mouseleave", function () {
      btn.style.transform = "scale(1)";
      btn.style.boxShadow = "0 4px 14px rgba(255,76,34,0.45)";
    });

    // ── Fade-in keyframe (injected once) ─────────────────────────────
    if (!document.getElementById("msp-portal-home-style")) {
      var style = document.createElement("style");
      style.id = "msp-portal-home-style";
      style.textContent =
        "@keyframes mspFadeIn{from{opacity:0;transform:translateY(12px)}" +
        "to{opacity:1;transform:translateY(0)}}";
      document.head.appendChild(style);
    }

    document.body.appendChild(btn);
  }, 300);
})();

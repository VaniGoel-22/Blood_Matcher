const GROUPS = ["A+","A-","B+","B-","AB+","AB-","O+","O-"];
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function api(path, options) {
  const res = await fetch("/api" + path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong. Try again.");
  return data;
}
const post = body => ({ method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body) });
function show(el, html, ok = true) { el.innerHTML = html; el.className = "msg " + (ok ? "ok" : "err"); }
function fillGroups(id) { $(id).innerHTML = '<option value="">Select</option>' + GROUPS.map(g => `<option>${g}</option>`).join(""); }

const PAGES = [["/", "Home"], ["/find", "Find donors"], ["/register", "Become a donor"], ["/dashboard", "Donor dashboard"], ["/track", "Track request"]];
const THEMES = { "/find": "find", "/register": "register", "/dashboard": "dashboard", "/track": "track" };

const SMILING_HEART = `<svg viewBox="0 0 200 200" aria-hidden="true">
  <path d="M100 180C30 128 8 88 18 56c10-32 62-38 82 4 20-42 72-36 82-4 10 32-12 72-82 124z" fill="#d4202e"/>
  <ellipse cx="68" cy="82" rx="8" ry="11" fill="#fff"/><ellipse cx="132" cy="82" rx="8" ry="11" fill="#fff"/>
  <circle cx="70" cy="85" r="4" fill="#1c1b1f"/><circle cx="134" cy="85" r="4" fill="#1c1b1f"/>
  <ellipse cx="52" cy="108" rx="11" ry="7" fill="#ff8f99" opacity=".7"/><ellipse cx="148" cy="108" rx="11" ry="7" fill="#ff8f99" opacity=".7"/>
  <path d="M74 112c8 20 44 20 52 0" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>
</svg>`;

function showSplash() {
  const s = document.createElement("div");
  s.className = "splash";
  s.innerHTML = `${SMILING_HEART}<p>Welcome to Blood Matcher<small>Every donation can save a life</small></p>`;
  document.body.appendChild(s);
  setTimeout(() => s.classList.add("hide"), 2200);
  setTimeout(() => s.remove(), 2800);
}

document.addEventListener("DOMContentLoaded", () => {
  const here = location.pathname;
  document.body.classList.add("theme-" + (THEMES[here] || "home"));

  $("site-header").innerHTML = `<div class="topbar"><a class="brand" href="/">
    <svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 29C7 22 3 16 3 11a6.5 6.5 0 0 1 13-1 6.5 6.5 0 0 1 13 1c0 5-4 11-13 18z" fill="currentColor"/></svg>Blood Matcher</a>
    <nav>${PAGES.map(([h, t]) => `<a href="${h}"${h === here ? ' aria-current="page"' : ""}>${t}</a>`).join("")}</nav></div>`;
  $("site-footer").innerHTML = "<strong>Every donation can save a life.</strong> In an emergency, call your local emergency number first.";

  // smiling heart: shown once each time the app is opened (not on every page change)
  try {
    if (!sessionStorage.getItem("welcomed")) {
      sessionStorage.setItem("welcomed", "1");
      showSplash();
    }
  } catch (e) { showSplash(); }
});
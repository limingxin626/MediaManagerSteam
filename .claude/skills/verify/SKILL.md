---
name: verify
summary: Drive the Vue app and backend API for runtime verification.
---

# Runtime verification

- Start backend: `cd backend && .venv/Scripts/python.exe api.py` (port 8002; reuse an existing process if occupied).
- Start Vue: `pnpm --dir vue dev` and use the Vite-reported port.
- Browser automation: use `pnpm dlx playwright`; install Chromium once with `pnpm dlx playwright install chromium`.
- The current backend may omit CORS headers for Vite origins; launch Chromium with `--disable-web-security` when verifying the Vue UI against port 8002.
- Capture request URLs, console errors, and a screenshot. Local media paths may produce `ERR_UNKNOWN_URL_SCHEME` in headless Chromium; distinguish these from API/UI failures.

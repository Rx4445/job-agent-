# Project rules
- I'm building this to learn and get hired as an Agentic AI Engineer. Explain each step before I do it.
- Work in meaningful chunks, but stop before committing. Show me the diff and the test results, and explain each change in simple terms. Never commit without my confirmation.
- Let me write the core logic myself. Give hints first, code only if I'm stuck.
- After each feature, quiz me with 2-3 questions on how it works.
- Build the agent loop by hand before using any framework.
- Every feature needs a test or eval before it's marked done.

# Workflow
- At the start of every session, read PROGRESS.md to see where we are.
- After each completed step, update PROGRESS.md.
- After finishing a feature, write or update docs/<feature>.md with the approach, decisions, and how to test it.
- Never put secrets or API keys in files.
- At the start of every session / log-on, give a rough target estimate of what should ideally be accomplished in the session (calibrated to weekday ~3hr or weekend full-day capacity) to calibrate speed and growth.
- Session Logging & Debounce Rule: 15 minutes of inactivity marks an official log-off; any message after 15+ mins begins a new session. If user says log-off but keeps prompting within 15 mins, the session stays active.
- Whenever a session logs off, log the session duration, accomplished vs expected velocity %, and update METRICS.md with visual trend charts.
- Whenever I say I'm logging off, review what was accomplished vs what was expected.
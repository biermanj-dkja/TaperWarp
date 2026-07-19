# Security Policy

TaperWarp is designed to be fully offline: it performs no network
communication and contains no telemetry, analytics, credentials, or
auto-update mechanism. It never executes user-provided code or external
binaries, and writes only to user-selected output paths.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via GitHub's
"Report a vulnerability" (Security Advisories) feature on this repository
rather than opening a public issue. Include reproduction steps and affected
versions. We aim to acknowledge reports within 7 days.

## Scope of interest

- Any code path that could read or write outside user-selected files
- Malformed PNG/JPEG/SVG inputs causing crashes or memory exhaustion
- Any behavior contradicting the offline guarantees above

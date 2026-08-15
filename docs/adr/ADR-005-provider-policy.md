# ADR-005: Official provider APIs and local validation

Status: accepted

## Context

The original specification allowed unofficial DeepSeek, Gemini, and ChatGPT
endpoints. Session scraping and unofficial account endpoints are unstable,
unsafe for credentials, and unsuitable for an enterprise product.

## Decision

Production builds integrate only official, authorized APIs. Provider-specific
payloads remain behind adapters. Every response is treated as untrusted input
and passes strict schema plus application-level semantic validation. Offline
mode blocks all external calls through the central privacy policy.

## Consequences

- Provider outages do not prevent project access or manual editing.
- Official API usage, retention, region, and cost are visible configuration.
- JSON validity alone is insufficient; language, terminology, duration, and
  story-preservation rules are separately validated.
- Provider/model changes require contract and quality-regression tests.


# Interactive Atlas — User Guide
**Module:** ITM-ORG-009 · **Issue:** 001 · **Date:** 2026-10-13

## Launch

Open [Interactive Atlas](../index.html) from a static HTTP host. For a local preview, from the **repository root** run:

```bash
python -m http.server 8000
```

Then visit:
`http://localhost:8000/manuals/enterprise-tech-operating-atlas/`

**GitHub Pages:** This interface is static and can be hosted with GitHub Pages once repository Pages settings publish the relevant directory/root. This commit does not enable repository Pages settings or provide a verified public deployment.

## Workspace operation

1. **Organisation:** Search and filter all 36 role families. Select API Platform to see illustrative hierarchy, function, partners, escalation and system ownership.
2. **Dependencies:** Select LOS, LMS, Gateway or another service. View direct upstream and downstream connections, interface contracts, engineering owner and business owner. Click connected cards to traverse the graph. Copy Mermaid source for documentation use.
3. **Incidents:** Select CORS, 502/504, LOS/LMS reporting mismatch or ML drift. View first-line checks, service impact and escalation.
4. **Change & RACI:** Enter change name and description. Select a template (or suggest one by keywords), generate draft RACI, checklist and control review, then copy or download as Markdown.

## Data and governance

- `data/atlas.json`: reference roles, groups, system nodes, edges, incidents, controls, templates and RACI.
- All generated guidance is *deterministic*, based on authored templates, **not** a model-based risk assessment. It runs in the browser.
- The interface does **not** collect personally identifying customer data or connect to bank services. Do not enter confidential or customer-specific information, particularly if hosting publicly.
- The source describes **fictional IndiaOne Bank**. The organisational roles are generic examples, not verified staffing or service ownership.
- RACI, severity, compliance and escalation require confirmation with real business, technology and security owners.
- Browser fetch requires HTTP; direct `file://` opening may block the JSON request.

## Validation and maintenance

GitHub Actions runs `scripts/validate_atlas.py` and `node --check` when atlas paths change. The Python check requires no external packages and catches duplicate IDs, missing owners, dangling references, inconsistent downstream edges and incomplete templates.

Use `python manuals/enterprise-tech-operating-atlas/scripts/validate_atlas.py` to validate locally.

## Example questions

- Who owns API routing, and which teams collaborate with them?
- Which dependencies connect LOS to LMS and reporting?
- Who investigates a 502 response versus an incorrect eligibility calculation?
- Which RACI tasks and regression tests apply when a sent-back case process changes?

## Limits

This version provides a clickable relationship pathway and Mermaid source, not a hosted Mermaid renderer. It does not automatically discover production services or inspect logs. Adding production discovery would require credentials, integrations, access control and a clearly defined review process.

#!/usr/bin/env python3
"""Validate the Enterprise Tech Operating Atlas reference graph. stdlib only."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "atlas.json"

def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    failures = []
    def check(ok, msg):
        if not ok:
            failures.append(msg)
    def distinct(objs, label):
        ids = [x["id"] for x in objs]
        check(len(ids) == len(set(ids)), f"{label}: duplicate IDs")
        return set(ids)
    groups = distinct(data["groups"], "groups")
    roles = distinct(data["roles"], "roles")
    systems = distinct(data["systems"], "systems")
    incidents = distinct(data["incidents"], "incidents")
    templates = distinct(data["templates"], "templates")
    controls = distinct(data["controls"], "controls")
    check(len(groups) == 5, "Expected 5 reference role groups")
    check(len(roles) == 36, "Expected 36 role functions")
    check(len(systems) >= 10, "Expected at least 10 service nodes")
    check({"cors", "http502", "data_mismatch", "ml_drift"} <= incidents, "Missing required incident examples")
    check(bool(templates), "No change templates defined")
    for role in data["roles"]:
        check(role["group"] in groups, f"role {role['id']}: unknown group")
        check(bool(role["name"] and role["hierarchy"] and role["escalation"]), f"role {role['id']}: missing hierarchy/escalation")
        for rel in role["collaborates"]:
            check(rel in roles, f"role {role['id']}: missing collaborator {rel}")
    for system in data["systems"]:
        check(system["owner"] in roles, f"system {system['id']}: missing technical owner")
        check(bool(system["businessOwner"]), f"system {system['id']}: no business owner")
        check(bool(system["contracts"]), f"system {system['id']}: no contracts")
        for upstream in system["upstream"]:
            check(upstream in systems, f"system {system['id']}: missing upstream {upstream}")
        expected = {x["id"] for x in data["systems"] if system["id"] in x["upstream"]}
        check(set(system["downstream"]) == expected, f"system {system['id']}: inconsistent downstream links")
    for incident in data["incidents"]:
        check(incident["primary"] in roles, f"incident {incident['id']}: missing owner")
        check(bool(incident["checks"]) and bool(incident["escalation"]), f"incident {incident['id']}: empty checks or escalation")
        for rid in incident["consult"]:
            check(rid in roles, f"incident {incident['id']}: unknown consultant {rid}")
        for sid in incident["systems"]:
            check(sid in systems, f"incident {incident['id']}: unknown system {sid}")
    for template in data["templates"]:
        check(bool(template["checks"]), f"template {template['id']}: empty checklist")
        for sid in template["defaultSystems"]:
            check(sid in systems, f"template {template['id']}: missing default system {sid}")
        for item in template["raci"]:
            check(bool(item["task"]), f"template {template['id']}: missing task")
            for rid in [item["r"], item["a"], *item["c"], *item["i"]]:
                check(rid in roles, f"template {template['id']}: unknown RACI role {rid}")
    for control in data["controls"]:
        check(control["owner"] in roles, f"control {control['id']}: owner not found")
        for rid in control["consult"]:
            check(rid in roles, f"control {control['id']}: consultant not found {rid}")
        for tid in control["applies"]:
            check(tid in templates, f"control {control['id']}: invalid change template {tid}")
    for static in ("index.html", "assets/atlas.css", "assets/atlas.js"):
        check((ROOT / static).is_file(), f"Missing user interface file: {static}")
    if failures:
        print("Atlas validation FAILED:")
        for failure in failures:
            print(" -", failure)
        return 1
    print(f"Atlas valid: {len(roles)} roles / {len(systems)} systems / "
          f"{len(incidents)} incidents / {len(templates)} templates / {len(controls)} controls")
    return 0

if __name__ == "__main__":
    sys.exit(main())

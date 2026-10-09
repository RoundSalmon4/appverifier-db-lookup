#!/usr/bin/env python3
"""Generate the AppVerifier DB lookup site.

Inputs:
  - Privacy Guides verified-apps data.yml (attestation verified by the workflow)
  - AppVerifier BG rotated keys store (optional)

Outputs, written into --outdir:
  - data.json    machine readable payload for the page
  - index.html   static page copied from the template

The site is an unofficial, more frequently refreshed view of the upstream
verified-apps data with rotated keys merged in. Upstream stays canonical.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys

import yaml


def normalize_fp(fp):
    """Return a colon separated SHA-256 fingerprint, or None if invalid."""
    if not fp:
        return None
    cleaned = re.sub(r"\s+", "", fp).replace(":", "").upper()
    if len(cleaned) != 64 or any(c not in "0123456789ABCDEF" for c in cleaned):
        return None
    return ":".join(cleaned[i:i + 2] for i in range(0, 64, 2))


def load_data_yml(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict):
        return data.get("packages") or []
    return data or []


def parse_upstream(entries):
    packages = {}
    for app in entries:
        pkg = app.get("package")
        if not pkg:
            continue
        signatures = []
        for sig in app.get("signature") or []:
            raw = sig.get("fingerprint") or ""
            fps = []
            for line in raw.splitlines():
                n = normalize_fp(line)
                if n and n not in fps:
                    fps.append(n)
            sources = []
            for src in sig.get("sources") or []:
                apk = src.get("apk") or {}
                sources.append({
                    "name": src.get("name") or "",
                    "issue": src.get("issue") or "",
                    "sha256": apk.get("sha256") or "",
                    "link": apk.get("link") or "",
                })
            if fps or sources:
                signatures.append({"fingerprints": fps, "sources": sources})
        packages[pkg] = {"signatures": signatures, "rotated": []}
    return packages


def parse_rotated(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for entry in data.get("entries") or []:
        pkg = entry.get("package")
        keys = []
        for k in entry.get("keys") or []:
            n = normalize_fp(k)
            if n and n not in keys:
                keys.append(n)
        if pkg and keys:
            out[pkg] = {"keys": keys, "source_issue": entry.get("source_issue")}
    return out


def build(upstream_entries, rotated):
    packages = parse_upstream(upstream_entries)
    for pkg, info in rotated.items():
        node = packages.setdefault(pkg, {"signatures": [], "rotated": []})
        known = set()
        for sig in node["signatures"]:
            known.update(sig["fingerprints"])
        node["rotated"] = [k for k in info["keys"] if k not in known]

    result = []
    for pkg, node in packages.items():
        all_fps = []
        for sig in node["signatures"]:
            for fp in sig["fingerprints"]:
                if fp not in all_fps:
                    all_fps.append(fp)
        for fp in node["rotated"]:
            if fp not in all_fps:
                all_fps.append(fp)
        result.append({
            "package": pkg,
            "signatures": node["signatures"],
            "rotated": node["rotated"],
            "all_fingerprints": all_fps,
        })
    result.sort(key=lambda p: p["package"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-yml", required=True)
    parser.add_argument("--rotated-json", default="")
    parser.add_argument("--template", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    entries = load_data_yml(args.data_yml)
    rotated = parse_rotated(args.rotated_json)
    packages = build(entries, rotated)

    os.makedirs(args.outdir, exist_ok=True)
    payload = {
        "generated": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "upstream": "https://github.com/privacyguides/verified-apps",
        "upstream_site": "https://privacyguides.github.io/verified-apps/",
        "count": len(packages),
        "rotated_count": sum(1 for p in packages if p["rotated"]),
        "packages": packages,
    }
    with open(os.path.join(args.outdir, "data.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    shutil.copyfile(args.template, os.path.join(args.outdir, "index.html"))

    print(f"wrote {len(packages)} packages, {payload['rotated_count']} with rotated keys")
    print(f"generated {payload['generated']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
portfolio-sync — an AUDIT-TIME helper that refreshes the git facts in command/portfolio.json.

The dashboard's "Sync latest from main" button just re-reads the committed portfolio.json — no token, no
cron, no cross-repo API. This script is run manually as part of a re-audit (when someone with `gh` access
to both repos regenerates the portfolio), to refresh ahead/behind, last-commit date, and open-PR count per
project's branch, then the result is committed to main. The curated narrative fields are the AI audit.
Resilient: any lookup that fails keeps the existing value.
"""
import json, subprocess, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PJSON = ROOT / "command" / "portfolio.json"
SLUG = {"wok": "abbas-MyPeople/WokAndKarahiTexas.com", "az": "abbas-MyPeople/AZ"}


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    return (r.stdout.strip() if r.returncode == 0 else None)


def refresh(p):
    slug = SLUG.get(p.get("repo"))
    branch = p.get("branch") or "main"
    if not slug:
        return
    g = p.setdefault("git", {})
    # ahead/behind vs main
    if branch != "main":
        cmp = gh("api", f"repos/{slug}/compare/main...{branch}", "--jq", "{a:.ahead_by,b:.behind_by}")
        if cmp:
            try:
                d = json.loads(cmp); g["ahead"] = d["a"]; g["behind"] = d["b"]
            except Exception:
                pass
    else:
        g["ahead"] = 0; g["behind"] = 0
    # last commit date
    dt = gh("api", f"repos/{slug}/commits/{branch}", "--jq", ".commit.committer.date")
    if dt:
        g["last_commit"] = dt[:10]
    # open PRs from this branch
    prs = gh("pr", "list", "--repo", slug, "--state", "open", "--head", branch, "--json", "number")
    if prs is not None:
        try:
            g["open_prs"] = len(json.loads(prs))
        except Exception:
            pass


def main():
    data = json.loads(PJSON.read_text())
    for p in data["projects"]:
        try:
            refresh(p)
        except Exception as e:  # never let one project break the sync
            print(f"skip {p.get('id')}: {e}")
    data["meta"]["last_git_sync"] = datetime.date.today().isoformat()
    PJSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"portfolio-sync: refreshed {len(data['projects'])} projects · {data['meta']['last_git_sync']}")


if __name__ == "__main__":
    main()

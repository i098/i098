#!/usr/bin/env python3
"""Render stats.svg: the frozen undeemed numbers (Sept 19, 2026) plus everything new on i098.

Reads base.json and stats.template.svg, asks the GitHub GraphQL API for i098's public
numbers, adds them to the frozen base, and writes stats.svg. Needs GITHUB_TOKEN.
"""
import json, os, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERY = """query($login: String!) { user(login: $login) {
  pullRequests { totalCount }
  issues { totalCount }
  repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
  contributionsCollection { totalCommitContributions }
  repositories(first: 100, ownerAffiliations: OWNER, isFork: false) { nodes { stargazerCount } }
} }"""


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    return {
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "contribs": u["repositoriesContributedTo"]["totalCount"],
    }


def k(n):
    # Same short form as github-readme-stats: 1234 -> 1.2k
    return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k" if n >= 1000 else str(n)


def main():
    base = json.load(open(os.path.join(ROOT, "base.json")))
    new = fetch(base["login"])
    svg = open(os.path.join(ROOT, "stats.template.svg")).read()
    for key in ("stars", "commits", "prs", "issues", "contribs"):
        svg, hits = re.subn(rf'(data-testid="{key}"\s*>)[^<]*(</text>)', rf"\g<1>{k(base[key] + new[key])}\g<2>", svg)
        assert hits == 1, key
    open(os.path.join(ROOT, "stats.svg"), "w").write(svg)
    print(json.dumps({"base": base, "new": new}))


if __name__ == "__main__":
    assert k(61) == "61" and k(4500) == "4.5k" and k(1600) == "1.6k" and k(4549) == "4.5k" and k(1000) == "1k"
    main()

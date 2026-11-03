"""Advisory public-baseline search, not provenance or an execution adapter.

Run from the project root: python3 tests/baseline_discovery.py
Inspect a result with --repository OWNER/REPO, then use --revision COMMIT
--acquire-native to retain its Q1/Q2 RTL without replacing project sources.
Use --references to inspect public branches/tags/releases separately from the
default-branch source tree; a planned README entry is not an executable Q4.
Use --forks to discover public fork candidates separately; a fork's name or
default branch is not an immutable source identity or an execution adapter.
Use --q4-history to inspect the first page of Q4 path history reachable from
the selected immutable commit; deleted historical sources need separate intake.
Use --pull-requests to retain public PR head commits independently of branches
and releases; a PR title or head identity is not validated baseline content.
Use --q4-commits to search public commit messages independently of path names;
message matches are candidates, not evidence that Q4 RTL exists.
Use --q4-issues to discover public Q4 discussions independently of source paths;
issue links are mutable leads, not baseline provenance or executable assets.
Each invocation retains fresh receipts under evidence/preparation/. Search
results are candidates only: identity, immutable revision, license, actual
content hashes and source-bound execution must be established separately.
Acquired README/license/version documents and RTL must match the selected
immutable tree's regular-file size and Git blob identity before being indexed.
Offline sensitivity: python3 tests/prepare.py --probe baseline-index-checker
An empty bounded GitHub search does not prove that no baseline exists.
The Q4 repository query includes forks, which GitHub otherwise excludes.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, sha256, write_json


QUERIES = (
    '"Anvil-Q1" in:name,description,readme',
    '"Anvil-Q2" in:name,description,readme',
    '"Anvil-Q4" in:name,description,readme fork:true',
    'anvil Qwen FPGA in:name,description,readme',
)


def discover(run):
    run.versions([("python3", "--version"), ("curl", "--version")])
    declared = json.loads((ROOT / "tests/public_assets.json").read_text())["assets"]
    provenance = json.loads((ROOT / "design/model_provenance.json").read_text())
    declared.extend(provenance.get("generation_baselines", []))
    report = {
        "schema": 1,
        "scope": "bounded unauthenticated public GitHub repository search",
        "acceptance_evidence": False,
        "declared_baseline_count": sum(a["category"] == "baseline" for a in declared),
        "supplied_q2_source_hashes": {
            name: value for name, value in run.hashes.items()
            if name.startswith("anvil_q2_reference/rtl/")
        },
        "searches": [],
        "limitations": [
            "Repository search is not exhaustive code search or proof of absence.",
            "Search hits are not validated baseline identities, licenses or adapters.",
            "Supplied Q2 and its Q1-compatible wrapper are not independent Q1/Q4 assets.",
        ],
    }
    for query in QUERIES:
        url = "https://api.github.com/search/repositories?" + urlencode(
            {"q": query, "per_page": 10, "page": 1})
        headers = run.path / f"search-{len(report['searches'])}-headers.txt"
        text, receipt = run.tool([
            "curl", "--disable", "--silent", "--show-error", "--location",
            "--proto", "=https", "--proto-redir", "=https",
            "--connect-timeout", "30", "--max-time", "120",
            "--max-filesize", "1048576", "--dump-header", run.rel(headers),
            "--header", "Accept: application/vnd.github+json",
            "--header", "X-GitHub-Api-Version: 2022-11-28", url,
        ])
        payload = json.loads(text)
        row = {"query": query, "url": url, "raw_stdout": receipt["stdout"],
               "raw_sha256": sha256(ROOT / receipt["stdout"]),
               "headers": run.rel(headers)}
        if "items" not in payload:
            row["error"] = payload
        else:
            if (type(payload.get("total_count")) is not int or
                    type(payload.get("incomplete_results")) is not bool or
                    not isinstance(payload["items"], list)):
                raise AssertionError("malformed GitHub repository search response")
            row.update({
                "total_count": payload["total_count"],
                "incomplete_results": payload["incomplete_results"],
                "candidates": [
                    {"repository": item["full_name"], "url": item["html_url"],
                     "description": item["description"], "fork": item["fork"],
                     "archived": item["archived"],
                     "license_metadata": item["license"]}
                    for item in payload["items"]
                ],
            })
        report["searches"].append(row)
        write_json(run.path / "baseline-discovery.json", report)
    return report


def reference_entries(kind, payload):
    if kind not in ("branches", "tags", "releases"):
        raise ValueError("unsupported public reference kind")
    if not isinstance(payload, list):
        raise AssertionError("malformed public " + kind + " response")
    entries = []
    for item in payload:
        if not isinstance(item, dict):
            raise AssertionError("malformed public " + kind + " entry")
        if kind in ("branches", "tags"):
            name = item.get("name")
            commit = item.get("commit")
            revision = commit.get("sha") if isinstance(commit, dict) else None
            if (not isinstance(name, str) or not name or
                    not isinstance(revision, str) or
                    not re.fullmatch(r"[a-f0-9]{40}", revision)):
                raise AssertionError("public reference lacks name/immutable commit")
            entries.append({"name": name, "revision": revision})
        elif kind == "releases":
            name = item.get("tag_name")
            if not isinstance(name, str) or not name:
                raise AssertionError("public release lacks tag identity")
            entries.append({"tag_name": name, "target_commitish": item.get("target_commitish"),
                            "draft": item.get("draft"), "prerelease": item.get("prerelease"),
                            "scope": "release metadata, not a resolved immutable source revision"})
    return entries


def fork_entries(payload):
    if not isinstance(payload, list):
        raise AssertionError("malformed public forks response")
    entries = []
    for item in payload:
        if not isinstance(item, dict):
            raise AssertionError("malformed public fork entry")
        repository = item.get("full_name")
        branch = item.get("default_branch")
        if (not isinstance(repository, str) or
                not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or
                any(part in (".", "..") for part in repository.split("/")) or
                not isinstance(branch, str) or not branch or item.get("fork") is not True):
            raise AssertionError("public fork lacks repository/default-branch identity")
        entries.append({"repository": repository, "default_branch": branch,
                        "scope": "candidate only; immutable source inspection required"})
    return entries


def q4_history_entries(payload):
    if not isinstance(payload, list):
        raise AssertionError("malformed public Q4 path history response")
    entries = []
    for item in payload:
        if (not isinstance(item, dict) or not isinstance(item.get("sha"), str) or
                not re.fullmatch(r"[a-f0-9]{40}", item["sha"])):
            raise AssertionError("public Q4 path history lacks immutable commit identity")
        entries.append({"revision": item["sha"]})
    return entries


def commit_search_entries(payload, repository):
    if (not isinstance(payload, dict) or
            type(payload.get("total_count")) is not int or payload["total_count"] < 0 or
            type(payload.get("incomplete_results")) is not bool or
            not isinstance(payload.get("items"), list)):
        raise AssertionError("malformed public commit search response")
    entries = []
    for item in payload["items"]:
        if (not isinstance(item, dict) or
                not isinstance(item.get("sha"), str) or
                not re.fullmatch(r"[a-f0-9]{40}", item["sha"]) or
                not isinstance(item.get("repository"), dict) or
                not isinstance(item["repository"].get("full_name"), str) or
                item["repository"].get("full_name", "").casefold() != repository.casefold()):
            raise AssertionError("public commit search lacks source-bound commit identity")
        entries.append({"revision": item["sha"]})
    if payload["total_count"] < len(entries):
        raise AssertionError("public commit search count contradicts returned candidates")
    return entries


def pull_request_entries(payload):
    if not isinstance(payload, list):
        raise AssertionError("malformed public pull requests response")
    entries = []
    for item in payload:
        if not isinstance(item, dict):
            raise AssertionError("malformed public pull request entry")
        head = item.get("head")
        repository = head.get("repo") if isinstance(head, dict) else None
        revision = head.get("sha") if isinstance(head, dict) else None
        number = item.get("number")
        state = item.get("state")
        if (type(number) is not int or number <= 0 or state not in ("open", "closed") or
                not isinstance(revision, str) or
                not re.fullmatch(r"[a-f0-9]{40}", revision)):
            raise AssertionError("public pull request lacks number/state/immutable head")
        # Deleted forks have null repo metadata; never invent an owner for them.
        name = repository.get("full_name") if isinstance(repository, dict) else None
        if repository is not None and (
                not isinstance(name, str) or
                not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name) or
                any(part in (".", "..") for part in name.split("/"))):
            raise AssertionError("public pull request has malformed head repository")
        entries.append({"number": number, "state": state, "repository": name,
                        "revision": revision,
                        "scope": "candidate head only; license/content/adapter validation required"})
    return entries


def issue_search_entries(payload, repository):
    if (not isinstance(payload, dict) or
            type(payload.get("total_count")) is not int or payload["total_count"] < 0 or
            type(payload.get("incomplete_results")) is not bool or
            not isinstance(payload.get("items"), list)):
        raise AssertionError("malformed public issue search response")
    entries = []
    base = "https://api.github.com/repos/" + repository
    for item in payload["items"]:
        if (not isinstance(item, dict) or type(item.get("number")) is not int or
                item["number"] <= 0 or item.get("state") not in ("open", "closed") or
                not isinstance(item.get("repository_url"), str) or
                item["repository_url"].casefold() != base.casefold() or
                "pull_request" in item or
                not isinstance(item.get("title"), str) or
                item.get("html_url") != "https://github.com/" + repository +
                "/issues/" + str(item["number"])):
            raise AssertionError("public issue search lacks source-bound discussion identity")
        entries.append({"number": item["number"], "state": item["state"],
                        "title": item["title"], "url": item["html_url"],
                        "scope": "mutable discussion lead only; not baseline source identity"})
    if payload["total_count"] < len(entries):
        raise AssertionError("public issue search count contradicts returned candidates")
    return entries


def verify_indexed_blob(item, content):
    if (item.get("type") != "blob" or item.get("mode") != "100644" or
            type(item.get("size")) is not int or not 0 < item["size"] <= 4194304 or
            not isinstance(item.get("sha"), str) or
            not re.fullmatch(r"[a-f0-9]{40}", item["sha"])):
        raise AssertionError("candidate content is not a bounded regular indexed blob")
    git_hash = hashlib.sha1(
        b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    if len(content) != item["size"] or git_hash != item["sha"]:
        raise AssertionError("candidate content differs from immutable source index")


def inspect_candidate(run, repository, revision=None, acquire_native=False, references=False,
                      forks=False, q4_history=False, pull_requests=False, q4_commits=False,
                      q4_issues=False):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("candidate must be a public owner/repository name")
    run.versions([("python3", "--version"), ("curl", "--version")])

    def fetch(url):
        text, receipt = run.tool([
            "curl", "--disable", "--silent", "--show-error", "--fail", "--location",
            "--proto", "=https", "--proto-redir", "=https",
            "--connect-timeout", "30", "--max-time", "120",
            "--max-filesize", "4194304", url,
        ])
        return text, {"url": url, "retained_path": receipt["stdout"],
                      "size_bytes": (ROOT / receipt["stdout"]).stat().st_size,
                      "sha256": sha256(ROOT / receipt["stdout"])}

    base = "https://api.github.com/repos/" + repository
    commit_record = None
    if revision is None:
        text, commit_record = fetch(base + "/commits?per_page=1")
        commit = json.loads(text)[0]
        revision = commit["sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise AssertionError("candidate revision is not immutable")
    text, tree_record = fetch(base + "/git/trees/" + revision + "?recursive=1")
    tree = json.loads(text)
    if tree.get("truncated") is not False:
        raise AssertionError("candidate tree incomplete")
    report = {"repository": repository, "revision": revision,
              "acceptance_evidence": False, "commit": commit_record, "tree": tree_record,
              "files": [item for item in tree["tree"] if item["type"] == "blob" and
                        not any(part.startswith(".") or part in ("VULCAN",)
                                for part in Path(item["path"]).parts)],
              "documents": []}
    write_json(run.path / "candidate-inspection.json", report)
    if q4_issues:
        text, record = fetch("https://api.github.com/search/issues?" + urlencode(
            {"q": "repo:" + repository + " is:issue Q4", "per_page": 100, "page": 1}))
        payload = json.loads(text)
        entries = issue_search_entries(payload, repository)
        report["q4_issue_search"] = {
            "response": record, "entries": entries,
            "total_count": payload["total_count"],
            "incomplete_results": payload["incomplete_results"],
            "possibly_truncated": payload["total_count"] > len(entries),
            "scope": "first page of public issue discussions at retrieval; "
                     "not immutable assets, executable adapters or proof of global absence"}
        write_json(run.path / "candidate-inspection.json", report)
    if q4_commits:
        text, record = fetch("https://api.github.com/search/commits?" + urlencode(
            {"q": "repo:" + repository + " Q4", "per_page": 100, "page": 1}))
        payload = json.loads(text)
        entries = commit_search_entries(payload, repository)
        report["q4_commit_message_search"] = {
            "response": record, "entries": entries,
            "total_count": payload["total_count"],
            "incomplete_results": payload["incomplete_results"],
            "possibly_truncated": payload["total_count"] > len(entries),
            "scope": "first page of indexed public commit-message matches at retrieval; "
                     "not confined to the selected tree or proof of baseline content/absence"}
        write_json(run.path / "candidate-inspection.json", report)
    if pull_requests:
        text, record = fetch(base + "/pulls?state=all&sort=updated&direction=desc&per_page=100&page=1")
        entries = pull_request_entries(json.loads(text))
        report["public_pull_requests"] = {
            "response": record, "entries": entries,
            "possibly_truncated": len(entries) == 100,
            "scope": "first page of public PRs sorted by update time at retrieval; "
                     "not private/deleted PRs, baseline validation or proof of absence"}
        write_json(run.path / "candidate-inspection.json", report)
    if q4_history:
        text, record = fetch(base + "/commits?" + urlencode(
            {"sha": revision, "path": "anvil-q4/", "per_page": 100, "page": 1}))
        payload = json.loads(text)
        entries = q4_history_entries(payload)
        report["q4_path_history"] = {
            "response": record, "entries": entries,
            "possibly_truncated": len(entries) == 100,
            "scope": "first page for anvil-q4/ reachable from " + revision +
                     "; excludes other paths, unreachable history and other repositories; "
                     "neither baseline validation nor proof of global absence"}
        write_json(run.path / "candidate-inspection.json", report)
    if forks:
        text, record = fetch(base + "/forks?per_page=100&page=1&sort=newest")
        payload = json.loads(text)
        entries = fork_entries(payload)
        report["public_forks"] = {
            "response": record, "entries": entries,
            "possibly_truncated": len(entries) == 100,
            "scope": "first page of public forks at retrieval time; "
                     "not private/deleted forks or proof of global baseline absence"}
        write_json(run.path / "candidate-inspection.json", report)
    if references:
        report["public_references"] = {}
        for kind in ("branches", "tags", "releases"):
            text, record = fetch(base + "/" + kind + "?per_page=100&page=1")
            payload = json.loads(text)
            report["public_references"][kind] = {
                "response": record, "entries": reference_entries(kind, payload),
                "possibly_truncated": len(payload) == 100,
                "scope": "first page of public references at retrieval time; "
                         "not private/deleted refs or historical execution evidence"}
            write_json(run.path / "candidate-inspection.json", report)
    for name in ("README.md", "LICENSE", "VERSION.json"):
        indexed = [item for item in report["files"] if item["path"] == name]
        if len(indexed) > 1:
            raise AssertionError("ambiguous candidate document in immutable source index")
        if indexed:
            _, record = fetch("https://raw.githubusercontent.com/" + repository +
                              "/" + revision + "/" + name)
            verify_indexed_blob(indexed[0], (ROOT / record["retained_path"]).read_bytes())
            report["documents"].append({"path": name, "git_blob_sha1": indexed[0]["sha"],
                                        "immutable_index_verified": True, **record})
            write_json(run.path / "candidate-inspection.json", report)
    if acquire_native:
        selected = [item for item in report["files"]
                    if any(item["path"].startswith(generation + "/rtl/")
                           for generation in ("anvil-q1", "anvil-q2")) and
                    item["path"].endswith((".sv", ".v"))]
        if not selected or len(selected) > 128:
            raise AssertionError("candidate native source count is empty or outside bounded intake")
        report["native_sources"] = []
        for item in selected:
            _, record = fetch("https://raw.githubusercontent.com/" + repository +
                              "/" + revision + "/" + item["path"])
            content = (ROOT / record["retained_path"]).read_bytes()
            verify_indexed_blob(item, content)
            report["native_sources"].append({"path": item["path"], **record})
            write_json(run.path / "candidate-inspection.json", report)
        q2 = [record for record in report["native_sources"]
              if record["path"].startswith("anvil-q2/rtl/")]
        report["supplied_q2_comparisons"] = [
            {"public_path": record["path"],
             "supplied_path": "anvil_q2_reference/rtl/" + Path(record["path"]).name,
             "public_sha256": record["sha256"],
             "supplied_sha256": run.hashes.get(
                 "anvil_q2_reference/rtl/" + Path(record["path"]).name),
             "byte_identical": (
                 ROOT / "anvil_q2_reference/rtl" / Path(record["path"]).name
             ).is_file() and (
                 ROOT / "anvil_q2_reference/rtl" / Path(record["path"]).name
             ).read_bytes() == (ROOT / record["retained_path"]).read_bytes()}
            for record in q2
        ]
        report["q4_indexed_files"] = [
            item["path"] for item in report["files"]
            if item["path"].startswith("anvil-q4/")
        ]
        report["q4_absence_scope"] = "this immutable candidate tree only; not global absence"
        write_json(run.path / "candidate-inspection.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", help="inspect one public search candidate at an immutable revision")
    parser.add_argument("--revision", help="pin candidate inspection to a previously identified commit")
    parser.add_argument("--acquire-native", action="store_true",
                        help="retain bounded Q1/Q2 RTL candidates; does not create an adapter")
    parser.add_argument("--references", action="store_true",
                        help="retain bounded public branch/tag/release identities, not just default HEAD")
    parser.add_argument("--forks", action="store_true",
                        help="retain bounded public fork candidates for independent source inspection")
    parser.add_argument("--q4-history", action="store_true",
                        help="retain Q4 path commit identities reachable from the pinned revision")
    parser.add_argument("--pull-requests", action="store_true",
                        help="retain bounded public PR head identities, including closed PRs")
    parser.add_argument("--q4-commits", action="store_true",
                        help="search bounded public Q4 commit messages without a path assumption")
    parser.add_argument("--q4-issues", action="store_true",
                        help="search bounded public Q4 discussions, not baseline source identities")
    parser.add_argument("--repair-of", help="link a prior advisory receipt without overwriting it")
    args = parser.parse_args()
    if (args.revision or args.acquire_native or args.references or args.forks or
            args.q4_history or args.pull_requests or args.q4_commits or
            args.q4_issues) and not args.repository:
        parser.error("candidate inspection options require --repository")
    run = Run("evidence/preparation/independent-baseline-discovery",
              "bounded public baseline discovery; not engineering acceptance",
              repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        report = (inspect_candidate(run, args.repository, args.revision, args.acquire_native,
                                    args.references, args.forks, args.q4_history, args.pull_requests,
                                    args.q4_commits, args.q4_issues)
                  if args.repository else discover(run))
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    errors = [row for row in report.get("searches", []) if "error" in row]
    run.finish("incomplete", result=report,
               diagnosis="Public baseline identity/content/adapter validation remains required; "
                         f"{len(errors)} search API errors")
    return 1


if __name__ == "__main__":
    sys.exit(main())

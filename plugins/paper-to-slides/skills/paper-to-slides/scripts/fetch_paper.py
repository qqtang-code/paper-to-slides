#!/usr/bin/env python3
"""Fetch a paper from an accessible link with provenance, validation, and safe extraction.

Accepts arXiv identifiers, arXiv URLs, or any direct http(s) file URL. Records the resolved
location, version, hashes, and content checks so a slide deck can cite what it actually read.
Archive members are validated before anything is written to disk, and nothing is executed.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

USER_AGENT = "paper-to-slides-fetch/1.0 (agent skill helper; scholarly use)"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={identifier}"
ARXIV_ID = re.compile(r"^(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})(v\d+)?$", re.I)
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MEMBERS = 5000
MAGIC = {"pdf": b"%PDF-", "gzip": b"\x1f\x8b", "zip": b"PK\x03\x04"}


def fail(parser, message):
    parser.exit(2, message.rstrip() + "\n")


def request(url, timeout):
    """Return (final_url, content_type, body) or raise ValueError with a readable reason."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # urllib follows redirects; re-check the status and final location.
            if response.status != 200:
                raise ValueError(f"HTTP {response.status} for {url}")
            body = response.read()
            return response.geturl(), response.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code} {exc.reason} for {url}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Cannot reach {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ValueError(f"Timed out after {timeout}s for {url}") from exc


def check_body(url, content_type, body, expect):
    """Reject error and login pages that a download tool would otherwise save as a paper."""
    if not body:
        raise ValueError(f"Empty response for {url}")
    warnings = []
    if content_type and expect not in content_type:
        warnings.append(f"Unexpected Content-Type {content_type!r} for {url}")
    if not body[:64].lower().startswith(MAGIC[expect].lower()):
        raise ValueError(f"Response for {url} is not a {expect} file "
                         f"(starts with {body[:16]!r}); a login or error page cannot be used")
    return warnings


def arxiv_metadata(identifier, timeout):
    """Resolve an arXiv identifier to its concrete version, title, authors, and date."""
    url = ARXIV_API.format(identifier=urllib.parse.quote(identifier))
    _, _, body = request(url, timeout)
    text = body.decode("utf-8", errors="replace")
    entry = re.search(r"<entry>.*?</entry>", text, re.S)
    if not entry:
        raise ValueError(f"arXiv returned no entry for {identifier}; check the identifier")
    entry = entry.group(0)

    def field(tag):
        found = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", entry, re.S)
        return re.sub(r"\s+", " ", found.group(1)).strip() if found else ""

    resolved = field("id")
    if resolved.startswith("http://"):
        resolved = "https://" + resolved[len("http://"):]
    version = ""
    match = re.search(r"v(\d+)\s*$", resolved)
    if match:
        version = match.group(1)
    return {"resolved_url": resolved, "version": version, "title": field("title"),
            "authors": re.findall(r"<name>(.*?)</name>", entry, re.S),
            "updated": field("updated") or field("published")}


def parse_reference(reference):
    if re.match(r"^https?://", reference, re.I):
        url = reference
        arxiv = re.search(r"arxiv\.org/(?:abs|pdf|src)/([^/?#]+)", url, re.I)
        if arxiv:
            return {"kind": "arxiv", "identifier": arxiv.group(1).removesuffix(".pdf"), "supplied_url": url}
        if url.lower().endswith(".pdf"):
            return {"kind": "pdf", "identifier": url, "supplied_url": url}
        raise ValueError(f"Not a supported paper reference: {url}")
    if ARXIV_ID.match(reference):
        return {"kind": "arxiv", "identifier": reference, "supplied_url": f"https://arxiv.org/abs/{reference}"}
    raise ValueError(f"Not an arXiv identifier or file URL: {reference}")


def lexically_safe(name):
    """A member name must be relative and must not traverse upwards."""
    if not name or name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name):
        return False
    return not any(part == ".." for part in Path(name.replace("\\", "/")).parts)


def inside(root, name):
    """True when name resolves inside root, after resolving symlinks such as /tmp on macOS."""
    root = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root, name))
    return target == root or target.startswith(root + os.sep)


def archive_members(path, data):
    """Summarize an archive: every entry is classified, and unsafe ones are rejected."""
    summary = {"entries": 0, "files": 0, "directories": 0, "rejected": []}
    rejected, files, total = summary["rejected"], 0, 0
    if path.name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            summary["entries"] = len(infos)
            for info in infos:
                if info.is_dir():
                    summary["directories"] += 1
                    continue
                if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                    rejected.append(f"symlink: {info.filename}")
                    continue
                if not lexically_safe(info.filename):
                    rejected.append(f"unsafe path: {info.filename}")
                    continue
                files += 1
                total += info.file_size
                if total > MAX_TOTAL_BYTES or files > MAX_MEMBERS:
                    raise ValueError("Archive is too large to extract safely")
            summary["files"] = files
            summary["names"] = sorted(i.filename for i in infos if not i.is_dir())
            return summary
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        summary["entries"] = len(members)
        for member in members:
            if member.isdir():
                summary["directories"] += 1
                continue
            if not member.isfile():
                rejected.append(f"{'link' if member.issym() or member.islnk() else 'special'}: {member.name}")
                continue
            if not lexically_safe(member.name):
                rejected.append(f"unsafe path: {member.name}")
                continue
            files += 1
            total += member.size
            if total > MAX_TOTAL_BYTES or files > MAX_MEMBERS:
                raise ValueError("Archive is too large to extract safely")
        summary["files"] = files
        summary["names"] = sorted(m.name for m in members if m.isfile())
        return summary


def extract_archive(data, destination, expect):
    """Write only validated regular files; every member is checked again before writing."""
    destination.mkdir(parents=True, exist_ok=True)
    root = os.path.realpath(destination)
    written = 0
    if expect == "zip":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir() or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                    continue
                if not (lexically_safe(info.filename) and inside(root, info.filename)):
                    continue
                target = Path(root) / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
                written += 1
    else:
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                if not member.isfile() or not (lexically_safe(member.name) and inside(root, member.name)):
                    continue
                target = Path(root) / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                target.write_bytes(handle.read())
                written += 1
    return written


def download(url, timeout, expect):
    final_url, content_type, body = request(url, timeout)
    warnings = check_body(url, content_type, body, expect)
    return {"url": url, "final_url": final_url, "content_type": content_type or "unknown",
            "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
            "magic": expect, "warnings": warnings}, body


def record_error(artifacts, url, exc):
    artifacts.append({"url": url, "error": str(exc)})
    print(f"Warning: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", help="arXiv id, arXiv URL, or direct http(s) file URL")
    parser.add_argument("--dir", type=Path, default=Path("paper-source"),
                        help="Output directory; default: ./paper-source")
    parser.add_argument("--what", choices=("both", "pdf", "source"), default="both",
                        help="Which artifact to fetch; default: both, falling back to the PDF")
    parser.add_argument("--extract", action="store_true",
                        help="Extract a validated source archive into <dir>/source/")
    parser.add_argument("--timeout", type=int, default=60, help="Per-request seconds; default: 60")
    parser.add_argument("--force", action="store_true", help="Replace existing downloaded files")
    parser.add_argument("--json", type=Path,
                        help="Write the provenance record here instead of <dir>/provenance.json")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        parsed = parse_reference(args.reference)
    except ValueError as exc:
        fail(parser, str(exc))

    provenance = {"supplied_reference": args.reference, "kind": parsed["kind"],
                  "retrieved": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                  "artifacts": [], "warnings": []}
    args.dir.mkdir(parents=True, exist_ok=True)

    if parsed["kind"] == "pdf":
        urls = {"pdf": parsed["identifier"]}
        provenance["supplied_url"] = parsed["supplied_url"]
    else:
        identifier = parsed["identifier"]
        try:
            # A versioned reference stays pinned; an unversioned one resolves to the latest.
            metadata = arxiv_metadata(identifier, args.timeout)
        except ValueError as exc:
            provenance["warnings"].append(f"Metadata lookup failed: {exc}")
            print(f"Warning: continuing without resolved metadata ({exc})", file=sys.stderr)
            metadata = {"resolved_url": f"https://arxiv.org/abs/{identifier}", "version": "", "title": "",
                        "authors": [], "updated": ""}
        provenance.update({"supplied_url": parsed["supplied_url"], "resolved_url": metadata["resolved_url"],
                           "version": metadata["version"], "title": metadata["title"],
                           "authors": metadata["authors"], "paper_updated": metadata["updated"]})
        base = metadata["resolved_url"].rsplit("/abs/", 1)[-1] if "/abs/" in metadata["resolved_url"] else identifier
        urls = {"pdf": f"https://arxiv.org/pdf/{base}", "source": f"https://arxiv.org/src/{base}"}
        provenance["identifier"] = base

    wanted = ["pdf", "source"] if args.what == "both" else [args.what]
    for kind in wanted:
        url = urls.get(kind)
        if not url:
            continue
        expect = "pdf" if kind == "pdf" else "gzip"
        try:
            artifact, body = download(url, args.timeout, expect)
        except ValueError as exc:
            record_error(provenance["artifacts"], url, exc)
            continue
        if kind == "source" and body.lstrip()[:4] == MAGIC["zip"]:
            # Some papers publish a zip source archive rather than a tarball.
            artifact["magic"] = expect = "zip"
        if kind == "pdf":
            filename = args.dir / "paper.pdf"
        else:
            filename = args.dir / ("source.zip" if expect == "zip" else "source.tar.gz")
        if filename.exists() and not args.force:
            fail(parser, f"Output exists: {filename}; use --force to replace it")
        filename.write_bytes(body)
        artifact.update({"kind": kind, "path": str(filename)})
        provenance["artifacts"].append(artifact)
        provenance["warnings"].extend(artifact.pop("warnings", []))
        print(f"{kind}: {artifact['bytes']} bytes, sha256 {artifact['sha256']} -> {filename}")

        if kind == "source":
            try:
                # Inspect before extracting, and only ever write validated regular files.
                summary = archive_members(filename, body)
                provenance["source_archive"] = summary
                print(f"source archive: {summary['entries']} entries "
                      f"({summary['files']} file(s), {summary['directories']} director(ies)), "
                      f"{len(summary['rejected'])} rejected")
                if args.extract:
                    written = extract_archive(body, args.dir / "source", artifact["magic"])
                    provenance["source_archive"]["extracted_to"] = str(args.dir / "source")
                    provenance["source_archive"]["extracted_files"] = written
                    print(f"extracted {written} file(s) to {args.dir / 'source'}")
            except (tarfile.TarError, zipfile.BadZipFile, OSError) as exc:
                provenance["warnings"].append(f"Cannot read source archive: {exc}")
                print(f"Warning: cannot read source archive ({exc})", file=sys.stderr)

    if not any("path" in artifact for artifact in provenance["artifacts"]):
        provenance["usable"] = False
        write_record(provenance, args)
        fail(parser, "Nothing was downloaded; an inaccessible link establishes only that retrieval failed")

    provenance["usable"] = True
    write_record(provenance, args)
    return 0


def write_record(provenance, args):
    path = args.json or (args.dir / "provenance.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"provenance: {path}")


if __name__ == "__main__":
    sys.exit(main())
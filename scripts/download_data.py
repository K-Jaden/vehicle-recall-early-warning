"""Download raw datasets listed in configs/data_sources.yaml into data/raw/.

Usage:
    python scripts/download_data.py --dry-run
    python scripts/download_data.py --only complaints recalls
    python scripts/download_data.py --force

Each download is recorded in data/manifest.json (URL, size, SHA-256, timestamp).
"""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "data_sources.yaml"
RAW_DIR = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "vehicle-recall-early-warning/0.1"})
    with urllib.request.urlopen(req) as resp, tmp.open("wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 20):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:,.0f} / {total / 1e6:,.0f} MB", end="", flush=True)
    print()
    tmp.replace(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", help="source names to download (default: all)")
    parser.add_argument("--force", action="store_true", help="re-download even if the file exists")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without downloading")
    args = parser.parse_args()

    sources = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["sources"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for name, src in sources.items():
        if args.only and name not in args.only:
            continue
        if not src.get("url"):
            print(f"[skip] {name}: url is not set in {CONFIG.name} (TODO)")
            continue
        dest = RAW_DIR / src["filename"]
        if dest.exists() and not args.force:
            print(f"[skip] {name}: {dest.name} already exists (use --force to re-download)")
            continue
        if args.dry_run:
            print(f"[dry-run] {name}: {src['url']} -> {dest.relative_to(ROOT)}")
            continue

        print(f"[download] {name}: {src['url']}")
        download(src["url"], dest)
        manifest[name] = {
            "url": src["url"],
            "filename": src["filename"],
            "size_bytes": dest.stat().st_size,
            "sha256": sha256_of(dest),
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

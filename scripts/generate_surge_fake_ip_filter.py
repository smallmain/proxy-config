#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/vernesong/OpenClash/refs/heads/master/"
    "luci-app-openclash/root/etc/openclash/custom/openclash_custom_fake_filter.list"
)
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "surge" / "fake-ip-filter.sgmodule"
)
USER_AGENT = "proxy-config-fake-ip-filter-generator/1.0"
VALID_ENTRY_PATTERN = re.compile(r"^[A-Za-z0-9+*._-]+$")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def is_supported_entry(entry: str) -> bool:
    return bool(VALID_ENTRY_PATTERN.fullmatch(entry))


def expand_entry(entry: str) -> list[str]:
    if entry.startswith("+."):
        base = entry[2:]
        return [base, f"*.{base}"]
    return [entry]


def parse_entries(raw_text: str) -> tuple[list[str], list[str]]:
    entries: list[str] = []
    seen_entries: set[str] = set()
    skipped_entries: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        normalized_entries = expand_entry(line)
        if all(is_supported_entry(item) for item in normalized_entries):
            for item in normalized_entries:
                if item in seen_entries:
                    continue
                seen_entries.add(item)
                entries.append(item)
            continue

        skipped_entries.append(line)

    if not entries:
        raise RuntimeError("No fake-ip filter entries were found in the source list.")

    return entries, skipped_entries


def render_module(entries: list[str]) -> str:
    module_lines = [
        "#!name=Fake IP Filter",
        "#!desc=Generated fake-ip filter list for Surge.",
        "#!category=Network",
        f"# Entry count: {len(entries)}",
        "",
        "[General]",
        f"always-real-ip = %APPEND% {', '.join(entries)}",
        "",
    ]
    return "\n".join(module_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Surge fake-ip filter module from a source list."
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    raw_text = fetch_text(args.source_url)
    entries, skipped_entries = parse_entries(raw_text)
    module_text = render_module(entries)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(module_text, encoding="utf-8")

    print(f"Wrote {len(entries)} entries to {output_path}")
    if skipped_entries:
        print(
            "Skipped unsupported entries: "
            + ", ".join(skipped_entries)
        )


if __name__ == "__main__":
    main()

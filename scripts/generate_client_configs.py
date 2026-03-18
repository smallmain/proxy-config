#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = PROJECT_ROOT / "config" / "base"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "config"
DEFAULT_RULE_BASE_URL = "https://testingcf.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule"
DEFAULT_CLASH_RULE_BASE_URL = (
    "https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/clash"
)
PLACEHOLDER_PATTERN = re.compile(r"\$([^$]+)\$")
NO_RESOLVE_SUFFIX = "_No_Resolve"
RESOLVE_SUFFIX = "_Resolve"
RESOLVE_SENSITIVE_RULE_PREFIXES = (
    "GEOIP,",
    "IP-ASN,",
    "IP-CIDR,",
    "IP-CIDR6,",
    "IP-SUFFIX,",
    "SRC-IP-ASN,",
    "SRC-IP-CIDR,",
    "SRC-IP-CIDR6,",
)


@dataclass(frozen=True)
class ClientSpec:
    name: str
    source_dir: str
    source_extension: str
    url_base: str
    generate_local_lists: bool = False


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative_path: Path
    normalized_key: str
    suffix_kind: str
    content_kind: str


@dataclass(frozen=True)
class SourceMatch:
    source: SourceFile
    extra_prefix_segments: int


CLIENT_SPECS = (
    ClientSpec(
        name="surge",
        source_dir="Surge",
        source_extension=".list",
        url_base=f"{DEFAULT_RULE_BASE_URL}/Surge",
    ),
    ClientSpec(
        name="shadowrocket",
        source_dir="Shadowrocket",
        source_extension=".list",
        url_base=f"{DEFAULT_RULE_BASE_URL}/Shadowrocket",
    ),
    ClientSpec(
        name="clash",
        source_dir="Clash",
        source_extension=".yaml",
        url_base=DEFAULT_CLASH_RULE_BASE_URL,
        generate_local_lists=True,
    ),
)


def strip_variant_suffix(stem: str) -> tuple[str, str]:
    if stem.endswith(NO_RESOLVE_SUFFIX):
        return stem[: -len(NO_RESOLVE_SUFFIX)], "noresolve"
    if stem.endswith(RESOLVE_SUFFIX):
        return stem[: -len(RESOLVE_SUFFIX)], "resolve"
    return stem, "base"


def normalize_rule_line(raw_line: str) -> str:
    stripped = raw_line.strip()
    if stripped.startswith("- "):
        return stripped[2:].strip()
    return stripped


def classify_content(text: str) -> str:
    has_no_resolve = False
    has_sensitive_rules = False

    for raw_line in text.splitlines():
        line = normalize_rule_line(raw_line)
        if not line or line.startswith("#") or line == "payload:":
            continue

        if line.endswith(",no-resolve"):
            has_no_resolve = True

        if line.startswith(RESOLVE_SENSITIVE_RULE_PREFIXES):
            has_sensitive_rules = True

    if has_no_resolve:
        return "noresolve"
    if has_sensitive_rules:
        return "resolve"
    return "neutral"


def build_source_index(root: Path, extension: str) -> dict[str, list[SourceMatch]]:
    suffix_map: dict[str, list[SourceMatch]] = {}

    for path in sorted(root.rglob(f"*{extension}")):
        relative_path = path.relative_to(root)
        normalized_stem, suffix_kind = strip_variant_suffix(path.stem)
        normalized_path = relative_path.with_name(normalized_stem).with_suffix("")
        normalized_key = normalized_path.as_posix()
        content_kind = classify_content(path.read_text(encoding="utf-8"))
        source = SourceFile(
            path=path,
            relative_path=relative_path,
            normalized_key=normalized_key,
            suffix_kind=suffix_kind,
            content_kind=content_kind,
        )

        parts = normalized_path.parts
        for index in range(len(parts)):
            suffix_key = Path(*parts[index:]).as_posix()
            suffix_map.setdefault(suffix_key, []).append(
                SourceMatch(source=source, extra_prefix_segments=index)
            )

    return suffix_map


def score_match(match: SourceMatch, want_noresolve: bool) -> tuple[int, int, int, str]:
    source = match.source
    if want_noresolve:
        suffix_score = {
            "noresolve": 3,
            "base": 2,
            "resolve": 1,
        }[source.suffix_kind]
        content_score = {
            "noresolve": 3,
            "neutral": 2,
            "resolve": 1,
        }[source.content_kind]
    else:
        suffix_score = {
            "resolve": 3,
            "base": 2,
            "noresolve": 1,
        }[source.suffix_kind]
        content_score = {
            "resolve": 3,
            "neutral": 2,
            "noresolve": 1,
        }[source.content_kind]

    return (
        suffix_score,
        content_score,
        -match.extra_prefix_segments,
        -len(Path(source.normalized_key).parts),
        source.relative_path.as_posix(),
    )


def choose_source(
    token: str,
    source_index: dict[str, list[SourceMatch]],
    want_noresolve: bool,
) -> SourceFile:
    candidates = [part.strip() for part in token.split("|") if part.strip()]
    if not candidates:
        raise RuntimeError(f"Invalid placeholder: {token!r}")

    for candidate in candidates:
        matches = source_index.get(candidate, [])
        if not matches:
            continue
        best_match = max(matches, key=lambda item: score_match(item, want_noresolve))
        return best_match.source

    raise FileNotFoundError(f"Unable to resolve placeholder ${token}$")


def convert_clash_yaml_to_list(source_path: Path, source_hint: str) -> str:
    rules: list[str] = []
    in_payload = False

    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "payload:":
            in_payload = True
            continue
        if not in_payload:
            raise RuntimeError(f"Unexpected Clash YAML line before payload: {source_path}")
        if not stripped.startswith("- "):
            raise RuntimeError(f"Unsupported Clash YAML payload line: {source_path}")
        rules.append(stripped[2:].strip())

    if not rules:
        raise RuntimeError(f"No payload rules found in {source_path}")

    return "\n".join(
        [
            f"# Generated from {source_hint}",
            "# Do not edit manually.",
            *rules,
            "",
        ]
    )


class Generator:
    def __init__(
        self,
        base_dir: Path,
        output_root: Path,
        ios_rule_script_root: Path,
        clash_rule_base_url: str,
    ) -> None:
        self.base_dir = base_dir
        self.output_root = output_root
        self.ios_rule_script_root = ios_rule_script_root
        self.clash_rule_base_url = clash_rule_base_url.rstrip("/")
        self.source_indexes = {
            spec.name: build_source_index(
                self.ios_rule_script_root / "rule" / spec.source_dir,
                spec.source_extension,
            )
            for spec in CLIENT_SPECS
        }
        self.generated_clash_lists: dict[str, Path] = {}

    def ensure_clash_list(self, source: SourceFile) -> str:
        output_name = f"{source.path.stem}.list"
        output_path = self.output_root / "clash" / output_name
        existing_source = self.generated_clash_lists.get(output_name)
        if existing_source is not None and existing_source != source.path:
            raise RuntimeError(
                "Clash output name collision: "
                f"{output_name} maps to both {existing_source} and {source.path}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        source_hint = f"rule/Clash/{source.relative_path.as_posix()}"
        output_path.write_text(
            convert_clash_yaml_to_list(source.path, source_hint),
            encoding="utf-8",
        )
        self.generated_clash_lists[output_name] = source.path
        return f"{self.clash_rule_base_url}/{output_name}"

    def replace_placeholders(self, text: str, spec: ClientSpec, want_noresolve: bool) -> str:
        source_index = self.source_indexes[spec.name]

        def replace(match: re.Match[str]) -> str:
            token = match.group(1)
            token_want_noresolve = want_noresolve
            if token.startswith("!"):
                token_want_noresolve = True
                token = token[1:].lstrip()
            source = choose_source(token, source_index, token_want_noresolve)
            if spec.generate_local_lists:
                return self.ensure_clash_list(source)
            return f"{spec.url_base}/{source.relative_path.as_posix()}"

        return PLACEHOLDER_PATTERN.sub(replace, text)

    def generate(self) -> None:
        base_files = sorted(self.base_dir.glob("*.ini"))
        if not base_files:
            raise RuntimeError(f"No base ini files found in {self.base_dir}")

        for base_file in base_files:
            want_noresolve = "noresolve" in base_file.stem.lower()
            base_text = base_file.read_text(encoding="utf-8")

            for spec in CLIENT_SPECS:
                output_dir = self.output_root / spec.name
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / base_file.name
                rendered = self.replace_placeholders(base_text, spec, want_noresolve)
                output_path.write_text(rendered, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate client INI files from config/base placeholders."
    )
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument(
        "--ios-rule-script-root",
        required=True,
        help="Path to the local blackmatrix7/ios_rule_script repository.",
    )
    parser.add_argument(
        "--clash-rule-base-url",
        default=DEFAULT_CLASH_RULE_BASE_URL,
        help="Base URL used by generated Clash INI files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = Generator(
        base_dir=Path(args.base_dir),
        output_root=Path(args.output_root),
        ios_rule_script_root=Path(args.ios_rule_script_root),
        clash_rule_base_url=args.clash_rule_base_url,
    )
    generator.generate()
    print(
        "Generated client configs in "
        f"{generator.output_root} and {len(generator.generated_clash_lists)} Clash rule files."
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_CONF = PROJECT_ROOT / "shadowrocket" / "base.conf"
DEFAULT_RULE_CONFIG_DIR = PROJECT_ROOT / "config" / "shadowrocket"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "shadowrocket"
SUBSCRIPTION_NAME = "SUBLINK.SMALLMAIN.COM"
COMMENT_PREFIXES = ("#", ";")
INLINE_RULE_FLAGS = {"no-resolve"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate final Shadowrocket .conf files by combining shadowrocket/base.conf "
            "with config/shadowrocket/*.ini rule templates."
        )
    )
    parser.add_argument("--base-conf", default=str(DEFAULT_BASE_CONF))
    parser.add_argument("--rule-config-dir", default=str(DEFAULT_RULE_CONFIG_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def normalize_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines()]


def parse_policy_token(token: str) -> str:
    if not token.startswith("[]"):
        raise ValueError(f"Unsupported policy token: {token}")
    return token[2:]


def parse_proxy_group(value: str) -> str:
    tokens = value.split("`")
    if len(tokens) < 2:
        raise ValueError(f"Invalid custom_proxy_group entry: {value}")

    name = tokens[0].strip()
    group_type = tokens[1].strip()
    if not name or not group_type:
        raise ValueError(f"Invalid custom_proxy_group entry: {value}")

    if group_type == "select":
        return render_select_group(name, tokens[2:])

    if group_type in {"url-test", "fallback", "load-balance", "random"}:
        return render_test_group(name, group_type, tokens[2:])

    raise ValueError(f"Unsupported proxy group type: {group_type}")


def render_select_group(name: str, tail_tokens: list[str]) -> str:
    policies: list[str] = []
    regex_filter = ""

    for token in tail_tokens:
        stripped = token.strip()
        if not stripped:
            continue
        if stripped.startswith("[]"):
            policies.append(parse_policy_token(stripped))
            continue
        if not regex_filter:
            regex_filter = stripped
            continue
        raise ValueError(f"Unsupported select group token: {stripped}")

    parts = [f"{name} = select"]
    if regex_filter:
        parts.append(f",{SUBSCRIPTION_NAME}")
    if policies:
        parts.append("," + ",".join(policies))
    if regex_filter:
        parts.append(f",use=true,policy-regex-filter={regex_filter}")
    return "".join(parts)


def render_test_group(name: str, group_type: str, tail_tokens: list[str]) -> str:
    if len(tail_tokens) < 3:
        raise ValueError(
            f"{group_type} group requires regex filter, test url, and timing info: {name}"
        )

    regex_filter = tail_tokens[0].strip()
    test_url = tail_tokens[1].strip()
    timing_tokens = [part.strip() for part in tail_tokens[2].split(",")]
    if len(timing_tokens) != 3:
        raise ValueError(
            f"{group_type} group timing must contain interval, timeout, tolerance: {name}"
        )

    interval, timeout, tolerance = timing_tokens
    params = [SUBSCRIPTION_NAME, "use=true", f"policy-regex-filter={regex_filter}"]
    if interval:
        params.append(f"interval={interval}")
    if timeout:
        params.append(f"timeout={timeout}")
    if tolerance:
        params.append(f"tolerance={tolerance}")
    params.append(f"url={test_url}")

    return f"{name} = {group_type}," + ",".join(params)


def parse_ruleset(value: str) -> str:
    policy, target = value.split(",", 1)
    policy = policy.strip()
    target = target.strip()

    if target.startswith("[]"):
        return render_inline_rule(policy, target[2:])

    return f"RULE-SET,{target},{policy}"


def render_inline_rule(policy: str, value: str) -> str:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise ValueError(f"Invalid inline ruleset: {value}")

    trailing_flags: list[str] = []
    while len(parts) > 1 and parts[-1] in INLINE_RULE_FLAGS:
        trailing_flags.insert(0, parts.pop())

    rendered = [*parts, policy, *trailing_flags]
    return ",".join(rendered)


def parse_rule_template(path: Path) -> tuple[list[str], list[str]]:
    proxy_groups: list[str] = []
    rules: list[str] = []
    current_section = ""

    for raw_line in normalize_lines(path.read_text(encoding="utf-8")):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped.lower()
            continue

        if current_section != "[custom]":
            continue

        if stripped.startswith("custom_proxy_group="):
            proxy_groups.append(parse_proxy_group(stripped.split("=", 1)[1]))
            continue

        if stripped.startswith("ruleset="):
            rules.append(parse_ruleset(stripped.split("=", 1)[1]))
            continue

        if stripped.startswith("enable_rule_generator="):
            continue

        if stripped.startswith("overwrite_original_rules="):
            continue

        raise ValueError(f"Unsupported line in {path}: {raw_line}")

    if not proxy_groups:
        raise ValueError(f"No proxy groups found in {path}")
    if not rules:
        raise ValueError(f"No rules found in {path}")

    return proxy_groups, rules


def render_final_config(base_text: str, proxy_groups: list[str], rules: list[str], source: Path) -> str:
    stripped_base = base_text.rstrip()
    if "[Proxy Group]" in stripped_base or "[Rule]" in stripped_base:
        raise ValueError("Base config already contains [Proxy Group] or [Rule] sections.")

    parts = [
        stripped_base,
        "",
        f"# Generated from {source.relative_to(PROJECT_ROOT)}",
        "[Proxy Group]",
        *proxy_groups,
        "",
        "[Rule]",
        *rules,
        "",
    ]
    return "\n".join(parts)


def generate(base_conf: Path, rule_config_dir: Path, output_dir: Path) -> list[Path]:
    if not base_conf.is_file():
        raise FileNotFoundError(f"Base config not found: {base_conf}")
    if not rule_config_dir.is_dir():
        raise FileNotFoundError(f"Rule config directory not found: {rule_config_dir}")

    base_text = base_conf.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_paths: list[Path] = []
    for ini_path in sorted(rule_config_dir.glob("*.ini")):
        proxy_groups, rules = parse_rule_template(ini_path)
        output_path = output_dir / f"{ini_path.stem}.conf"
        rendered = render_final_config(base_text, proxy_groups, rules, ini_path)
        output_path.write_text(rendered, encoding="utf-8")
        generated_paths.append(output_path)

    if not generated_paths:
        raise RuntimeError(f"No .ini files found in {rule_config_dir}")

    return generated_paths


def main() -> None:
    args = parse_args()
    generated_paths = generate(
        base_conf=Path(args.base_conf),
        rule_config_dir=Path(args.rule_config_dir),
        output_dir=Path(args.output_dir),
    )
    print("Generated Shadowrocket configs:")
    for path in generated_paths:
        print(path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import re
import fileinput
import subprocess
import json
import os

from typing import Set, Iterable


def get_nix_packages() -> Set[str]:
    res = subprocess.run(
        [
            "nix",
            "--experimental-features",
            "nix-command",
            "eval",
            "--json",
            "-f",
            "<nixpkgs>",
            "texlive",
            "--apply",
            "builtins.attrNames",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return set(json.loads(res.stdout))


def get_packages(line: str) -> Set[str]:
    match = re.match(r"\\(?:usepackage|RequirePackage).*{([^}]+)}", line)
    if not match:
        return set()
    args = match.group(1)
    packages = set()
    for arg in args.split(","):
        packages.add(arg.strip())
    return packages


def _collect_deps(
    working_set: Set[str], done: Set[str], all_packages: Set[str]
) -> None:
    package = working_set.pop()
    done.add(package)
    cmd = ["nix-build", "--no-out-link", "<nixpkgs>", "-A", f"texlive.{package}.pkgs"]
    paths = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE)
    for dir in paths.stdout.split("\n"):
        path = os.path.join(dir, "tex")
        for root, _, files in os.walk(path):
            for fname in files:
                path = os.path.join(root, fname)
                with open(path, "rb") as f:
                    for line in f:
                        packages = get_packages(line.decode("utf-8", errors="ignore"))
                        working_set |= all_packages & (packages - done)


def collect_deps(packages: Set[str], all_packages: Set[str]) -> Set[str]:
    working_set: Set[str] = set(packages)
    done: Set[str] = set()
    while working_set:
        _collect_deps(working_set, done, all_packages)

    return done


def write_tex_env(dir: str, packages: Set[str]) -> str:
    name = os.path.join(dir, "tex-env.nix")
    with open(name, "w") as f:
        f.write(
            """# Generated with tex2nix 0.0.0
{ texlive, extraTexPackages ? {} }:
(texlive.combine ({
    inherit (texlive) scheme-small;
"""
        )
        for package in sorted(packages):
            f.write(f'    "{package}" = texlive."{package}";\n')
        f.write(
            """
} // extraTexPackages))
"""
        )
    print("wrote tex-env.nix...")
    return name


def extract_dependencies(lines: Iterable[str]) -> Set[str]:
    packages = set()
    for line in lines:
        packages |= get_packages(line)

    all_packages = get_nix_packages()
    nix_packages = packages & all_packages
    return collect_deps(nix_packages, all_packages)


def main() -> None:
    packages = extract_dependencies(fileinput.input())
    write_tex_env(os.getcwd(), packages)


if __name__ == "__main__":
    main()

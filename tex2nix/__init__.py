#!/usr/bin/env python3

import re
import fileinput
import subprocess
import json
import os
from pathlib import Path

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


with open("/home/shortcut/git/tex2nix/base.tex") as myTex:
    for line in myTex:
        get_packages(line)


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


# REVIEW: No errors, but the types don't seem right
def extract_tex_dependencies(lines: Iterable[str], inputSrc: Path) -> Set[Path]:
    tex_dependencies = set()
    for line in lines:
        match = re.match(r"\\input.*{([^}]+)}", line)
        if match:
            args = match.group(1)
            for arg in args.split(","):
                # REVIEW: Add check for circular depencencies?
                # Assumes inputs are of the form: \input{FILENAME}, corresponding to {inputSrc}/FILENAME.tex
                argPath = inputSrc / f"{arg}.tex"
                tex_dependencies.add(argPath)
                tex_dependencies |= extract_tex_dependencies(open(argPath), inputSrc)
    return tex_dependencies


def extract_dependencies(lines: Iterable[str], inputSrc: Path) -> Set[str]:
    # Building set of all \input .tex files
    packages = set()
    linesPersist = [x for x in map(str, lines)]
    tex_dependencies = extract_tex_dependencies(list(linesPersist), inputSrc)
    for dependency in tex_dependencies:
        for x in open(dependency):
            packages |= get_packages(x)
    for y in list(linesPersist):
        packages |= get_packages(y)

    all_packages = get_nix_packages()
    nix_packages = packages & all_packages
    return collect_deps(nix_packages, all_packages)


def main() -> None:
    with fileinput.input() as f:
        # REVIEW: Does this pop the first line of f?
        f.readline()
        inputSrc = Path(f.filename()).parent.absolute()
        packages = extract_dependencies(f, inputSrc)
    write_tex_env(os.getcwd(), packages)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import tempfile
import subprocess

from tex2nix import extract_dependencies, write_tex_env


def test_document() -> None:
    deps = extract_dependencies(
        """
\\documentclass[12pt,twoside,a4paper]{article}
\\usepackage{tabu}
\\begin{document}
\\end{document}
    """.split(
            "\n"
        )
    )
    assert deps == set(["varwidth", "tabu"])


def test_expression() -> None:
    with tempfile.TemporaryDirectory() as dir:
        env = write_tex_env(dir, set(["varwidth", "tabu"]))
        expr = f"with import <nixpkgs> {{}}; pkgs.callPackage {env} {{}}"
        subprocess.run(["nix-build", "--no-out-link", "-E", expr], check=True)

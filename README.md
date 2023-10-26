# tex2nix

Generate Texlive environment containing all dependencies for your document
rather than downloading gigabytes of texlive packages.


## Installation

With stable nix you can do:

``` console
nix-build && ./result/bin/tex2nix
```

If you use flakes put the following in your inputs

```nix
{
  inputs.tex2nix.url = "github:rgri/tex2nix";
  inputs.tex2nix.inputs.utils.follows = "nixpkgs";
}
```

or just do:

```console
$ nix run github:rgri/tex2nix
```


## USAGE

```console
$ tex2nix main.tex
wrote tex-env.nix
$ cat tex-env.nix
# Generated with tex2nix 0.0.0
{ texlive }:
(texlive.combine {
    inherit (texlive) scheme-small;
    "varwidth" = texlive."varwidth";
    "tabu" = texlive."tabu";

})
```

tex2nix does not follow `\input` or `\include`. However you can specify multiple
texfiles as input

```console
$ tex2nix *.tex
```

The resulting expression can be imported like this to in your document directory:

```nix
# shell.nix
with import <nixpkgs> {};
mkShell {
  buildInputs = [ (pkgs.callPackage ./tex-env.nix {}) ];
}
```

``` console
$ nix-shell shell.nix
nix-shell> pdflatex --version
pdfTeX 3.14159265-2.6-1.40.21 (TeX Live 2020/NixOS.org)
...
```

To add additional packages you can use the extraTexPackages field:

```nix
with import <nixpkgs> {};
mkShell {
  buildInputs = [ (pkgs.callPackage ./tex-env.nix {
    extraTexPackages = {
      inherit (texlive) latexmk;
    };
  }) ];
}
```

# Project history

tex2nix was originally written by [Mic92](https://github.com/Mic92). Since 2023, [rgri](https://github.com/rgri) is the new maintainer.

#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 nixfmt

import argparse
import re
import os
from typing import Callable


FILES_TO_IGNORE = [
    # similar attr names not in meta
    "pkgs/tools/text/uniscribe/gemset.nix",
    "pkgs/top-level/release-lib.nix",
    "pkgs/top-level/release-cross.nix",
    "pkgs/top-level/perl-packages.nix",
    "pkgs/tools/package-management/nix/modular/packaging/everything.nix",
    "pkgs/tools/typesetting/tex/texlive/default.nix",

    # platforms = if ...
    "pkgs/by-name/lo/losslesscut-bin/build-from-dmg.nix",
    "pkgs/by-name/ol/ollama/package.nix",
    "pkgs/by-name/qu/qutebrowser/package.nix",
    "pkgs/by-name/sp/speechd/package.nix",
    "pkgs/by-name/vi/vifm/package.nix",
    "pkgs/by-name/ze/zenith/package.nix",
    "pkgs/development/tools/documentation/doxygen/default.nix",
    "pkgs/games/nethack/default.nix",
    "pkgs/tools/system/nvtop/build-nvtop.nix",

    # some code in attrs
    "pkgs/development/python-modules/setuptools/default.nix",
];


# Find 'key ='; then:
# if it's 'key = [ val1 val2 ];', return 'key = [ lib.val1 lib.val2 ];'
# if it's 'key = val;', return 'key = lib.val;'
# if it's 'key = key.xxx ++ key.yyy;', return 'key = lib.key.xxx ++ lib.key.yyy;'.
#
# But: if there's already a 'lib.' prefix, don't add another one.
# But: if val is a "string", don't add 'lib.' prefix.
def list_or_value(key, lib_key=None):
    lib_key = lib_key or key

    def transform(content):
        # Ignore any file that doesn't have 'key(s).'; these meta attrs probably refer to other sets
        if f"{lib_key}." not in content and f"{lib_key}s." not in content:
            return content

        pattern = rf"({key}\s*=\s*)(\[[^\]]*\]|[^;]+)(;)"
        matches = re.finditer(pattern, content)

        for match in matches:
            full_match = match.group(0)
            prefix = match.group(1)
            value = match.group(2)
            suffix = match.group(3)

            if value.startswith("[") and value.endswith("]"):
                # It's a list
                items = re.findall(r"[^\s\[\]]+", value)
                new_items = []
                for item in items:
                    if item.startswith("lib.") or item.startswith('"') or item.startswith("'"):
                        new_items.append(item)
                    else:
                        new_items.append(f"lib.{item}")
                new_value = "[ " + " ".join(new_items) + " ]"
            elif "++" in value:
                # It's a concatenation of lists or values
                parts = re.split(r"(\s*\+\+\s*)", value)
                new_parts = []
                for part in parts:
                    part = part.strip()
                    if part == "++":
                        new_parts.append(part)
                    elif part.startswith("lib.") or part.startswith('"') or part.startswith("'") or not part.startswith(lib_key + "."):
                        new_parts.append(part)
                    else:
                        new_parts.append(f"lib.{part}")
                new_value = " ".join(new_parts)
            else:
                # It's a single value
                if value.startswith("lib.") or value.startswith('"') or value.startswith("'"):
                    new_value = value
                else:
                    new_value = f"lib.{value}"

            new_full_match = f"{prefix}{new_value}{suffix}"
            content = content.replace(full_match, new_full_match)

        return content

    return transform


RULES = [
    (r"meta = with lib; ", "meta = "),
    (r"maintainers = with maintainers; ", "maintainers = with lib.maintainers; "),
    (r"platforms = with platforms; ", "platforms = with lib.platforms; "),
    (r"license = with licenses; ", "license = with lib.licenses; "),
    (r"sourceProvenance = with sourceTypes; ", "sourceProvenance = with lib.sourceTypes; "),
    list_or_value("platforms"),
    list_or_value("badPlatforms", "platforms"),
    list_or_value("maintainers"),
    list_or_value("license"),
    list_or_value("teams"),
]


def transform_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    for rule in RULES:
        if isinstance(rule, Callable):
            content = rule(content)
        else:
            content = re.sub(rule[0], rule[1], content)

    with open(file_path, "w") as f:
        f.write(content)


def get_files(file_path):
    if os.path.isdir(file_path):
        file_list = []
        for root, _, files in os.walk(file_path):
            for file in files:
                if file.endswith(".nix"):
                    file_list.append(os.path.join(root, file))
        return file_list
    else:
        return [file_path]


# ./remove-with-lib.py <path-to-file-or-directory>
def main():
    parser = argparse.ArgumentParser(description="Clean up nixpkgs meta from with libs")
    parser.add_argument("file", help="Path to a file or directory")

    args = parser.parse_args()

    files = get_files(args.file)
    files = [f for f in files if f not in FILES_TO_IGNORE]

    nfiles = len(files)
    for i, file in enumerate(files):
        print(f"Processing file {i+1}/{nfiles}: {file}")
        #os.system("git checkout " + file)
        transform_file(file)

        # Sanity check: run nixfmt on the file and see that it doesn't fail; if it does, git checkout - we'll address it later
        ret = os.system("nixfmt " + file)
        if ret != 0:
            print(f"nix fmt failed on {file}, reverting changes")
            os.system("git checkout " + file)

    # Finally, reformat everything with nix fmt just in case
    os.system("nix fmt")

if __name__ == "__main__":
    main()

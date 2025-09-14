#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 nixfmt

import argparse
import re
import os
import subprocess
import multiprocessing
from typing import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed


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
    "pkgs/development/web/nodejs/nodejs.nix",
    "pkgs/development/python-modules/markupsafe/default.nix",
    "pkgs/by-name/li/libdrm/package.nix",
    "pkgs/stdenv/generic/check-meta.nix",
    "pkgs/development/libraries/science/math/openblas/default.nix",
    "pkgs/by-name/aa/aapt/package.nix",
    "pkgs/development/embedded/arduino/arduino-core/default.nix",
    "pkgs/development/python-modules/cryptography/default.nix",
    "pkgs/tools/typesetting/tex/texlive/tlpdb-overrides.nix",
    "pkgs/development/libraries/botan/default.nix",
    "pkgs/by-name/ap/apple-cursor/package.nix",
    "pkgs/development/compilers/ccl/default.nix",
    "pkgs/development/tools/electron/common.nix",
    "pkgs/development/python-modules/dtschema/default.nix",
    "pkgs/by-name/ba/babl/package.nix",
    "pkgs/by-name/bu/burpsuite/package.nix",
    "pkgs/by-name/co/comixcursors/package.nix",
    "pkgs/by-name/cl/clickhouse/generic.nix",
    "pkgs/applications/networking/remote/citrix-workspace/generic.nix",
    "pkgs/by-name/dm/dmtcp/package.nix",
    "pkgs/by-name/ff/fftw/package.nix",
    "pkgs/os-specific/linux/gasket/default.nix",
    "pkgs/development/libraries/libva/default.nix",
    "pkgs/desktops/gnome/extensions/clock-override/default.nix",
    "pkgs/tools/misc/logstash/7.x.nix",
    "pkgs/by-name/gi/giac/package.nix",
    "pkgs/by-name/gl/glide-media-player/package.nix",
    "pkgs/tools/package-management/nix/common-meson.nix",
    "pkgs/by-name/gr/grass-sass/package.nix",
    "pkgs/by-name/gv/gvfs/package.nix",
    "pkgs/servers/monitoring/grafana/plugins/grafana-clickhouse-datasource/default.nix",
    "pkgs/by-name/hp/hp2p/package.nix",
    "pkgs/by-name/is/isa-l/package.nix",
    "pkgs/by-name/jo/john/package.nix",
    "pkgs/by-name/lt/lttng-ust_2_12/package.nix",
    "pkgs/by-name/lu/luau-lsp/package.nix",
    "pkgs/development/compilers/mozart/binary.nix",
    "pkgs/by-name/mu/mullvad-browser/package.nix",
    "pkgs/by-name/nr/nrf-command-line-tools/package.nix",
    "pkgs/development/ocaml-modules/ocaml-freestanding/default.nix",
    "pkgs/by-name/oc/ocis_5-bin/package.nix",
    "pkgs/by-name/pg/pgbouncer/package.nix",
    "pkgs/by-name/po/polkadot/package.nix",
    "pkgs/development/python-modules/deepwave/default.nix",
    "pkgs/development/python-modules/impacket/default.nix",
    "pkgs/development/python-modules/pycurl/default.nix",
    "pkgs/by-name/ti/tiny-cuda-nn/package.nix",
    "pkgs/by-name/sa/saleae-logic/package.nix",
    "pkgs/development/compilers/sbcl/default.nix",
    "pkgs/by-name/si/simde/package.nix",
    "pkgs/by-name/si/singular/package.nix",
    "pkgs/by-name/sl/slimserver/package.nix",
    "pkgs/by-name/so/solo5/package.nix",
    "pkgs/by-name/so/sox/package.nix",
    "pkgs/by-name/st/string-machine/package.nix",
    "pkgs/by-name/ta/tabnine/package.nix",
    "pkgs/by-name/te/tela-icon-theme/package.nix",
    "pkgs/by-name/ut/ut1999/package.nix",
    "pkgs/by-name/wa/wayfarer/package.nix",
    "pkgs/by-name/we/webrtc-audio-processing_0_3/package.nix",
    "pkgs/by-name/we/webrtc-audio-processing_1/package.nix",
    "pkgs/by-name/wi/wiredtiger/package.nix",
    "pkgs/by-name/wi/wireguard-vanity-keygen/package.nix",
    "pkgs/by-name/wl/wlr-layout-ui/package.nix",
    "pkgs/desktops/xfce/core/thunar/wrapper.nix",
    "pkgs/by-name/yo/yourkit-java/package.nix",
    "pkgs/by-name/ze/zeroad-unwrapped/package.nix",
    "pkgs/by-name/fa/fasmg/package.nix",
    "pkgs/development/compilers/ghc/9.0.2-binary.nix",
    "pkgs/development/compilers/ghc/9.2.4-binary.nix",
    "pkgs/development/interpreters/python/cpython/default.nix",
    "pkgs/development/libraries/qt-5/modules/qtwebengine.nix",
    "pkgs/servers/web-apps/wordpress/packages/default.nix",
    "pkgs/by-name/xd/xdgmenumaker/package.nix",
    "pkgs/applications/networking/cluster/hadoop/containerExecutor.nix",
    "pkgs/tools/filesystems/ceph/old-python-packages/cryptography.nix",

    # other
    "pkgs/development/interpreters/acl2/default.nix",
    "pkgs/by-name/ad/adns/package.nix",
    "pkgs/by-name/ae/aeron/package.nix",
    "pkgs/by-name/ae/aeron-cpp/package.nix",
    "pkgs/misc/arm-trusted-firmware/default.nix",
    "pkgs/by-name/ap/apkg/package.nix",
    "pkgs/os-specific/darwin/apple-source-releases/patch_cmds/package.nix",
    "pkgs/by-name/aw/aws-lc/package.nix",
    "pkgs/os-specific/darwin/xcode/default.nix",
    "pkgs/development/python-modules/breezy/default.nix",
    "pkgs/development/cuda-modules/generic-builders/manifest.nix",
    "pkgs/tools/misc/grub/default.nix",
    "pkgs/development/tools/electron/binary/generic.nix",
    "pkgs/development/libraries/ffmpeg/generic.nix",
    "pkgs/development/interpreters/luajit/default.nix",
    "pkgs/tools/networking/networkmanager/default.nix",
    "pkgs/development/libraries/glew/default.nix",
    "pkgs/by-name/co/committed/package.nix",
    "pkgs/by-name/cs/csharp-ls/package.nix",
    "pkgs/by-name/dc/dconf/package.nix",
    "pkgs/by-name/do/dolphin-emu/package.nix",
    "pkgs/development/compilers/go/1.25.nix",
    "pkgs/development/compilers/go/1.24.nix",
    "pkgs/development/em-modules/generic/default.nix",
    "pkgs/development/tools/haskell/dconf2nix/default.nix",
    "pkgs/tools/system/netdata/default.nix",
    "pkgs/development/compilers/zulu/common.nix",
    "pkgs/by-name/gn/gnome-keyring/package.nix",
    "pkgs/by-name/fr/frr/package.nix",
    "pkgs/by-name/gl/glib-networking/package.nix",
    "pkgs/development/libraries/libinput/default.nix",
    "pkgs/development/libraries/gstreamer/bad/default.nix",
    "pkgs/development/libraries/gstreamer/ugly/default.nix",
    "pkgs/by-name/gl/glucose/package.nix",
    "pkgs/by-name/jo/joypixels/package.nix",
    "pkgs/by-name/li/libwacom/package.nix",
    "pkgs/by-name/po/polkit/package.nix",
    "pkgs/servers/dns/knot-resolver/default.nix",
    "pkgs/by-name/li/libcamera/package.nix",
    "pkgs/by-name/li/libgpiod/package.nix",
    "pkgs/by-name/li/libpciaccess/package.nix",
    "pkgs/by-name/li/libproxy/package.nix",
    "pkgs/by-name/li/libsystemtap/package.nix",
    "pkgs/by-name/li/libvgm/package.nix",
    "pkgs/applications/radio/limesuite/default.nix",
    "pkgs/development/libraries/mbedtls/generic.nix",
    "pkgs/by-name/mi/millet/package.nix",
    "pkgs/by-name/mo/monosat/package.nix",
    "pkgs/by-name/mu/munge/package.nix",
    "pkgs/by-name/ne/neko/package.nix",
    "pkgs/by-name/no/nofi/package.nix",
    "pkgs/by-name/ns/nsh/package.nix",
    "pkgs/by-name/op/openrw/package.nix",
    "pkgs/by-name/op/opensmt/package.nix",
    "pkgs/by-name/op/opensplat/package.nix",
    "pkgs/by-name/p1/p11-kit/package.nix",
    "pkgs/tools/archivers/p7zip/default.nix",
    "pkgs/applications/networking/browsers/palemoon/bin.nix",
    "pkgs/by-name/pa/passt/package.nix",
    "pkgs/by-name/pd/pdns-recursor/package.nix",
    "pkgs/applications/misc/pe-bear/default.nix",
    "pkgs/by-name/pe/peergos/package.nix",
    "pkgs/development/compilers/polyml/5.6.nix",
    "pkgs/by-name/ti/tinyxxd/package.nix",
    "pkgs/by-name/qb/qbittorrent-cli/package.nix",
    "pkgs/by-name/sa/sauerbraten/package.nix",
    "pkgs/development/lisp-modules/packages.nix",
    "pkgs/by-name/sf/sfml_2/package.nix",
    "pkgs/applications/science/machine-learning/shogun/default.nix",
    "pkgs/by-name/sp/splitcode/package.nix",
    "pkgs/by-name/sq/sqlpkg-cli/package.nix",
    "pkgs/by-name/sq/squeezelite/package.nix",
    "pkgs/by-name/su/superlu/package.nix",
    "pkgs/by-name/su/supersonic/package.nix",
    "pkgs/by-name/ta/tacent/package.nix",
    "pkgs/by-name/ta/tahoe-lafs/package.nix",
    "pkgs/by-name/te/tetrio-plus/package.nix",
    "pkgs/by-name/th/thepeg/package.nix",
    "pkgs/by-name/tr/tracy/package.nix",
    "pkgs/by-name/ve/verapdf/package.nix",
    "pkgs/by-name/vg/vgmstream/package.nix",
    "pkgs/by-name/vp/vpnc/package.nix",
    "pkgs/applications/misc/ape/default.nix",
    "pkgs/by-name/bu/bulk_extractor/package.nix",
    "pkgs/by-name/bu/bun/package.nix",
    "pkgs/development/haskell-modules/configuration-nix.nix",
    "pkgs/games/crawl/default.nix",
    "pkgs/development/libraries/db/generic.nix",
    "pkgs/applications/audio/dfasma/default.nix",
    "pkgs/desktops/enlightenment/efl/default.nix",
    "pkgs/by-name/hu/hunspell/dictionaries.nix",
    "pkgs/by-name/je/jed/package.nix",
    "pkgs/by-name/ne/netbird/package.nix",
    "pkgs/by-name/nv/nvpy/package.nix",
    "pkgs/applications/video/obs-studio/plugins/obs-ndi/default.nix",
    "pkgs/by-name/op/opensoldat/package.nix",
    "pkgs/by-name/pe/penpot-desktop/package.nix",
    "pkgs/development/python-modules/gurobipy/default.nix",
    "pkgs/by-name/re/redeclipse/package.nix",
    "pkgs/development/compilers/scala/2.x.nix",
    "pkgs/by-name/tr/trrntzip/package.nix",
    "pkgs/by-name/ve/vectorscan/package.nix",
    "pkgs/build-support/go/module.nix",
    "pkgs/by-name/ya/yazi/plugins/default.nix",
    "pkgs/by-name/ne/netflix/package.nix",
    "pkgs/development/libraries/kde-frameworks/default.nix",
    "pkgs/by-name/si/signal-desktop-bin/generic.nix",
    "pkgs/development/compilers/go/binary.nix",
    "pkgs/os-specific/bsd/freebsd/pkgs/drm-kmod-firmware.nix",
    "pkgs/by-name/io/iozone/package.nix",
    "pkgs/development/r-modules/default.nix",
    "pkgs/os-specific/bsd/freebsd/pkgs/libspl.nix",
    "pkgs/development/compilers/factor-lang/factor99.nix",
    "pkgs/by-name/ro/root/tests/test-thisroot.nix",

    # avoid spurious rebuild
    "pkgs/tools/misc/anystyle-cli/default.nix",

    # pkgs.lib
    "pkgs/development/python-modules/azure-mgmt-common/default.nix",
    "pkgs/development/python-modules/azure-mgmt-core/default.nix",
    "pkgs/development/python-modules/azure-mgmt-nspkg/default.nix",
    "pkgs/development/python-modules/django-leaflet/default.nix",
    "pkgs/development/python-modules/dopy/default.nix",
    "pkgs/development/python-modules/escapism/default.nix",
    "pkgs/development/python-modules/facebook-sdk/default.nix",
    "pkgs/development/python-modules/opcua-widgets/default.nix",

    # maintainers = teams
    "pkgs/applications/video/kodi/addons/bluetooth-manager/default.nix",

    # platforms = system...
    "pkgs/by-name/tc/tcb/package.nix",

    # wrong attrs used?
    "pkgs/servers/home-assistant/custom-lovelace-modules/custom-sidebar/package.nix",
    "pkgs/by-name/ma/maphosts/package.nix",
    "pkgs/by-name/me/mercurial/package.nix",
    "pkgs/by-name/pg/pgf2/package.nix",
    "pkgs/by-name/pg/pgf3/package.nix",
    "pkgs/development/python-modules/flask/default.nix",
    "pkgs/development/python-modules/motmetrics/default.nix",
    "pkgs/development/python-modules/scikit-learn/default.nix",
    "pkgs/development/python-modules/sphinx-version-warning/default.nix",
    "pkgs/development/libraries/quarto/default.nix",
    "pkgs/desktops/xfce/applications/xfmpc/default.nix",
    "pkgs/development/python-modules/textx/tests.nix",
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

        pattern = rf"\s({key}\s*=\s*)(\[[^\]]*\]|[^;]+)(;)"
        matches = re.finditer(pattern, content)

        for match in matches:
            full_match = match.group(0)
            prefix = match.group(1)
            value = match.group(2)
            suffix = match.group(3)

            if " if " in value or value.startswith("if "):
                # Skip any conditional expressions for now
                continue

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
                if value.strip().startswith("lib.") or value.startswith('"') or value.startswith("'") or value.startswith("with ") or value.startswith("if ") or value.startswith("{") or value.startswith("["):
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
    (r"hydraPlatforms = with platforms; ", "hydraPlatforms = with lib.platforms; "),
    (r"license = with licenses; ", "license = with lib.licenses; "),
    (r"sourceProvenance = with sourceTypes; ", "sourceProvenance = with lib.sourceTypes; "),
    (r"teams = with teams; ", "teams = with lib.teams; "),
    list_or_value("platforms"),
    list_or_value("badPlatforms", "platforms"),
    list_or_value("hydraPlatforms", "platforms"),
    list_or_value("maintainers"),
    list_or_value("license"),
    list_or_value("teams"),
    (r" sourceTypes.binaryBytecode", " lib.sourceTypes.binaryBytecode"),
    (r" sourceTypes.binaryNativeCode", " lib.sourceTypes.binaryNativeCode"),
    (r" sourceTypes.fromSource", " lib.sourceTypes.fromSource"),
    (r"broken = versionOlder ", "broken = lib.versionOlder "),
    (r"broken = versionAtLeast ", "broken = lib.versionAtLeast "),
]


def transform_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    if "meta = with lib;" not in content:
        return False

    for rule in RULES:
        if isinstance(rule, Callable):
            content = rule(content)
        else:
            content = re.sub(rule[0], rule[1], content)

    with open(file_path, "w") as f:
        f.write(content)

    return True


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
    files = [f for f in files if not any(f.endswith(ignored) for ignored in FILES_TO_IGNORE)]

    nfiles = len(files)

    # Use all available CPU cores for parallel processing
    max_workers = multiprocessing.cpu_count()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        batch = list(enumerate(files))
        futures = [executor.submit(process_file, idx_file, nfiles) for idx_file in batch]
        for future in as_completed(futures):
            future.result()

def process_file(idx_file, nfiles):
    i, file = idx_file
    print(f"Processing file {i+1}/{nfiles}: {file}")
    #os.system("git checkout " + file)

    if not transform_file(file):
        return

    # Sanity check: run nixfmt on the file and see that it doesn't fail; if it does, git checkout - we'll address it later
    try:
        subprocess.run(["nixfmt", file], check=True)
    except subprocess.CalledProcessError:
        print(f"nix fmt failed on {file}, reverting changes")
        subprocess.run(["git", "checkout", file])

if __name__ == "__main__":
    main()

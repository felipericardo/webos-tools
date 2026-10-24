"""Build a minimal webOS IPK (ar: debian-binary, control.tar.gz, data.tar.gz).

Usage: build_ipk.py <app-dir> <out.ipk>   (app id/version read from appinfo.json)
"""
import io
import json
import os
import sys
import tarfile
import time


def add_entry(tar, name, data, mode=None):
    info = tarfile.TarInfo(name)
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    info.mtime = int(time.time())
    if data is None:
        info.type, info.mode = tarfile.DIRTYPE, 0o755
        tar.addfile(info)
    else:
        info.size, info.mode = len(data), mode or 0o644
        tar.addfile(info, io.BytesIO(data))


def add_tree(tar, src_dir, arc_prefix):
    for root, dirs, files in os.walk(src_dir):
        dirs.sort()
        rel = os.path.relpath(root, src_dir)
        arc_dir = arc_prefix if rel == "." else f"{arc_prefix}/{rel}"
        add_entry(tar, arc_dir, None)
        for f in sorted(files):
            with open(os.path.join(root, f), "rb") as fh:
                add_entry(tar, f"{arc_dir}/{f}", fh.read())


def targz(build):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        build(tar)
    return buf.getvalue()


def ar_member(name, data):
    hdr = f"{name:<16}{int(time.time()):<12}{0:<6}{0:<6}{'100644':<8}{len(data):<10}`\n".encode()
    return hdr + data + (b"\n" if len(data) % 2 else b"")


def main():
    app_dir, out = sys.argv[1], sys.argv[2]
    with open(os.path.join(app_dir, "appinfo.json")) as fh:
        info = json.load(fh)
    app_id, version = info["id"], info["version"]
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(app_dir) for f in fs)

    def data(tar):
        for d in ("usr", "usr/palm", "usr/palm/applications", "usr/palm/packages"):
            add_entry(tar, d, None)
        add_tree(tar, app_dir, f"usr/palm/applications/{app_id}")
        add_entry(tar, f"usr/palm/packages/{app_id}", None)
        pkg = json.dumps({"id": app_id, "version": version, "app": app_id}, indent=2).encode()
        add_entry(tar, f"usr/palm/packages/{app_id}/packageinfo.json", pkg)

    control = (f"Package: {app_id}\nVersion: {version}\nSection: misc\nPriority: optional\n"
               f"Architecture: all\nInstalled-Size: {size}\nMaintainer: N/A <nobody@example.com>\n"
               f"Description: This is a webOS application.\nwebOS-Package-Format-Version: 2\n"
               f"webOS-Packager-Version: x.y.x\n").encode()

    with open(out, "wb") as f:
        f.write(b"!<arch>\n")
        f.write(ar_member("debian-binary", b"2.0\n"))
        f.write(ar_member("control.tar.gz", targz(lambda t: add_entry(t, "./control", control))))
        f.write(ar_member("data.tar.gz", targz(data)))
    print(f"{out}: {app_id} {version}")


if __name__ == "__main__":
    main()

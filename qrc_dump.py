#!/usr/bin/env python3
"""Dump zlib-compressed Qt resource (rcc) payloads embedded in an ELF.

Qt's rcc stores compressed files as a 4-byte big-endian uncompressed size
followed by a zlib stream. We scan for zlib headers, inflate, keep anything
that decodes and whose prefixed size matches, and write it out. Uncompressed
resources are already visible with `strings`, so they're not handled here.

Usage: qrc_dump.py <binary> <out-dir>
"""
import os
import sys
import zlib

ZLIB_HEADERS = (b"\x78\x9c", b"\x78\xda", b"\x78\x01", b"\x78\x5e")


def guess_ext(data: bytes) -> str:
    head = data[:200].lstrip()
    if head.startswith(b"\x89PNG"):
        return ".png"
    if b"import Qt" in data[:2000] or b"import " in head[:20]:
        return ".qml"
    if head.startswith(b"<"):
        return ".xml"
    if b"function " in data[:4000] or head.startswith(b".pragma") or head.startswith(b"/*"):
        return ".js"
    return ".bin"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    path, out_dir = sys.argv[1], sys.argv[2]
    blob = open(path, "rb").read()
    os.makedirs(out_dir, exist_ok=True)

    found = 0
    i = 4
    while i < len(blob) - 2:
        if blob[i:i + 2] not in ZLIB_HEADERS:
            i += 1
            continue
        expected = int.from_bytes(blob[i - 4:i], "big")
        d = zlib.decompressobj()
        try:
            data = d.decompress(blob[i:i + max(expected * 2, 1 << 20)])
        except zlib.error:
            i += 1
            continue
        if not d.eof or len(data) != expected or expected == 0:
            i += 1
            continue
        found += 1
        name = f"{i:08x}{guess_ext(data)}"
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
        i += len(blob[i:]) - len(d.unused_data)
    print(f"{found} resources written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

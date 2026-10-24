# webos-tools

Development helpers for the webOS apps used on the rooted LG TVs (homelab personal project).
Run them from the Mac; nothing here is installed on a TV.

| Tool | What it does |
|---|---|
| `build_ipk.py <app-dir> <out.ipk>` | Package an app folder (with `appinfo.json`) as a webOS IPK. No `ares-cli` needed. |
| `install_ipk.sh <tv-host> <file.ipk> [--launch]` | Copy an IPK to a TV and install it with the system installer; optionally launch it. |
| `cdp_eval.mjs <port> <title> '<js>'` | Evaluate JavaScript in a page of the TV's web engine over the Chrome DevTools Protocol. Needs Node 22+. |
| `qrc_dump.py <binary> <out-dir>` | Extract zlib-compressed Qt resources (QML/JS) embedded in a binary. Reverse-engineering aid. |

## DevTools access

The TV's web engine (WebAppMgr) listens on `127.0.0.1:9998`. Tunnel it first:

```sh
ssh -f -N -L 19998:127.0.0.1:9998 root@<tv-host>
/opt/homebrew/opt/node@22/bin/node cdp_eval.mjs 19998 "Cam Test" 'document.title'
```

## Gotchas

- `luna-send` prints nothing when run directly in an SSH session; run it detached
  (`nohup ... < /dev/null &`) and read its output file. The scripts here already do.
- Keep files from the TV's firmware out of every repo; they are LG's proprietary files.

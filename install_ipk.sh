#!/bin/sh
# Install an IPK on a rooted webOS TV through the system installer (appInstallService),
# optionally launching it afterwards.
# Usage: install_ipk.sh <tv-host> <file.ipk> [--launch]
set -e
TV="$1"; IPK="$2"; LAUNCH="$3"
[ -n "$TV" ] && [ -f "$IPK" ] || { echo "usage: $0 <tv-host> <file.ipk> [--launch]" >&2; exit 2; }
APP_ID=$(basename "$IPK" | sed 's/_.*//')

scp "$IPK" "root@$TV:/tmp/install.ipk"
# luna-send prints nothing when run straight in an SSH session: run it detached and read a file.
ssh "root@$TV" "
nohup luna-send -i luna://com.webos.appInstallService/dev/install '{\"id\":\"$APP_ID\",\"ipkUrl\":\"/tmp/install.ipk\",\"subscribe\":true}' > /tmp/inst.log 2>&1 < /dev/null &
P=\$!; i=0
while [ \$i -lt 60 ]; do grep -q -E 'install failed|\"installed\"' /tmp/inst.log && break; sleep 1; i=\$((i+1)); done
kill \$P 2>/dev/null
STATE=\$(tr -d '\n' < /tmp/inst.log | grep -o '\"state\":\"[^\"]*\"' | tail -1)
REASON=\$(tr -d '\n' < /tmp/inst.log | grep -o '\"reason\":\"[^\"]*\"' | tail -1)
echo \"$APP_ID: \$STATE \$REASON\"
rm -f /tmp/install.ipk /tmp/inst.log
if [ '$LAUNCH' = '--launch' ]; then
  nohup luna-send -n 1 -w 4000 luna://com.webos.applicationManager/launch '{\"id\":\"$APP_ID\"}' > /tmp/l.log 2>&1 < /dev/null &
  sleep 2; echo \"launch: \$(cat /tmp/l.log)\"; rm -f /tmp/l.log
fi
echo \"\$STATE\" | grep -q '\"installed\"'
"

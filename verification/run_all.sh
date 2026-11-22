#!/bin/bash
set -u
V="$(dirname "$(readlink -f "$0")")"
fail=0
python3 "$V/verify.py" "$V"/../results/octahedra_genus*.jsonl || fail=1
for f in mizhaev rostvigh szilassi; do python3 "$V/verify.py" --one "$V/controls/$f.json" || fail=1; done
for f in "$V"/controls/neg_*.json; do python3 "$V/verify.py" --one "$f" --expect-invalid || fail=1; done
[ $fail = 0 ] && echo "ALL CHECKS PASS" || echo "SOME CHECKS FAIL"
exit $fail

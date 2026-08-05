#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd "$(dirname "$0")/.." && pwd)
script="$root_dir/scripts/ecs-test-autodeploy.sh"
service="$root_dir/systemd/equipment-test-autodeploy.service"
timer="$root_dir/systemd/equipment-test-autodeploy.timer"
environment="$root_dir/systemd/equipment-test-autodeploy.env.example"

for required in "$script" "$service" "$timer" "$environment"; do
  [[ -f "$required" ]] || { echo "missing $required" >&2; exit 1; }
done

grep -Fq 'codex/task-013-prototype-fidelity-remediation' "$script"
grep -Fq 'flock' "$script"
grep -Fq 'fetch --prune origin' "$script"
grep -Fq 'docker compose' "$script"
grep -Fq '/healthz' "$script"
grep -Fq 'rollback' "$script"
grep -Fq 'OnUnitActiveSec=30s' "$timer"
grep -Fq 'ExecStart=/usr/local/sbin/equipment-test-autodeploy' "$service"
grep -Fq 'BRANCH=codex/task-013-prototype-fidelity-remediation' "$environment"
grep -Fq 'HEALTH_URL=https://127.0.0.1:18443/healthz' "$environment"

echo 'ECS test auto-deploy contract: PASS'

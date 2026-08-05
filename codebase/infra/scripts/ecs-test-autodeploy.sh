#!/usr/bin/env bash
set -euo pipefail

repository_url=${REPOSITORY_URL:-https://github.com/QI-code1992/Equipment-repair.git}
branch=${BRANCH:-codex/task-013-prototype-fidelity-remediation}
preview_root=${PREVIEW_ROOT:-/opt/equipment-platform/previews}
project_name=${PROJECT_NAME:-equipment-preview-77fbc42}
health_url=${HEALTH_URL:-https://127.0.0.1:18443/healthz}
cache_dir=${CACHE_DIR:-/opt/equipment-platform/autodeploy/repository}
state_file=${STATE_FILE:-/opt/equipment-platform/autodeploy/deployed-sha}
lock_file=${LOCK_FILE:-/run/equipment-test-autodeploy.lock}

exec 9>"$lock_file"
flock -n 9 || exit 0

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

fail() {
  log "ERROR $*"
  exit 1
}

prepare_repository() {
  if [[ ! -d "$cache_dir/.git" ]]; then
    install -d -m 0755 "$(dirname "$cache_dir")"
    git clone --no-checkout "$repository_url" "$cache_dir"
  fi
  git -C "$cache_dir" fetch --prune origin "$branch"
}

copy_runtime_files() {
  local source_dir=$1
  local target_dir=$2
  local path
  for path in compose.yml preview-api.Dockerfile preview-web.Dockerfile preview-nginx.conf runtime.env certs secrets; do
    [[ -e "$source_dir/$path" ]] || fail "active release is missing $path"
    cp -a "$source_dir/$path" "$target_dir/$path"
  done
}

wait_for_health() {
  local attempt
  for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error --insecure --max-time 5 "$health_url" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  return 1
}

rollback() {
  local active_dir=$1
  local api_image_id=$2
  local web_image_id=$3
  log "rollback to $(basename "$active_dir")"
  docker tag "$api_image_id" "$project_name-api"
  docker tag "$web_image_id" "$project_name-web"
  docker compose -p "$project_name" -f "$active_dir/compose.yml" up -d --no-build --force-recreate api web
}

install -d -m 0755 "$(dirname "$state_file")"
[[ -L "$preview_root/current" ]] || fail "missing active release symlink: $preview_root/current"
active_dir=$(readlink -f "$preview_root/current")
[[ -f "$active_dir/SOURCE_COMMIT" ]] || fail "active release has no SOURCE_COMMIT"
active_sha=$(tr -d '[:space:]' < "$active_dir/SOURCE_COMMIT")

prepare_repository
target_sha=$(git -C "$cache_dir" rev-parse "origin/$branch")
if [[ "$target_sha" == "$active_sha" ]]; then
  exit 0
fi

if ! git -C "$cache_dir" diff --quiet "$active_sha" "$target_sha" -- codebase/backend/alembic; then
  fail "automatic deployment refuses migration changes; deploy $target_sha manually"
fi

candidate_dir="$preview_root/$target_sha"
if [[ ! -d "$candidate_dir/source" ]]; then
  install -d -m 0755 "$candidate_dir/source"
  git -C "$cache_dir" archive "$target_sha" | tar -x -C "$candidate_dir/source"
  copy_runtime_files "$active_dir" "$candidate_dir"
  printf '%s\n' "$target_sha" > "$candidate_dir/SOURCE_COMMIT"
fi

api_image_id=$(docker inspect --format '{{.Image}}' "$project_name-api-1")
web_image_id=$(docker inspect --format '{{.Image}}' "$project_name-web-1")
log "build candidate=$target_sha active=$active_sha"
docker compose -p "$project_name" -f "$candidate_dir/compose.yml" build api web

if ! docker compose -p "$project_name" -f "$candidate_dir/compose.yml" up -d --no-build --force-recreate api web; then
  rollback "$active_dir" "$api_image_id" "$web_image_id"
  fail "candidate startup failed: $target_sha"
fi

if ! wait_for_health; then
  rollback "$active_dir" "$api_image_id" "$web_image_id"
  fail "candidate health check failed: $target_sha"
fi

ln -s "$candidate_dir" "$preview_root/current.next"
mv -Tf "$preview_root/current.next" "$preview_root/current"
printf '%s\n' "$target_sha" > "$state_file"
log "DEPLOYED sha=$target_sha"

#!/usr/bin/env bash
# Gitee wiki 读写。清空 helper 后以 GITEE_TOKEN 认证，避开本机 GitHub 凭据。
set -euo pipefail

usage() {
  echo "usage: $0 <owner/repo> <workdir> <clone|pull|push> [commit message]" >&2
  exit 2
}

[[ $# -ge 3 ]] || usage
owner_repo="$1"
workdir="$2"
action="$3"
message="${4:-docs: update wiki}"

: "${GITEE_TOKEN:?GITEE_TOKEN 未设置}"
auth=(
  git
  -c credential.helper=
  -c "http.extraheader=Authorization: Basic $(printf 'oauth2:%s' "$GITEE_TOKEN" | base64 -w0)"
)
url="https://gitee.com/${owner_repo}.wiki.git"

case "$action" in
  clone)
    GIT_TERMINAL_PROMPT=0 "${auth[@]}" clone "$url" "$workdir"
    ;;
  pull)
    GIT_TERMINAL_PROMPT=0 "${auth[@]}" -C "$workdir" pull --ff-only
    ;;
  push)
    "${auth[@]}" -C "$workdir" add -A
    if "${auth[@]}" -C "$workdir" diff --cached --quiet; then
      echo "nothing to commit" >&2
      exit 0
    fi
    "${auth[@]}" -C "$workdir" commit -m "$message"
    GIT_TERMINAL_PROMPT=0 "${auth[@]}" -C "$workdir" push origin HEAD
    ;;
  *)
    usage
    ;;
esac

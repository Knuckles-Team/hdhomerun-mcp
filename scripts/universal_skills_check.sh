#!/usr/bin/env bash
# Run one universal-skills gate script: scripts/universal_skills_check.sh <name> [args...]
# <name> is check_atomicity, check_frontmatter_portability or check_path_portability.
# Resolution order: $UNIVERSAL_SKILLS_SCRIPTS, the workspace checkout, then the published
# universal-skills main (downloaded to the cache), so the hook also runs on a CI runner.
set -euo pipefail
name="$1"; shift
dir="${UNIVERSAL_SKILLS_SCRIPTS:-}"
if [ -z "$dir" ] || [ ! -f "$dir/$name.py" ]; then
  dir=/home/apps/workspace/agent-packages/skills/universal-skills/scripts
fi
if [ ! -f "$dir/$name.py" ]; then
  dir="${XDG_CACHE_HOME:-$HOME/.cache}/universal-skills-gates"
  mkdir -p "$dir"
  tmp=$(mktemp "$dir/$name.XXXXXX")
  curl -fsSL --retry 3 -o "$tmp" "https://raw.githubusercontent.com/Knuckles-Team/universal-skills/main/scripts/$name.py"
  mv "$tmp" "$dir/$name.py"
fi
exec python3 "$dir/$name.py" "$@"

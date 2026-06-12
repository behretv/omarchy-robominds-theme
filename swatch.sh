#!/usr/bin/env bash
# Visualize colors from colors.toml and update PNG swatches.
set -e

dir="$(dirname "$0")"
toml="$dir/colors.toml"
swatch_dir="$dir/swatches"
width=${1:-10}

[[ -f "$toml" ]] || { echo "colors.toml not found at $toml"; exit 1; }

mkdir -p "$swatch_dir"

# Collect unique hex values from colors.toml
declare -A hexes
while IFS='=' read -r key val; do
  key="${key// /}"
  val="${val//\"/}"
  val="${val// /}"
  [[ -z "$key" || "$key" == \#* || -z "$val" ]] && continue
  hex="${val#"#"}"

  # Generate PNG if missing
  png="$swatch_dir/$hex.png"
  if [[ ! -f "$png" ]]; then
    convert -size 15x15 "xc:#$hex" "$png" 2>/dev/null
    echo "  created $png"
  fi
  hexes["$hex"]=1
done <"$toml"

# Remove stale PNGs not in current palette
for png in "$swatch_dir"/*.png; do
  name="${png##*/}"
  hex="${name%.png}"
  [[ -z "${hexes[$hex]+x}" ]] && rm "$png" && echo "  removed stale $png"
done

# Terminal output
print_swatch() {
  local hex="$1" label="$2"
  hex="${hex#"#"}"
  local r=$((16#${hex:0:2})) g=$((16#${hex:2:2})) b=$((16#${hex:4:2}))
  local blocks=""
  for ((i = 0; i < width; i++)); do blocks+="█"; done
  printf "\e[48;2;%d;%d;%dm\e[38;2;%d;%d;%dm%s\e[0m %s\n" "$r" "$g" "$b" "$r" "$g" "$b" "$blocks" "$label"
}

echo ""
while IFS='=' read -r key val; do
  key="${key// /}"
  val="${val//\"/}"
  val="${val// /}"
  [[ -z "$key" || "$key" == \#* || -z "$val" ]] && continue
  print_swatch "$val" "$key = $val"
done <"$toml"
echo ""

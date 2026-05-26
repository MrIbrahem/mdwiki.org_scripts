#!/bin/bash
# deploy_secure.sh

# 1. Validate if GH_TOKEN exists in the environment
# Toolforge envvars are automatically loaded in most contexts
: "${GH_TOKEN:?GH_TOKEN is not set. Use 'toolforge envvars create' to set it.}"

# 2. Setup security credentials
ASKPASS_SCRIPT="$(mktemp)"
trap 'rm -f "$ASKPASS_SCRIPT"' EXIT
cat > "$ASKPASS_SCRIPT" <<'EOF'
#!/bin/sh
echo "$GH_TOKEN"
EOF
chmod 700 "$ASKPASS_SCRIPT"
export GIT_ASKPASS="$ASKPASS_SCRIPT"
export GIT_USERNAME="${USER_NAME:-MrIbrahem}"
export GIT_TERMINAL_PROMPT=0
# 3. Call the original script and pass all arguments
# "$@" ensures all parameters ($1, $2, etc.) are passed through
$HOME/shs/deploy_repo.sh "$@"

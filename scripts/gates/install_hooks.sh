#!/bin/bash
#
# Install Git Hooks for 4-Gate System
#
# This script installs pre-commit hooks that run gate validations
# before allowing commits.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================"
echo "Installing AI-PAL 4-Gate Pre-Commit Hooks"
echo "================================================================"

# Find Git directory
if [ -d ".git" ]; then
    GIT_DIR=".git"
elif [ -f ".git" ]; then
    # Worktree - read git dir from file
    GIT_DIR=$(cat .git | sed 's/gitdir: //')
else
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

HOOKS_DIR="${GIT_DIR}/hooks"

# Create hooks directory if it doesn't exist
mkdir -p "${HOOKS_DIR}"

# Create pre-commit hook
HOOK_FILE="${HOOKS_DIR}/pre-commit"

cat > "${HOOK_FILE}" << 'HOOK_SCRIPT'
#!/bin/bash
#
# AI-PAL 4-Gate Pre-Commit Hook
#
# Runs all 4 gates before allowing commit:
# - Gate 1: Net Agency
# - Gate 2: Extraction Static Analysis
# - Gate 3: Humanity Override
# - Gate 4: Performance Parity

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Run gate checks
python3 "${PROJECT_ROOT}/scripts/gates/pre_commit_gate_check.py"

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Gate checks failed. Commit blocked."
    echo ""
    echo "To bypass (not recommended):"
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi

exit 0
HOOK_SCRIPT

# Make hook executable
chmod +x "${HOOK_FILE}"

echo -e "${GREEN}✓ Pre-commit hook installed at: ${HOOK_FILE}${NC}"

# Make the gate check script executable
GATE_SCRIPT="scripts/gates/pre_commit_gate_check.py"
if [ -f "${GATE_SCRIPT}" ]; then
    chmod +x "${GATE_SCRIPT}"
    echo -e "${GREEN}✓ Gate check script made executable${NC}"
fi

echo ""
echo "================================================================"
echo -e "${GREEN}Installation complete!${NC}"
echo "================================================================"
echo ""
echo "The 4-gate system will now run automatically before each commit."
echo ""
echo "To test the hooks:"
echo "  git commit --allow-empty -m \"Test commit\""
echo ""
echo "To bypass hooks (not recommended):"
echo "  git commit --no-verify"
echo ""
echo "To uninstall hooks:"
echo "  rm ${HOOK_FILE}"
echo ""

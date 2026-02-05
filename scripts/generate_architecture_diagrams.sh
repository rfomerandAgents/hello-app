#!/bin/bash
# Generate dependency visualizations for {{PROJECT_NAME}} architecture

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARCH_DIR="$PROJECT_ROOT/ipe_docs/architecture"

echo "🎨 Generating Architecture Diagrams..."
echo "======================================"

# Create architecture directory if it doesn't exist
mkdir -p "$ARCH_DIR"

# Check if pydeps is installed
if ! command -v pydeps &> /dev/null; then
    echo "⚠️  pydeps not found. Installing..."
    pip install pydeps
fi

echo ""
echo "📊 Generating ADW dependency graph..."
cd "$PROJECT_ROOT"
pydeps adws/adw_modules \
    --max-bacon=3 \
    --cluster \
    --exclude-exact "tests,__pycache__,*.pyc" \
    -o "$ARCH_DIR/adw_dependencies.svg" \
    2>/dev/null || echo "  ⚠️  Skipped (module structure issue)"

echo "📊 Generating IPE dependency graph..."
pydeps ipe/ipe_modules \
    --max-bacon=3 \
    --cluster \
    --exclude-exact "tests,__pycache__,*.pyc" \
    -o "$ARCH_DIR/ipe_dependencies.svg" \
    2>/dev/null || echo "  ⚠️  Skipped (module structure issue)"

echo "📊 Generating Shared modules dependency graph..."
pydeps shared \
    --max-bacon=2 \
    --cluster \
    --exclude-exact "tests,__pycache__,*.pyc" \
    -o "$ARCH_DIR/shared_dependencies.svg" \
    2>/dev/null || echo "  ⚠️  Skipped (module structure issue)"

echo ""
echo "🌐 Generating Next.js app dependency graph..."

# Check if madge is installed
if ! command -v madge &> /dev/null; then
    echo "⚠️  madge not found. Installing..."
    npm install -g madge
fi

cd "$PROJECT_ROOT/app"
madge --image "$ARCH_DIR/app_dependencies.svg" \
    --exclude 'node_modules|\.next|out' \
    components/ app/ \
    2>/dev/null || echo "  ⚠️  Skipped (module structure issue)"

echo ""
echo "✅ Architecture diagrams generated!"
echo ""
echo "📂 Output directory: $ARCH_DIR"
echo ""
echo "Generated files:"
ls -lh "$ARCH_DIR"/*.svg 2>/dev/null || echo "  No SVG files generated (check for errors above)"

echo ""
echo "📖 View the complete architecture documentation:"
echo "   $ARCH_DIR/system-overview.md"
echo ""
echo "💡 Tip: Open system-overview.md in VS Code with Mermaid Preview extension"
echo "   or view on GitHub for rendered diagrams!"

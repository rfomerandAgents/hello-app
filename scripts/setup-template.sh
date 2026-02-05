#!/bin/bash
# Template Setup Script
# Run this after cloning the template to replace all placeholders

set -e

echo "🚀 Template Setup"
echo "=================="
echo ""

# Prompt for values
read -p "Project Name (e.g., 'My App'): " PROJECT_NAME
read -p "Project Name Slug (e.g., 'my-app'): " PROJECT_NAME_SLUG
read -p "Project Description: " PROJECT_DESCRIPTION
read -p "Domain (e.g., 'myapp.com'): " DOMAIN
read -p "GitHub Owner (username or org): " GITHUB_OWNER
read -p "GitHub Repo Name: " GITHUB_REPO_NAME
read -p "Terraform Organization: " TF_ORGANIZATION
read -p "Terraform Project: " TF_PROJECT

# Construct GitHub URL
GITHUB_REPO_URL="https://github.com/${GITHUB_OWNER}/${GITHUB_REPO_NAME}"

echo ""
echo "Configuration:"
echo "  PROJECT_NAME: ${PROJECT_NAME}"
echo "  PROJECT_NAME_SLUG: ${PROJECT_NAME_SLUG}"
echo "  PROJECT_DESCRIPTION: ${PROJECT_DESCRIPTION}"
echo "  DOMAIN: ${DOMAIN}"
echo "  GITHUB_OWNER: ${GITHUB_OWNER}"
echo "  GITHUB_REPO_URL: ${GITHUB_REPO_URL}"
echo "  TF_ORGANIZATION: ${TF_ORGANIZATION}"
echo "  TF_PROJECT: ${TF_PROJECT}"
echo ""

read -p "Proceed with replacement? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Replacing placeholders..."

# Function to replace in files
replace_in_files() {
    local search="$1"
    local replace="$2"

    # Use find + sed for cross-platform compatibility
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        find . -type f \( -name "*.md" -o -name "*.tf" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.py" -o -name "*.sh" -o -name "*.example" \) \
            -not -path "./.git/*" \
            -not -path "./node_modules/*" \
            -not -path "./.venv/*" \
            -exec sed -i '' "s|${search}|${replace}|g" {} \;
    else
        # Linux
        find . -type f \( -name "*.md" -o -name "*.tf" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.py" -o -name "*.sh" -o -name "*.example" \) \
            -not -path "./.git/*" \
            -not -path "./node_modules/*" \
            -not -path "./.venv/*" \
            -exec sed -i "s|${search}|${replace}|g" {} \;
    fi
}

# Replace placeholders (order matters - more specific first)
replace_in_files "{{PROJECT_NAME_SLUG}}" "${PROJECT_NAME_SLUG}"
replace_in_files "{{PROJECT_NAME}}" "${PROJECT_NAME}"
replace_in_files "{{PROJECT_DESCRIPTION}}" "${PROJECT_DESCRIPTION}"
replace_in_files "{{GITHUB_REPO_URL}}" "${GITHUB_REPO_URL}"
replace_in_files "{{GITHUB_REPO_NAME}}" "${GITHUB_REPO_NAME}"
replace_in_files "{{GITHUB_OWNER}}" "${GITHUB_OWNER}"
replace_in_files "{{DOMAIN}}" "${DOMAIN}"
replace_in_files "{{TF_ORGANIZATION}}" "${TF_ORGANIZATION}"
replace_in_files "{{TF_PROJECT}}" "${TF_PROJECT}"

echo "✅ Placeholders replaced!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and configure secrets"
echo "  2. Set up GitHub repository secrets"
echo "  3. Initialize Terraform Cloud workspaces"
echo "  4. Add your application code to app/"
echo "  5. Run /install to set up dependencies"
echo ""
echo "For detailed instructions, see README.md"

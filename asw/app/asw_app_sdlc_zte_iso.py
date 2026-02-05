#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ASW App SDLC ZTE Iso - Zero Touch Execution: Complete SDLC with automatic shipping

Usage: uv run asw_app_sdlc_zte_iso.py <issue-number> [asw-id] [--skip-e2e] [--skip-resolution]

This script runs the complete ASW App SDLC pipeline with automatic shipping:
1. asw_app_plan_iso.py - Planning phase (isolated)
2. asw_app_build_iso.py - Implementation phase (isolated)
3. asw_app_test_iso.py - Testing phase (isolated)
4. asw_app_review_iso.py - Review phase (isolated)
5. asw_app_document_iso.py - Documentation phase (isolated)
6. asw_app_ship_iso.py - Ship phase (approve & merge PR)

FULL-DEPLOY MODE:
If the GitHub issue description contains the keyword "full-deploy", the workflow will
automatically continue after the ship phase to:
7. Build new AMI with Packer (via ipe_build.py → GitHub Actions)
8. Deploy infrastructure with Terraform (via ipe_deploy.py → GitHub Actions)
9. Update DNS in Cloudflare (automatic in GitHub Actions workflow)

ZTE = Zero Touch Execution: The entire workflow runs to completion without
human intervention, automatically shipping code to production if all phases pass.

The scripts are chained together via persistent state (asw_app_state.json).
Each phase runs on the same git worktree with dedicated ports.

FULL-DEPLOY REQUIREMENTS:
- GitHub CLI (gh) must be installed and authenticated
- AWS credentials must be configured for AMI builds
- HCP Terraform credentials must be configured for deployments
- Cloudflare API token must be configured for DNS updates
- Issue description must contain "full-deploy" keyword (case-insensitive)

EXAMPLES:
  # Regular ZTE (code only)
  uv run asw_app_sdlc_zte_iso.py 123

  # ZTE with full-deploy (code + infrastructure)
  # Create issue #456 with description: "Add new feature with full-deploy"
  uv run asw_app_sdlc_zte_iso.py 456
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from asw.modules.workflow_ops import ensure_asw_app_id, detect_full_deploy
from asw.modules.github import make_issue_comment, get_issue_description


def main():
    """Main entry point."""
    # Check for flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv

    # Remove flags from argv
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    if skip_resolution:
        sys.argv.remove("--skip-resolution")

    if len(sys.argv) < 2:
        print(
            "Usage: uv run asw_app_sdlc_zte_iso.py <issue-number> [asw-id] [--skip-e2e] [--skip-resolution]"
        )
        print("\n🚀 Zero Touch Execution: Complete SDLC with automatic shipping")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated)")
        print("  5. Document (isolated)")
        print("  6. Ship (approve & merge PR) 🚢")
        print("\n⚠️  WARNING: This will automatically merge to main if all phases pass!")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_asw_app_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Check if issue description contains "full-deploy" keyword
    issue_description = get_issue_description(issue_number)
    enable_full_deploy = detect_full_deploy(issue_description) if issue_description else False

    if enable_full_deploy:
        print(f"🚀 Full-Deploy detected in issue description!")
        print(f"Will build new AMI with Packer and deploy with Terraform after ship phase")

    # Post initial ZTE message
    try:
        base_message = (
            f"{adw_id}_ops: 🚀 **Starting Zero Touch Execution (ZTE)**\n\n"
            "This workflow will automatically:\n"
            "1. ✍️ Plan the implementation\n"
            "2. 🔨 Build the solution\n"
            "3. 🧪 Test the code\n"
            "4. 👀 Review the implementation\n"
            "5. 📚 Generate documentation\n"
            "6. 🚢 **Ship to production** (approve & merge PR)\n"
        )

        if enable_full_deploy:
            base_message += (
                "\n🌟 **Full-Deploy Mode Enabled** 🌟\n"
                "7. 📦 **Build new AMI** with Packer\n"
                "8. ☁️ **Deploy infrastructure** with Terraform\n"
                "9. 🌐 **Update DNS** in Cloudflare\n"
            )

        base_message += "\n⚠️ Code will be automatically merged if all phases pass!"

        make_issue_comment(issue_number, base_message)
    except Exception as e:
        print(f"Warning: Failed to post initial comment: {e}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the ADW ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_plan_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_build_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated test with the ADW ID
    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_test_iso.py"),
        issue_number,
        adw_id,
        "--skip-e2e",  # Always skip E2E tests in SDLC workflows
    ]

    print(f"\n=== ISOLATED TEST PHASE ===")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # For ZTE, we should stop if tests fail
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: ❌ **ZTE Aborted** - Test phase failed\n\n"
                "Automatic shipping cancelled due to test failures.\n"
                "Please fix the tests and run the workflow again.",
            )
        except:
            pass
        sys.exit(1)

    # Run isolated review with the ADW ID
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_review_iso.py"),
        issue_number,
        adw_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")

    print(f"\n=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("Isolated review phase failed")
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: ❌ **ZTE Aborted** - Review phase failed\n\n"
                "Automatic shipping cancelled due to review failures.\n"
                "Please address the review issues and run the workflow again.",
            )
        except:
            pass
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_document_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        # Documentation failure shouldn't block shipping
        print("WARNING: Documentation phase failed but continuing with shipping")

    # Run isolated ship with the ADW ID
    ship_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_ship_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED SHIP PHASE (APPROVE & MERGE) ===")
    print(f"Running: {' '.join(ship_cmd)}")
    ship = subprocess.run(ship_cmd)
    if ship.returncode != 0:
        print("Isolated ship phase failed")
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: ❌ **ZTE Failed** - Ship phase failed\n\n"
                "Could not automatically approve and merge the PR.\n"
                "Please check the ship logs and merge manually if needed.",
            )
        except:
            pass
        sys.exit(1)

    # === FULL-DEPLOY PHASE (if enabled) ===
    ami_id = None
    public_ip = None
    site_urls = []

    if enable_full_deploy:
        print(f"\n=== FULL-DEPLOY PHASE (BUILD AMI + DEPLOY) ===")

        # Validate prerequisites
        validation_errors = []

        # Check if gh CLI is available (required by ipe_build.py and ipe_deploy.py)
        gh_check = subprocess.run(["which", "gh"], capture_output=True)
        if gh_check.returncode != 0:
            validation_errors.append("GitHub CLI (gh) not found - required for triggering workflows")

        # Check if uv is available
        uv_check = subprocess.run(["which", "uv"], capture_output=True)
        if uv_check.returncode != 0:
            validation_errors.append("uv not found - required for running Python scripts")

        # Check if ipe_build.py exists
        if not os.path.exists("ipe/ipe_build.py"):
            validation_errors.append("ipe/ipe_build.py not found")

        # Check if ipe_deploy.py exists
        if not os.path.exists("ipe/ipe_deploy.py"):
            validation_errors.append("ipe/ipe_deploy.py not found")

        if validation_errors:
            error_msg = "Full-Deploy prerequisites not met:\n" + "\n".join(f"- {e}" for e in validation_errors)
            print(error_msg)
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ❌ **Full-Deploy Aborted**\n\n{error_msg}"
                )
            except:
                pass
            sys.exit(1)

        print("✅ Prerequisites validated")

        # Post full-deploy start notification
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: 🌟 **Starting Full-Deploy**\n\n"
                "Step 7/9: Building new AMI with Packer...\n"
                "This may take 10-15 minutes."
            )
        except:
            pass

        # Build AMI with Packer (via GitHub Actions)
        build_cmd = [
            "uv",
            "run",
            "ipe/ipe_build.py",
            "--environment=dev",  # Use dev for ZTE workflows
            f"--ipe-id={adw_id}",
            "--wait",  # Wait for build to complete
            "--timeout=45",  # 45 minutes timeout
            "--output-format=text"
        ]

        print(f"Running: {' '.join(build_cmd)}")

        try:
            build_result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=3000  # 50 minutes (5 minutes buffer over --timeout=45)
            )
        except subprocess.TimeoutExpired:
            error_msg = "AMI build timed out after 50 minutes"
            print(error_msg)
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ⏱️ **Full-Deploy Timeout**\n\n{error_msg}\n"
                    "Check GitHub Actions for workflow status."
                )
            except:
                pass
            sys.exit(1)

        if build_result.returncode != 0:
            error_msg = (
                f"AMI build failed with exit code {build_result.returncode}\n\n"
                "**Error Output:**\n"
                f"```\n{build_result.stderr[:1000]}\n```\n\n"  # Limit to 1000 chars
                "**Suggested Actions:**\n"
                "1. Check GitHub Actions workflow logs\n"
                "2. Verify AWS credentials are configured\n"
                "3. Check Packer template syntax\n"
                "4. Manually run: `uv run ipe/ipe_build.py --environment=dev`"
            )
            print(error_msg)
            print(f"Build stderr: {build_result.stderr}")
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ❌ **Full-Deploy Failed**\n\n"
                    "AMI build failed. Infrastructure deployment aborted.\n"
                    "Please check the GitHub Actions logs for details."
                )
            except:
                pass
            sys.exit(1)

        # Extract AMI ID from output
        # ipe_build.py outputs: "AMI ID: ami-0123456789abcdef0"
        for line in build_result.stdout.split('\n'):
            if 'AMI ID:' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    ami_id = parts[1].strip()
                    break

        if not ami_id:
            error_msg = "Could not extract AMI ID from build output"
            print(error_msg)
            print(f"Build output:\n{build_result.stdout}")
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ❌ **Full-Deploy Failed**\n\n"
                    f"{error_msg}\n"
                    "Please check the build logs."
                )
            except:
                pass
            sys.exit(1)

        print(f"✅ Built AMI: {ami_id}")

        # Post success notification
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: ✅ **AMI Build Complete**\n\n"
                f"Step 7/9: AMI built successfully\n"
                f"AMI ID: `{ami_id}`\n\n"
                "Step 8/9: Deploying infrastructure with Terraform..."
            )
        except:
            pass

        # Deploy infrastructure with Terraform (via GitHub Actions)
        deploy_cmd = [
            "uv",
            "run",
            "ipe/ipe_deploy.py",
            "--mode=deploy-custom-ami",  # Use the AMI we just built
            f"--ami-id={ami_id}",
            "--environment=dev",
            f"--ipe-id={adw_id}",
            "--wait",  # Wait for deployment to complete
            "--timeout=30",  # 30 minutes timeout
            "--output-format=text"
        ]

        print(f"Running: {' '.join(deploy_cmd)}")

        try:
            deploy_result = subprocess.run(
                deploy_cmd,
                capture_output=True,
                text=True,
                timeout=2100  # 35 minutes (5 minutes buffer over --timeout=30)
            )
        except subprocess.TimeoutExpired:
            error_msg = "Infrastructure deployment timed out after 35 minutes"
            print(error_msg)
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ⏱️ **Full-Deploy Timeout**\n\n{error_msg}\n"
                    "AMI build succeeded but Terraform deployment timed out.\n"
                    f"AMI ID: `{ami_id}`\n"
                    "Check GitHub Actions for workflow status."
                )
            except:
                pass
            sys.exit(1)

        if deploy_result.returncode != 0:
            error_msg = (
                f"Infrastructure deployment failed with exit code {deploy_result.returncode}\n\n"
                "**Error Output:**\n"
                f"```\n{deploy_result.stderr[:1000]}\n```\n\n"
                "**Suggested Actions:**\n"
                "1. Check GitHub Actions workflow logs\n"
                "2. Verify Terraform state is not locked\n"
                "3. Check HCP Terraform credentials\n"
                "4. Review Terraform plan for conflicts"
            )
            print(error_msg)
            print(f"Deploy stderr: {deploy_result.stderr}")
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ❌ **Full-Deploy Failed**\n\n"
                    "Terraform deployment failed.\n"
                    "AMI was built successfully but infrastructure deployment failed.\n"
                    f"AMI ID: `{ami_id}`\n\n"
                    "Please check the GitHub Actions logs for details.\n"
                    "You may need to deploy manually or debug Terraform state."
                )
            except:
                pass
            sys.exit(1)

        print("✅ Infrastructure deployed successfully")
        print(f"Deploy output:\n{deploy_result.stdout}")

        # Extract deployment details from output
        for line in deploy_result.stdout.split('\n'):
            if 'Public IP:' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    public_ip = parts[1].strip()
            # ipe_deploy.py includes site URLs in output
            if 'https://{{PROJECT_DOMAIN}}' in line or 'https://www.{{PROJECT_DOMAIN}}' in line:
                import re
                url_match = re.search(r'https://[^\s]+', line)
                if url_match:
                    site_urls.append(url_match.group(0))

        # Post full-deploy success notification
        try:
            success_msg = (
                f"{adw_id}_ops: 🎉 **Full-Deploy Completed Successfully!**\n\n"
                "✅ All phases completed:\n"
                "1. ✅ Plan phase\n"
                "2. ✅ Build phase\n"
                "3. ✅ Test phase\n"
                "4. ✅ Review phase\n"
                "5. ✅ Documentation phase\n"
                "6. ✅ Ship phase (PR merged)\n"
                "7. ✅ AMI build (Packer)\n"
                "8. ✅ Infrastructure deployment (Terraform)\n"
                "9. ✅ DNS update (Cloudflare)\n\n"
                "🚀 **Application is now live!**\n\n"
                f"**Infrastructure Details:**\n"
                f"- AMI ID: `{ami_id}`\n"
            )

            if public_ip:
                success_msg += f"- Public IP: `{public_ip}`\n"

            if site_urls:
                success_msg += "\n**Site URLs:**\n"
                for url in site_urls:
                    success_msg += f"- {url}\n"

            success_msg += (
                "\n**Note:** DNS propagation may take up to 5 minutes.\n\n"
                f"Worktree location: `trees/{adw_id}/`\n"
                f"To clean up: `./scripts/purge_tree.sh {adw_id}`"
            )

            make_issue_comment(issue_number, success_msg)
        except Exception as e:
            print(f"Warning: Failed to post success comment: {e}")

    print(f"\n=== 🎉 ZERO TOUCH EXECUTION COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")
    print(f"✅ Code has been shipped to production!")

    if enable_full_deploy:
        print(f"✅ AMI built: {ami_id}")
        print(f"✅ Infrastructure deployed!")
        if public_ip:
            print(f"✅ Public IP: {public_ip}")
        if site_urls:
            print(f"✅ Site URLs:")
            for url in site_urls:
                print(f"   - {url}")

    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {adw_id}")

    # Only post this simple comment if full-deploy is disabled
    # (full-deploy posts its own comprehensive comment)
    if not enable_full_deploy:
        try:
            make_issue_comment(
                issue_number,
                f"{adw_id}_ops: 🎉 **Zero Touch Execution Complete!**\n\n"
                "✅ Plan phase completed\n"
                "✅ Build phase completed\n"
                "✅ Test phase completed\n"
                "✅ Review phase completed\n"
                "✅ Documentation phase completed\n"
                "✅ Ship phase completed\n\n"
                "🚢 **Code has been automatically shipped to production!**",
            )
        except:
            pass


if __name__ == "__main__":
    main()

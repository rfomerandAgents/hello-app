# Implement Plan

## Run
/prime

IMPORTANT: You must use the Task tool to launch the plan-implementer subagent. Do NOT implement the plan directly.

Launch the plan-implementer subagent with the following prompt:

---

Implement the plan in the following file: $ARGUMENTS

Read the plan file thoroughly, then systematically implement each phase and step in order. Follow all dependencies, verify each step's success criteria, and report your progress.

After implementation, provide:
1. Summary of completed work (concise bullet points)
2. Any deviations from the plan and why
3. Git diff stats showing files changed
4. Verification status of key features
5. Any issues encountered and resolutions

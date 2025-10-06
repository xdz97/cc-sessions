# Code-Review Agent Customization

The code-review agent runs before you commit code. It checks for bugs, security issues, and whether you're following your own patterns.

To make it useful, it needs to know what matters in your specific situation.

## Understanding Your Security Concerns

Let's figure out what security issues actually matter for your software.

**Who uses this software?**

Is it:
- An internal tool just for you or your team?
- A public API or service anyone can access?
- Enterprise software for paying customers?
- Something else?

[Wait for user's response]

---

**After they answer who uses it:**

**Are users running untrusted code or processing untrusted data?**

Think about whether users:
- Upload files or submit data you don't control
- Run code from external sources
- Process content from the internet
- Have any way to inject malicious input

[Wait for user's response]

---

**After they answer about untrusted data:**

**What's the worst case if someone malicious gets access?**

Think about:
- Could they steal data? Whose data?
- Could they break things for other users?
- Could they cost you money?
- Could they access other systems?

[Wait for user's response]

---

## Understanding Your Performance Standards

**How important is performance to you?**

[Wait for user's response]

---

**After they answer:**

**Do you have any existing performance standards for this app?**

Like:
- Response time requirements
- Throughput targets
- SLAs or customer expectations
- Known bottlenecks you're working on

[Wait for user's response]

---

**After they answer:**

**How important is latency?**

Are users waiting for responses in real-time, or is this background processing?

[Wait for user's response]

---

## Creating the Customized Agent

**Instructions after gathering security and performance info:**

Now scan the codebase to identify:
- Tech stack-specific issues to watch for
- Common mistakes in their languages/frameworks

After scanning:

1. Read the package agent: `.claude/agents/code-review.md`
2. Update the agent to include:
   - Threat model section based on who uses it and what data they process
   - Performance profile section based on their standards and requirements
   - Tech stack-specific slop patterns (common LLM mistakes in their languages)

3. Show them the key sections you added and confirm it looks right

---

**After code-review customization:**

Ask: "Want to customize the other agents (logging, context-refinement, service-documentation), or use the defaults?"

[Wait for user's response]

---

**If they want to customize others:**

For each agent they choose:
- Brief explanation of what it does
- Quick customization conversation
- Update the agent file

**If they're good with defaults:**

Run: `python -m sessions.kickstart next`

This will move to the next module.

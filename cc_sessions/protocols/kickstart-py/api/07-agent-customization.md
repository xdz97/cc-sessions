# Agent Customization

cc-sessions has 5 specialized agents that handle heavy operations. Two are worth customizing for your project:

**context-gathering** - Runs when creating/starting tasks to find relevant code patterns
**code-review** - Runs before commits to check for bugs and security issues

The others (logging, context-refinement, service-documentation) work well with defaults.

## Context-Gathering Customization

The agent needs to know what patterns matter in your codebase.

**What patterns does your codebase follow?**

Think about:
- Service structure: Microservices, modules, packages?
- Database patterns: Redis keys, Postgres schemas, ORM usage?
- API conventions: REST endpoints, auth flows, routing?

[Wait for response, have conversational exchange to understand patterns]

---

**After gathering pattern info:**

1. Read `.claude/agents/context-gathering.md`
2. Update it to add:
   - Service structure specifics
   - Database convention patterns
   - API pattern examples from their codebase
3. Show snippet of additions, confirm it looks right

---

## Code-Review Customization

The agent needs to understand your threat model and performance requirements.

### Security Assessment

**Who uses this software?**
- Internal tool?
- Public API/service?
- Enterprise software?

[Wait for response]

**Are users processing untrusted data?**
- Uploading files or submitting data you don't control?
- Running code from external sources?
- Processing content from internet?

[Wait for response]

**What's the worst case if someone malicious gets access?**
- Steal data? Whose data?
- Break things for other users?
- Cost you money?
- Access other systems?

[Wait for response]

### Performance Assessment

**How important is performance?**

[Wait for response]

**Do you have performance standards?**
- Response time requirements?
- Throughput targets?
- SLAs or customer expectations?

[Wait for response]

**How important is latency?**

Are users waiting for responses in real-time, or background processing?

[Wait for response]

---

**After gathering security and performance info:**

Scan codebase to identify tech stack-specific issues.

1. Read `.claude/agents/code-review.md`
2. Update it to add:
   - Threat model section (who uses it, data they process)
   - Performance profile section (standards, requirements)
   - Tech stack-specific patterns to watch for
3. Show key sections, confirm it looks right

---

**After code-review customization:**

Ask: "Want to customize the other agents (logging, context-refinement, service-documentation), or use defaults?"

[Wait for response]

If yes: Briefly customize each one they choose
If no: Run `python -m sessions.kickstart next`

# MCP & Agentic AI Architecture Research - Executive Summary

**Created:** 2026-04-28  
**For:** Claude Bootcamp Hackathon - Intake/Routing System  

---

## What Was Researched

This comprehensive research document covers 10 core topics essential for building agentic intake/routing systems:

1. **Model Context Protocol (MCP)** - The "USB-C for AI"
2. **MCP Server Implementation** - Python FastMCP & TypeScript SDK
3. **Claude Agent SDK** - Programmatic agent development
4. **Agentic Architecture Patterns** - Six core patterns + routing specialization
5. **Intake/Routing System Design** - Full system architecture
6. **Prompt Injection Defense** - 4 defense strategies + best practices
7. **Evaluation Harnesses** - Testing, metrics (pass@k vs pass^k), grading
8. **Structured Outputs** - JSON Schema validation with retry loops
9. **Human-in-the-Loop** - Approval gates, confidence routing, escalation
10. **Tool Design** - 7 key principles for agent-friendly APIs

---

## Key Findings (TL;DR)

### MCP Overview
- **Latest Spec:** November 2025 (2025-11-25)
- **Three Primitives:** Tools (actions), Resources (context), Prompts (templates)
- **Key Innovation:** Tasks primitive for async long-running operations
- **Security:** Built-in trust & consent framework

### Implementation Options
```
Python: FastMCP (@mcp.tool decorators) → fastest iteration
TypeScript: Official SDK (Zod schemas) → more control
```

### Agentic Patterns for Routing
```
Orchestrator-Workers Pattern (Recommended)
├── Orchestrator: Classifies, routes, synthesizes
├── Worker 1: Classifier (multi-model voting)
├── Worker 2: Impact Assessor
├── Worker 3: Router (confidence-based)
└── Worker 4: Escalation Manager
```

### Intake/Routing Core Flow
```
Request → Parse → Classify (with confidence) → Assess Impact
    → Check Escalation Rules → Route Decision → Execute → Audit Trail
```

### Confidence Routing (Key Pattern)
```
Confidence >= 0.85 → Automate
Confidence >= 0.60 → Specialist Agent
Confidence < 0.60 → Human Review

IF Critical Impact → Always Human
```

### Prompt Injection Threat (2026)
- **Ranking:** OWASP #1 LLM vulnerability (3rd year)
- **Prevalence:** 73% of production deployments affected
- **Cost:** $2.3 billion globally in 2025
- **Types:** Direct (user input) + Indirect (data sources)
- **Best Defense:** PromptArmor (< 1% false rate at ICLR 2026)

### Defense Strategies (in order of effectiveness)
1. **PromptArmor** - Dedicated preprocessor LLM (< 1% FP/FN)
2. **Two-Stage Classification** - Fast + deliberation (F1: 0.972)
3. **PromptGuard** - Four-layer defense (67% reduction)
4. **Architectural Controls** - Trust boundaries, least privilege, red teaming

### Evaluation Metrics (Critical!)
```
For ONE GOOD SOLUTION needed:
  pass@k = 1 - (1 - p)^k (increases with retries) ✓ coding

For ALL REQUESTS SUCCESS (customer-facing):
  pass^k = p^k (decreases with retries) ✓ intake/routing
```

**Key Insight:** Use **pass^k** for your intake/routing system. If individual success rate is 95%, pass^3 drops to 86% — one failure affects customer trust.

### Tool Design Principles
1. Fewer tools (< 20) with better parameters
2. Clear namespacing (service_resource pattern)
3. Concise descriptions (60-200 chars with examples)
4. Error messages that guide solutions
5. Return semantic info, not just IDs
6. Rate limiting with clear feedback
7. Deterministic results when possible

### Human-in-the-Loop Patterns
```
Approval Gate → Confidence Routing → Smart Escalation → Audit Trail
  (1-2 days)     (then iterate)      (multi-level)    (compliance)
```

---

## Code Examples Included

### 1. **Complete Python MCP Server** (FastMCP)
- `parse_intake_request()` - Extract structured info
- `classify_request()` - Multi-classifier voting
- `assess_impact()` - Business impact scoring
- `determine_routing()` - Route based on confidence
- `create_audit_entry()` - Compliance logging
- Resources for rules and audit logs
- Prompts for guided decision-making

### 2. **Claude Agent SDK Integration**
- Agent initialization with MCP servers
- Lifecycle hooks (pre/post tool use)
- Session management
- Batch processing with subagents
- End-to-end intake workflow

### 3. **Evaluation Harness**
- Test case definition
- Code-based grading (deterministic)
- Model-based grading (LLM rubrics)
- pass@k and pass^k calculation
- Aggregate results

---

## Architecture Diagram (Intake/Routing)

```
Incoming Request
    ↓
[Intake Agent] → Parse content, extract entities
    ↓
[Classifier Agent] → Category + confidence (multi-model voting)
    ↓
[Impact Assessor] → Business impact level (critical/high/medium/low)
    ↓
[Escalation Engine]
    ├─ If Critical Impact → Escalate
    ├─ If Low Confidence + High Impact → Escalate
    ├─ If High Confidence + Low Impact → Automate
    └─ Otherwise → Route to specialist
    ↓
[Execution]
    ├─ Automation (auto-process)
    ├─ Specialist Agent (focused handling)
    ├─ Human Review (escalation queue)
    └─ Executive Review (critical)
    ↓
[Audit Trail] → Complete decision log for compliance
```

---

## Critical Statistics (2026)

| Metric | Value |
|--------|-------|
| Prompt Injection Prevalence | 73% of production |
| Attack Success Rate | 85%+ with adaptive strategies |
| Financial Losses (2025) | $2.3 billion globally |
| PromptArmor False Positive Rate | < 1% |
| Two-Stage Detector F1 Score | 0.972 |
| MCP Downloads | 1M+ per day |
| FastMCP Market Share | 70% of MCP servers |
| Claude Managed Agents Status | Public beta (Apr 2026) |

---

## Recommended Reading Order

**For Implementation (Shortest Path):**
1. MCP Architecture & Specification (page 2)
2. Building MCP Servers (page 3)
3. Python FastMCP Implementation (page 4)
4. Claude Agent SDK (page 6)
5. Intake/Routing System Design (page 9)
6. Code Examples (page 13)

**For Comprehensive Understanding:**
1. Read above order first
2. Then: Agentic Architecture Patterns (page 8)
3. Then: Tool Design Best Practices (page 12)
4. Then: Evaluation Harnesses (page 11)
5. Then: Human-in-the-Loop Patterns (page 10)
6. Finally: Prompt Injection Defense (page 7)

**For Security-First Approach:**
1. Prompt Injection Defense Strategies (page 7)
2. Tool Design Best Practices (page 12)
3. Human-in-the-Loop Patterns (page 10)
4. Then follow comprehensive order above

---

## Quick Start Checklist for Hackathon

- [ ] Read MCP Overview & Specification (2 hours)
- [ ] Set up Python FastMCP locally (30 mins)
- [ ] Run MCP server example (30 mins)
- [ ] Create Agent SDK integration (1 hour)
- [ ] Implement classification with confidence voting (2 hours)
- [ ] Add escalation rules engine (1 hour)
- [ ] Build evaluation harness with test cases (2 hours)
- [ ] Implement prompt injection defense (1 hour)
- [ ] Add human-in-the-loop approval gate (1 hour)
- [ ] Create audit trail logging (1 hour)
- [ ] Test end-to-end workflow (1 hour)
- [ ] Performance optimization & tuning (as time allows)

**Total Time:** ~14 hours for solid prototype

---

## Key Insights & Lessons

### 1. Confidence is Everything
Multi-model voting gives you reliable confidence scores. Don't skip this.

### 2. Escalation Rules are Simple
```python
if confidence < 0.6 and impact == "high":
    escalate_to_human()
elif confidence >= 0.85 and impact <= "medium":
    automate()
else:
    route_to_specialist()
```

### 3. Defense First, Not Retrofit
Implement prompt injection defense from day one. It's cheaper than remediation.

### 4. Audit Everything
Complete audit trails are mandatory, not optional. Required for compliance.

### 5. Test on Edge Cases
Adversarial eval sets catch failures before production. Build them early.

### 6. Metrics Matter
Use **pass^k for production reliability**, not pass@k. The math is different.

### 7. Humans Stay in Loop
Even 99% accurate systems escalate edge cases. Design for human review.

---

## Research Sources (All Linked in Main Document)

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [Claude Agent SDK Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Anthropic Research Papers](https://www.anthropic.com/research)
- [OWASP LLM Security](https://genai.owasp.org/)
- [FastMCP Framework](https://gofastmcp.com/)
- [Google Cloud Architecture Patterns](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)

---

## Contact & Support

For questions on:
- **MCP Implementation** → Consult modelcontextprotocol.io
- **Agent SDK** → Check platform.claude.com/docs
- **Architectural Patterns** → See Anthropic research papers
- **Prompt Injection Defense** → Review OWASP Gen AI Security Project

Document is completely self-contained with code examples. You can implement directly.

---

**Last Updated:** 2026-04-28  
**Status:** Complete & Ready for Hackathon  
**Next Step:** Open `MCP_AGENT_ARCHITECTURE_RESEARCH.md` and start building!


# Agent Customization Guide for Kickstart

This guide helps you customize the cc-sessions agents during the kickstart protocol to match your specific project needs.

## Overview

The cc-sessions package includes five core agents that are designed to work well out-of-the-box for most projects. However, you can customize them during kickstart to better match your specific:
- Technology stack
- Architectural patterns  
- Team conventions
- Domain terminology

## Core Agents to Customize

### 1. context-gathering
**Purpose**: Creates comprehensive context manifests for tasks

**Customization Points**:
- **Terminology**: Replace generic "component/module/service" with your specific terms (e.g., "microservice", "lambda", "actor")
- **Architecture Patterns**: Add your specific patterns (e.g., "Event Sourcing", "CQRS", "Clean Architecture")
- **Tech Stack**: Specify your ORMs, caching systems, message queues
- **Skip Patterns**: Add file patterns to skip (e.g., "Skip generated files", "Skip vendor directories")
- **Domain-Specific Sections**: Add sections for your domain (e.g., "Payment Processing", "ML Pipeline", "Game State")

**Example Customization**:
```markdown
# In your local .claude/agents/context-gathering.md

### Step 2: Research Everything (SPARE NO TOKENS)
Hunt down:
- Every Lambda function and Step Function that will be touched
- DynamoDB tables and their GSIs  
- S3 buckets and their event triggers
- EventBridge rules and targets
- API Gateway endpoints and authorizers
- NOTE: Skip CDK output files and node_modules
```

### 2. logging
**Purpose**: Maintains clean work logs for tasks

**Customization Points**:
- **Transcript Locations**: Specify where your project stores transcripts
- **Work Log Format**: Adjust categories to match your workflow (e.g., add "Tests Written", "Migrations Created")
- **Date Format**: Match your team's preferred date format
- **Custom Sections**: Add project-specific sections (e.g., "Performance Impact", "Security Review")

**Example Customization**:
```markdown
### Work Log Format

## Work Log

### [Sprint X - Date]

#### User Stories Completed
- [JIRA-123] Implemented user authentication

#### Technical Debt Addressed
- Refactored payment processing module

#### Tests Added
- Unit tests for auth service
- Integration tests for payment flow

#### Database Changes
- Added indexes to user table
- Created audit log table
```

### 3. context-refinement
**Purpose**: Updates context when discoveries are made during implementation

**Customization Points**:
- **Discovery Categories**: Add project-specific discovery types (e.g., "Compliance Requirements", "Performance Bottlenecks")
- **Worth Documenting Threshold**: Adjust based on your team's documentation standards
- **Update Format**: Match your documentation style

**Example Customization**:
```markdown
**YES - Update for these:**
- Undocumented Kubernetes config requirements
- Terraform state dependencies not originally known
- Rate limits discovered on third-party APIs
- GDPR compliance requirements affecting data flow
- Undocumented feature flags controlling behavior
```

### 4. service-documentation
**Purpose**: Maintains CLAUDE.md documentation files

**Customization Points**:
- **Documentation Structure**: Adjust sections based on your architecture
- **File Patterns**: Specify your project's file organization
- **Integration Points Format**: Match how you document APIs
- **Special Sections**: Add domain-specific sections

**Example Customization**:
```markdown
## GraphQL Schema
- Type definitions: `schema/types.graphql`
- Resolvers: `src/resolvers/`
- Subscriptions: `src/subscriptions/`

## Event Streams
### Publishes
- `user.created` → UserEventStream
- `order.placed` → OrderEventStream

### Subscribes  
- `payment.processed` ← PaymentService
- `inventory.updated` ← InventoryService

## Feature Flags
- `ENABLE_NEW_CHECKOUT` - New checkout flow
- `ENABLE_RECOMMENDATIONS` - ML recommendations
```

### 5. code-review
**Purpose**: Reviews code for quality and security issues

**Customization Points**:
- **Review Focus**: Add project-specific concerns (e.g., "PCI compliance", "WCAG accessibility")
- **Severity Levels**: Adjust based on your deployment requirements
- **Pattern Library**: Reference your team's accepted patterns
- **Exclude Patterns**: Skip reviewing generated or vendored code

**Example Customization**:
```markdown
#### 🔴 Critical (Blocks Deployment)
**Compliance Issues:**
- PII exposed in logs
- Credit card data not tokenized
- HIPAA violations in data handling
- Missing audit trail for sensitive operations

**Infrastructure Issues:**
- Hardcoded AWS credentials
- Missing CloudWatch alarms
- Unencrypted data at rest
- Public S3 buckets with sensitive data
```

## How to Customize During Kickstart

### Step 1: Identify Your Patterns
Before customizing agents, identify:
- Your repository structure (mono-repo, microservices, etc.)
- Your tech stack (languages, frameworks, databases)
- Your architectural patterns (MVC, hexagonal, etc.)
- Your team conventions (naming, documentation style)
- Your domain terminology

### Step 2: Create Local Overrides
During kickstart, create customized versions in `.claude/agents/`:

```bash
# The kickstart protocol will help you create these
.claude/agents/
├── context-gathering.md  # Your customized version
├── logging.md            # Your customized version
└── ...                   # Only customize what you need
```

### Step 3: Test Your Customizations
After customizing:
1. Create a test task
2. Run the context-gathering agent
3. Verify it captures your specific patterns
4. Adjust as needed

## Customization Best Practices

### DO:
- ✅ Keep the core structure and sections
- ✅ Add project-specific patterns and terminology
- ✅ Include examples from your actual codebase
- ✅ Specify paths and conventions used in your project
- ✅ Add domain-specific requirements

### DON'T:
- ❌ Remove core functionality
- ❌ Change the input/output format
- ❌ Add project secrets or credentials
- ❌ Over-specialize to the point where agents break on edge cases
- ❌ Remove safety checks or restrictions

## Common Customization Patterns

### For Microservices Architecture
- Emphasize service boundaries and contracts
- Add service discovery patterns
- Include deployment configurations
- Document inter-service communication

### For Monolithic Applications  
- Focus on module boundaries
- Emphasize layered architecture
- Document shared libraries
- Include build configurations

### For Serverless Architecture
- Focus on function triggers and events
- Document cold start considerations
- Include IAM roles and permissions
- Emphasize event-driven patterns

### For Frontend Applications
- Include component hierarchies
- Document state management
- Add styling conventions
- Include build and bundling setup

## Maintenance

Customized agents should be:
- Kept in version control
- Updated when patterns change
- Reviewed during retrospectives
- Shared across the team

## When NOT to Customize

The default agents work well for:
- Standard web applications
- Common architectural patterns
- Well-documented codebases
- Small to medium projects

Only customize if you have:
- Specific domain requirements
- Unusual architectural patterns
- Strict compliance needs
- Large, complex systems

## Getting Help

If you're unsure about customization:
1. Start with the defaults
2. Note what's missing during use
3. Customize incrementally
4. Share customizations with the community

Remember: The goal is to make agents more helpful, not more complex. When in doubt, keep it simple and let the default agents do their job.
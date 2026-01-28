# fal.ai Best Practices - Brainstorm Document

**Date:** 2026-01-28
**Status:** Documented
**Type:** Reference Documentation

---

## What We're Building

A comprehensive best practices guide for fal.ai integration, structured as a decision-making reference with minimal code examples. This documentation will help evaluate and implement fal.ai services in the future.

**Scope:**
- API integration patterns
- Model selection and configuration
- Error handling and reliability strategies
- Performance optimization techniques

**Out of scope:**
- Full implementation in fal-skill (this is reference documentation)
- Migration plan from existing services
- Cost analysis

---

## Why This Approach

**Selected: Decision Matrix + Minimal Examples**

**Rationale:**
- Faster to create and maintain than full implementation examples
- Focuses on strategic decisions (when/why) over implementation details (how)
- Less likely to become outdated as fal.ai evolves
- Complements existing repo patterns without prescribing specific code structure
- Better for quick reference and evaluation

**Trade-offs accepted:**
- Less immediately actionable than full code examples
- Will require implementation work when building fal-skill
- May need supplementary research during actual development

---

## Key Decisions

### 1. Documentation Structure

**Decision:** Organize by decision domains, not architectural layers

Structure:
```
docs/
└── reference/
    └── fal-ai-best-practices.md
        ├── Model Selection Matrix
        ├── Configuration Decisions
        ├── Error Handling Strategies
        ├── Performance Patterns
        └── Quick Reference Tables
```

**Why:** Optimized for looking up answers to specific questions rather than linear reading

---

### 2. Content Coverage

| Area | Coverage Level | Example Format |
|------|---------------|----------------|
| **API Integration** | Decision trees | "When to use sync vs async" with 3-line code snippet |
| **Model Selection** | Comparison tables | Flux Pro vs Dev matrix with use cases |
| **Error Handling** | Strategy catalog | Retry patterns with pseudocode |
| **Performance** | Pattern library | Caching strategies with minimal implementation notes |

**Principle:** Each section answers "When should I...?" and "Why would I...?" questions

---

### 3. Code Example Style

**Guidelines:**
- Maximum 10 lines per code snippet
- Pseudocode acceptable for complex patterns
- Reference existing repo patterns where applicable
- Link to official fal.ai docs for complete implementations

**Example style:**
```python
# Decision: Use async for bulk operations
async def generate_batch(prompts: list[str]):
    tasks = [fal_client.submit(model, {"prompt": p}) for p in prompts]
    return await asyncio.gather(*tasks)
```

---

### 4. Decision Matrices Format

Use this structure for each major decision:

```markdown
## When to Use [Option A] vs [Option B]

**Choose Option A if:**
- Condition 1
- Condition 2

**Choose Option B if:**
- Condition 3
- Condition 4

**Example scenario:** [One sentence + 3-line code]
```

---

## Key Architectural Patterns to Document

Based on research into existing repo patterns:

### 1. API Integration Patterns

**Decisions to cover:**
- Sync vs async client usage
- Authentication: API key in env vs explicit configuration
- Request/response validation
- Client factory pattern vs singleton

**Reference from repo:**
- Pattern: Factory pattern from `vibe-image-3/flashcard-generator/util/image_generator.py:create_image_client()`
- Pattern: Async threading bridge from same file

---

### 2. Model Selection Matrix

**Flux Pro vs Flux Dev comparison:**

| Factor | Flux Pro | Flux Dev |
|--------|----------|----------|
| Quality | Highest | High |
| Speed | Slower (~60s) | Faster (~30s) |
| Cost | Higher | Lower |
| Use case | Production, final assets | Iteration, development |

**Decision tree:**
- Need highest quality? → Flux Pro
- Rapid iteration? → Flux Dev
- Budget constrained? → Flux Dev
- Commercial use? → Check license, likely Flux Pro

---

### 3. Error Handling Strategies

**Decisions to cover:**

| Error Type | Strategy | Implementation Complexity |
|------------|----------|--------------------------|
| Rate limiting (429) | Exponential backoff + retry | Medium |
| Auth errors (401) | Fail fast, log clearly | Low |
| Timeout | Retry with increased timeout | Low |
| Invalid input (400) | Validate before request | Medium |
| Server errors (5xx) | Limited retry + fallback | High |

**Reference from repo:**
- Pattern: Exception handling from `vibe-video-2/src/avatar.py:_make_cv_call()` (non-standard API response handling)

---

### 4. Performance Optimization

**Patterns to document:**

**Caching Strategy Decision:**
```
Question: Should I cache this result?
├─ Is it expensive? (>5s generation)
│  ├─ Yes: Cache it
│  └─ No: Skip caching
└─ Does it change frequently?
   ├─ No: Cache it
   └─ Yes: Cache with short TTL or skip
```

**Concurrency Pattern:**
```python
# Decision: Batch requests for multiple images
# Use when: >3 images needed, can wait for all
async def batch_generate(prompts: list[str], max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)
    async def generate_with_limit(prompt):
        async with semaphore:
            return await fal_client.submit(...)
    return await asyncio.gather(*[generate_with_limit(p) for p in prompts])
```

**Reference from repo:**
- Pattern: File-based caching from `flashcard-generator/util/image_generator.py:get_scene_cache_path()`
- Pattern: Async/await with threading from same file

---

### 5. Configuration Management

**Decision: Where to store configuration?**

| Approach | When to Use | Example |
|----------|-------------|---------|
| Environment variables | API keys, secrets | `FAL_KEY=sk-...` |
| Config file | Model IDs, defaults | `config.py` with `FAL_MODELS = {...}` |
| Function parameters | Per-request overrides | `generate(model="flux-pro")` |
| Class properties | Client-level settings | `FalClient(timeout=30)` |

**Reference from repo:**
- Pattern: Centralized config from `flashcard-generator/util/model_config.py`
- Pattern: Env loading from `vibe-video-2/.env` structure

---

## Documentation Sections

### Minimal document structure:

```markdown
# fal.ai Best Practices Reference

## Quick Decision Trees
- [Choose between Flux Pro and Flux Dev]
- [Decide sync vs async implementation]
- [Select error handling strategy]
- [Pick caching approach]

## Model Selection Matrix
[Table format with use cases]

## API Integration Patterns
### Pattern: Basic Client Setup
### Pattern: Async Batch Processing
### Pattern: Error Handling

## Performance Optimization
### Caching Strategies
### Concurrent Requests
### Resource Management

## Common Scenarios
### Scenario 1: Single image generation
### Scenario 2: Bulk processing
### Scenario 3: Real-time generation

## Troubleshooting Guide
[Common errors + solutions table]

## External Resources
- Official fal.ai docs
- SDK references
- Community patterns
```

---

## Open Questions

1. **Documentation location:** Should this live in `fal-skill/docs/reference/` or `docs/reference/` at repo root?
   - **Lean toward:** `fal-skill/docs/reference/` to keep it self-contained

2. **Integration with existing services:** Should we include comparison with Gemini/Volcengine patterns?
   - **Lean toward:** Brief comparison section, not full analysis

3. **Update frequency:** How often should this be reviewed?
   - **Suggest:** Quarterly review or when considering fal.ai implementation

4. **Code examples source:** Pull from fal.ai official docs or create synthetic examples?
   - **Lean toward:** Mix of official + synthetic aligned with repo patterns

---

## Implementation Notes

### When creating the reference doc:

1. **Research phase:**
   - Review fal.ai official documentation
   - Examine Python SDK source code
   - Check community best practices
   - Identify decision points

2. **Writing phase:**
   - Start with decision trees
   - Add comparison matrices
   - Write minimal code snippets
   - Create troubleshooting table

3. **Validation phase:**
   - Cross-check with repo patterns
   - Verify code snippets are accurate
   - Ensure all decision trees are complete

### Estimated sections: 6-8
### Estimated length: 800-1200 words
### Code snippets: 10-15 minimal examples

---

## Success Criteria

Documentation is successful if it enables:
- **Quick decisions:** Can answer "Should I use X?" in <2 minutes
- **Pattern lookup:** Can find relevant pattern without reading entire doc
- **Implementation start:** Provides enough direction to begin coding
- **Comparison:** Can evaluate fal.ai vs existing services

**Metrics:**
- All 4 focus areas covered (API integration, model selection, error handling, performance)
- Each decision point has clear criteria
- Code examples are <10 lines each
- Document is <1500 words total

---

## Next Steps

1. **Create reference document:** `fal-skill/docs/reference/fal-ai-best-practices.md`
2. **Research fal.ai specifics:** Review official docs for current patterns
3. **Write decision trees:** Start with model selection and API patterns
4. **Add code examples:** Minimal snippets aligned with repo style
5. **Create comparison table:** Brief comparison with Gemini/Volcengine

**Estimated effort:** 2-3 hours of focused work

---

## References

**Existing repo patterns analyzed:**
- `vibe-image-3/flashcard-generator/util/model_config.py` - Configuration pattern
- `vibe-image-3/flashcard-generator/util/image_generator.py` - Client factory, async patterns
- `vibe-video-2/src/avatar.py` - Error handling for non-standard APIs
- `vibe-video-2/.env` - Environment configuration
- `~/.claude/skills/*/SKILL.md` - Skill documentation structure

**External resources:**
- fal.ai official documentation: https://fal.ai/docs
- fal-client Python SDK: https://github.com/fal-ai/fal-client-python
- Flux model documentation: https://fal.ai/models/flux

---
name: team-coordination
description: Multi-agent team coordination, task delegation, collaborative problem-solving, and team communication
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["coordination", "teamwork", "delegation", "collaboration"]
---

# Team Coordination Skill

Use this skill when coordinating multi-agent teams, delegating tasks, or managing collaborative workflows.

## When to Use

- Coordinating specialist team members
- Delegating tasks to appropriate agents
- Synthesizing multiple agent outputs
- Managing complex multi-step workflows
- Collaborative problem-solving

## Coordination Framework

### 1. Task Analysis

Break down the request:

- What is the primary goal?
- What expertise is needed?
- Are subtasks independent or dependent?
- What is the desired output format?

### 2. Member Selection

Select appropriate team members based on:

- Expertise required
- Task complexity
- Member availability
- Coordination mode

### 3. Delegation Strategy

For complex requests, delegate:

- Independent subtasks to relevant specialists
- Complex analysis to expert agents
- Synthesis to coordinator role

### 4. Synthesis

Integrate member contributions:

- Consolidate findings
- Resolve conflicts
- Identify consensus
- Highlight discrepancies

## Coordination Modes

### Sequential Processing

- Each member processes in order
- Output feeds into next member
- Use for dependent tasks

### Parallel Processing

- Multiple members work simultaneously
- Results synthesized afterward
- Use for independent assessments

### Delegate on Complexity

- Simple: Handle directly
- Complex: Delegate to specialist
- Multi-faceted: Assemble team

## Communication Guidelines

### Clear Delegation

- Specify what you need from each member
- Set expectations for output format
- Provide relevant context

### Synthesis

- Summarize key findings from each member
- Resolve conflicting recommendations
- Present unified conclusion

### Feedback

- Acknowledge member contributions
- Flag areas of uncertainty
- Suggest follow-up if needed

## Output Structure

```
Team Analysis:
Task: [original request]

Member Contributions:
- [Specialist 1]: [findings]
- [Specialist 2]: [findings]

Synthesis:
[Unified analysis and conclusions]

Recommendations:
[Combined recommendations]

Next Steps:
[Follow-up actions if needed]
```

## Best Practices

- Match task to specialist expertise
- Provide clear, focused requests
- Allow appropriate processing time
- Synthesize don't just concatenate
- Acknowledge uncertainty
- Flag urgent findings
- Maintain coherence in final output

# claw-platform

claw platform - Agent/Skill management platform with Vue 3 + TypeScript frontend and FastAPI Python backend.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa
- Code review/diff check → invoke /review
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture decisions → invoke /plan-eng-review
- Design system/plan review → invoke /plan-design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore

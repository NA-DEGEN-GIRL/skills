# Skill Behavior Scenarios

`scenarios.json` is a small forward-testing contract for high-risk routing and safety behavior. It is not an automated claim that an LLM will comply: `make all` validates scenario registration and structure, while maintainers should run selected cases in fresh agent threads after substantive SKILL.md changes.

Forward tests should give the agent the named skill and raw request/setup only. Do not leak the `expected` or `forbidden` assertions into the test prompt. Review the resulting chat, files, commands, and tool trace against those assertions.

Add or update a case when changing a trigger, approval boundary, file-write protocol, runner contract, handoff schema, or runtime delegation rule.

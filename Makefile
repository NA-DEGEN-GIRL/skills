.PHONY: all validate syntax-check test sync-check

VALIDATOR ?= $(HOME)/.codex/skills/.system/skill-creator/scripts/quick_validate.py
PYTHON ?= python3
ENV := PYTHONDONTWRITEBYTECODE=1

all: validate syntax-check test sync-check

validate:
	@if [ -f "$(VALIDATOR)" ]; then \
		$(ENV) $(PYTHON) $(VALIDATOR) ./codex-handoff; \
		$(ENV) $(PYTHON) $(VALIDATOR) ./claude-handoff; \
	else \
		echo "WARNING: validator not found at $(VALIDATOR); skipping skill schema validation"; \
	fi

syntax-check:
	$(ENV) $(PYTHON) ./scripts/syntax_check.py "codex-handoff/scripts/*.py" "claude-handoff/scripts/*.py" "scripts/*.py"

test:
	$(ENV) $(PYTHON) ./codex-handoff/scripts/test_handoff_snapshot.py
	$(ENV) $(PYTHON) ./claude-handoff/scripts/test_handoff_snapshot.py
	$(ENV) $(PYTHON) ./codex-handoff/scripts/test_prune_backups.py
	$(ENV) $(PYTHON) ./claude-handoff/scripts/test_prune_backups.py
	$(ENV) $(PYTHON) ./codex-handoff/scripts/test_apply_marker_block.py
	$(ENV) $(PYTHON) ./claude-handoff/scripts/test_apply_marker_block.py
	$(ENV) $(PYTHON) ./codex-handoff/scripts/test_validate_snapshot.py
	$(ENV) $(PYTHON) ./claude-handoff/scripts/test_validate_snapshot.py

sync-check:
	$(ENV) $(PYTHON) ./scripts/check_handoff_sync.py

.PHONY: all validate syntax-check test sync-check

LOCAL_VALIDATOR ?= ./scripts/validate_skill.py
EXTERNAL_VALIDATOR ?= $(HOME)/.codex/skills/.system/skill-creator/scripts/quick_validate.py
PYTHON ?= python3
ENV := PYTHONDONTWRITEBYTECODE=1

all: validate syntax-check test sync-check

validate:
	$(ENV) $(PYTHON) $(LOCAL_VALIDATOR) ./codex-handoff ./claude-handoff
	@if [ -f "$(EXTERNAL_VALIDATOR)" ]; then \
		$(ENV) $(PYTHON) $(EXTERNAL_VALIDATOR) ./codex-handoff; \
		$(ENV) $(PYTHON) $(EXTERNAL_VALIDATOR) ./claude-handoff; \
	else \
		echo "INFO: external validator not found at $(EXTERNAL_VALIDATOR); local validator already ran"; \
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

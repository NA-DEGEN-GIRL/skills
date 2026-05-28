.PHONY: all validate syntax-check test sync-check

LOCAL_VALIDATOR ?= ./scripts/validate_skill.py
EXTERNAL_VALIDATOR ?= $(HOME)/.codex/skills/.system/skill-creator/scripts/quick_validate.py
PYTHON ?= python3
ENV := PYTHONDONTWRITEBYTECODE=1
SKILL_DIRS := $(shell find skills -mindepth 3 -maxdepth 4 -name SKILL.md -exec dirname {} \; | sort)
# A skill package is any directory under skills/ that contains SKILL.md.
# Family-specific maintenance checks live under skills/<family>/scripts/check_*_sync.py.
PY_FILES := $(shell find skills scripts -name '*.py' -type f | sort)
TEST_FILES := $(shell find skills -path '*/scripts/test_*.py' -type f | sort)
SYNC_CHECKS := $(shell find skills -path '*/scripts/check_*_sync.py' -type f | sort)

all: validate syntax-check test sync-check

validate:
	$(ENV) $(PYTHON) $(LOCAL_VALIDATOR) $(SKILL_DIRS)
	@if [ -f "$(EXTERNAL_VALIDATOR)" ]; then \
		for skill_dir in $(SKILL_DIRS); do \
			$(ENV) $(PYTHON) $(EXTERNAL_VALIDATOR) $$skill_dir || exit 1; \
		done; \
	else \
		echo "INFO: external validator not found at $(EXTERNAL_VALIDATOR); local validator already ran"; \
	fi

syntax-check:
	$(ENV) $(PYTHON) ./scripts/syntax_check.py $(PY_FILES)

test:
	@for test_file in $(TEST_FILES); do \
		echo "$(ENV) $(PYTHON) $$test_file"; \
		$(ENV) $(PYTHON) $$test_file || exit 1; \
	done

sync-check:
	@if [ -z "$(SYNC_CHECKS)" ]; then \
		echo "INFO: no family sync checks found"; \
	else \
		for check in $(SYNC_CHECKS); do \
			echo "$(ENV) $(PYTHON) $$check"; \
			$(ENV) $(PYTHON) $$check || exit 1; \
		done; \
	fi

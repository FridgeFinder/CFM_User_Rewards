.PHONY: build invoke invoke-new-only test test-cov lint fmt clean

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
STACK_NAME   ?= user-rewards-dev
REGION       ?= us-east-1
ENV          ?= dev
FUNCTION     ?= UserRewardsConsumerFunction

# ──────────────────────────────────────────────────────────────────────────────
# SAM
# ──────────────────────────────────────────────────────────────────────────────

## Build the SAM application (resolves dependencies into .aws-sam/)
build:
	sam build --use-container

## Deploy to AWS (guided first-run; subsequent runs use samconfig.toml)
deploy:
	sam deploy \
		--stack-name $(STACK_NAME) \
		--region $(REGION) \
		--parameter-overrides Environment=$(ENV) \
		--capabilities CAPABILITY_IAM \
		--resolve-s3

# ──────────────────────────────────────────────────────────────────────────────
# Local invoke (requires Docker + AWS SAM CLI)
# Env vars map to real table names; use local DynamoDB or mock for dev.
# ──────────────────────────────────────────────────────────────────────────────

## Invoke function locally with a FridgeReportUpdated event (both reports present)
invoke-fridge-report-updated:
	sam local invoke $(FUNCTION) \
		--event events/fridge_report_updated.json \
		--parameter-overrides ParameterKey=DeploymentTarget,ParameterValue=local ParameterKey=Stage,ParameterValue=dev \
		--docker-network cfm-network

## Invoke function locally with a FridgeReportUpdated event (no previous report)
invoke-fridge-report-updated-new-only:
	sam local invoke $(FUNCTION) \
		--event events/fridge_report_updated_new_only.json \
		--parameter-overrides ParameterKey=DeploymentTarget,ParameterValue=local ParameterKey=Stage,ParameterValue=dev \
		--docker-network cfm-network

# ──────────────────────────────────────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────────────────────────────────────

## Install all Python dependencies (runtime + dev)
install:
	pip install -r requirements.txt

## Run full unit-test suite
test:
	PYTHONPATH=functions/fridge_report_consumer pytest tests/ -v

## Run tests with HTML coverage report
test-cov:
	PYTHONPATH=functions/fridge_report_consumer pytest tests/ -v \
		--cov=functions/fridge_report_consumer \
		--cov-report=term-missing \
		--cov-report=html:htmlcov

# ──────────────────────────────────────────────────────────────────────────────
# Linting / Formatting
# ──────────────────────────────────────────────────────────────────────────────

## Run Ruff linter (pip install ruff)
lint:
	ruff check functions/ tests/

## Run Black formatter (pip install black)
fmt:
	black functions/ tests/

# ──────────────────────────────────────────────────────────────────────────────
# Housekeeping
# ──────────────────────────────────────────────────────────────────────────────

## Remove build artefacts
clean:
	rm -rf .aws-sam htmlcov .pytest_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

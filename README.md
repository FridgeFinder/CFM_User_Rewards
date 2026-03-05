<p align="center">
  <a href="https://www.fridgefinder.app/">
    <img src="https://raw.githubusercontent.com/CollectiveFocus/CFM_Frontend/dev/public/feedback/happyFridge.svg" height="128">
  </a>
    <h1 align="center">FridgeFinder User Rewards Service</h1>
</p>

<p align="center">
  <a aria-label="GitHub Repo stars" href="https://github.com/FridgeFinder/CFM_User_Rewards/">
    <img alt="" src="https://img.shields.io/github/stars/FridgeFinder/CFM_User_Rewards?style=flat-square&labelColor=F6F6F6">
  </a>
  <img aria-label="GitHub contributors" alt="GitHub contributors" src="https://img.shields.io/github/contributors/FridgeFinder/CFM_User_Rewards?style=flat-square&labelColor=F6F6F6">
  <img aria-label="GitHub commit activity (dev)" alt="GitHub commit activity (dev)" src="https://img.shields.io/github/commit-activity/m/FridgeFinder/CFM_User_Rewards/main?style=flat-square&labelColor=F6F6F6">
  <a aria-label="Join the community on Discord" href="https://discord.com/channels/955884900655972463/955886184159125534">
    <img alt="" src="https://img.shields.io/badge/Join%20the%20community-yellow.svg?style=flat-square&logo=Discord&labelColor=F6F6F6">
  </a>
</p>

# CFM User Rewards Service

Async, event-driven service that awards **points** and maintains **action-stat counters** when users performs actions.

---

## Architecture Overview

```
Producer services (EventBridge events)
        │
        ▼
EventBridge Bus  ─────► EventBridge Rules
                                │
                                ▼
                  UserRewardsConsumerFunction
                     │            │
                     ▼            ▼
              UserPointsHistory  UserActionStats
```
## Pre-Requisites

1. AWS CLI - [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
    * **You DO NOT have to create an AWS account to use AWS CLI for this project, skip these steps if you don't want to create an AWS account**
    * AWS CLI looks for credentials when using it, but doesn't validate. So will need to set some fake one. But the region name matters, use any valid region name. 
        ```sh
        $ aws configure
        $ AWS Access Key ID: [ANYTHING YOU WANT]
        $ AWS Secret Access Key: [ANYTHING YOUR HEART DESIRES]
        $ Default region nam: us-east-1
        $ Default output format [None]: (YOU CAN SKIP)
        ```
2. SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
    * **You DO NOT need to create an aws account to use SAM CLI for this project, skip these steps if you don't want to create an aws account**
    * Note: if you are getting the following error: `runtime is not supported` when running `sam build --use-container` make sure your SAM CLI version is up to date
3. Python 3 - [Install Python 3](https://www.python.org/downloads/)
4. Docker - [Install Docker](https://docs.docker.com/get-docker/)

## Setup Local Database Connection

**Guide that was used:** https://betterprogramming.pub/how-to-deploy-a-local-serverless-application-with-aws-sam-b7b314c3048c

Follow these steps to get Dynamodb running locally

1. **Start a local DynamoDB service**
    ```sh
    $ docker compose up
    # OR if you want to run it in the background:
    $ docker compose up -d
    ```

2. **Create tables**
    ```sh
    $ ./scripts/create_local_dynamodb_tables.py
    ```

## Local Setup
```bash
# 1. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
make install
```

---
## Running Unit Tests

```bash
# Run all tests with verbose output
make test

# Run with coverage report (generates htmlcov/)
make test-cov

# Run a single test file
PYTHONPATH=functions/fridge_report_consumer pytest tests/test_rules.py -v
```
---

## SAM Build & Local Invoke

```bash
# Build Lambda package (resolves dependencies)
make build

# Invoke locally with a FridgeReportUpdated event (both reports present)
make invoke-fridge-report-updated

# Invoke locally with a FridgeReportUpdated event (no previous report)
make invoke-repaired

# Use sam local invoke directly with any event file
sam local invoke UserRewardsConsumerFunction \
    --event events/status_update_created.json \
    --env-vars env.local.json
```
---

## Deploy to AWS

```bash
# First-time guided deploy (creates samconfig.toml)
sam deploy --guided

# Subsequent deploys
make deploy

# Override environment
make deploy ENV=staging
```

---
## License

See [LICENSE](LICENSE).
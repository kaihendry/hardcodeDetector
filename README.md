# CDK Hardcoded Name Detector

A CDK Aspect that detects hardcoded physical resource names which cause conflicts in shared development environments.

## The Problem

When multiple developers deploy to a shared AWS account, hardcoded resource names like `tableName: 'users-table'` will conflict. Only CDK-generated names provide isolation.

## Quick Start

```bash
cd hardcodeDetector
uv sync
uv run cdk synth
```

Expected output shows warnings for hardcoded names:
```
[Warning at /HardcodeDetectorStack/HardcodedBucket/Resource] Hardcoded BucketName: 'my-hardcoded-bucket-name' - consider using CDK-generated names for developer isolation
[Warning at /HardcodeDetectorStack/HardcodedTable/Resource] Hardcoded TableName: 'users-table' - consider using CDK-generated names for developer isolation
```

## Using the Detector in Your Project

Copy `hardcode_detector/aspect.py` to your project and add to your `app.py`:

```python
from aws_cdk import Aspects
from hardcode_detector.aspect import HardcodedNameDetector

# After creating your stacks
Aspects.of(app).add(HardcodedNameDetector())
```

---

## Developer Workflow for Feature Branches

Once hardcoded names are removed, use **stack suffixes** to isolate your work.

### How It Works

CDK generates physical resource names that include the stack name:
- Stack `MyStack` → Bucket `mystack-mybucket-abc123`
- Stack `MyStack-alice` → Bucket `mystack-alice-mybucket-def456`

Different stack names = different resources = no conflicts.

### Step 1: Update Your CDK App

Modify your `app.py` to accept a suffix:

```python
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from my_project.stack import MyStack

app = cdk.App()

# Get suffix from environment (empty = canonical stack for CI/CD)
suffix = os.environ.get("STACK_SUFFIX", "")
stack_name = f"MyStack-{suffix}" if suffix else "MyStack"

MyStack(app, stack_name, env=cdk.Environment(region="eu-west-2"))

app.synth()
```

### Step 2: Developer Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-user-auth

# 2. Deploy your isolated stack (use your name or branch name)
STACK_SUFFIX=alice uv run cdk deploy

# 3. Develop and test against your isolated resources
#    Your stack: MyStack-alice
#    Your resources: mystack-alice-*

# 4. When done, destroy your stack
STACK_SUFFIX=alice uv run cdk destroy

# 5. Merge PR - CI/CD deploys to main stack (no suffix)
git checkout main
git merge feature/add-user-auth
```

### Step 3: Add a Helper Script (Optional)

Create `scripts/dev-deploy.sh`:

```bash
#!/bin/bash
# Deploy with your username as suffix
export STACK_SUFFIX="${STACK_SUFFIX:-$(whoami)}"
echo "Deploying stack: MyStack-${STACK_SUFFIX}"
uv run cdk deploy "$@"
```

Then developers just run:
```bash
./scripts/dev-deploy.sh
```

### CI/CD Integration

In your GitHub Actions workflow:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set stack suffix
        run: |
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            # PR deployments get branch-based suffix
            BRANCH="${{ github.head_ref }}"
            echo "STACK_SUFFIX=${BRANCH//[^a-zA-Z0-9]/-}" >> $GITHUB_ENV
          else
            # Main branch uses canonical stack (no suffix)
            echo "STACK_SUFFIX=" >> $GITHUB_ENV
          fi

      - name: Deploy
        run: uv run cdk deploy --require-approval never
        env:
          STACK_SUFFIX: ${{ env.STACK_SUFFIX }}

      # Clean up PR stacks on merge
      - name: Destroy PR stack
        if: github.event_name == 'pull_request' && github.event.action == 'closed'
        run: uv run cdk destroy --force
        env:
          STACK_SUFFIX: ${{ env.STACK_SUFFIX }}
```

---

## Summary

| Scenario | Stack Name | Command |
|----------|------------|---------|
| Local dev (Alice) | `MyStack-alice` | `STACK_SUFFIX=alice cdk deploy` |
| Local dev (Bob) | `MyStack-bob` | `STACK_SUFFIX=bob cdk deploy` |
| PR #123 | `MyStack-feature-xyz` | CI sets suffix from branch |
| Main branch | `MyStack` | No suffix needed |

**Key points:**
1. Remove all hardcoded physical resource names (use this detector to find them)
2. Use `STACK_SUFFIX` environment variable to namespace stacks
3. Always destroy your dev stacks when done
4. CI/CD manages PR stacks automatically

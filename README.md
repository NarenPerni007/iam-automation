# IAM Automation

Least-privilege IAM across AWS and Azure, plus a read-only review script that flags roles which drifted too broad.

## The approach

- **Roles do one job.** An audit role reads. A deploy role deploys. Nothing gets a standing admin role because it is convenient.
- **Trust is explicit.** The AWS audit role is assumable only by one security account, and only with an external ID. The deploy role is assumable only by one CI role. Trust policies are the real boundary, so they get the most review.
- **No wildcard actions on wildcard resources.** The deploy policy lists the exact actions it needs. Where a service requires `Resource: "*"` (ECR auth token, EKS describe), a region condition narrows it.
- **Azure mirrors the same idea.** Two custom role definitions, Platform Reader and Platform Deployer. Neither grants `roleAssignments/write`, so a deployer can never grant itself more access.

## Layout

| Path | What it holds |
| --- | --- |
| `terraform/aws/` | Audit and deploy roles, scoped deploy policy |
| `terraform/azure/` | Platform Reader and Deployer custom roles and assignments |
| `scripts/iam_review.py` | Read-only AWS role review |
| `tests/` | Unit tests for the policy checks |

## Run a review

```bash
pip install boto3
python3 scripts/iam_review.py --profile my-profile
python3 scripts/iam_review.py --profile my-profile --include-last-used --days 90
python3 scripts/iam_review.py --profile my-profile --format json
```

The script only reads. It never creates, modifies, or deletes anything. `--include-last-used` asks the IAM Access Advisor for each role's activity, which is slow on accounts with many roles, so it is off by default.

## Deploy the Terraform

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

Same steps under `terraform/azure`. Both stacks need their variables filled in: account IDs, principal IDs, bucket and log group ARNs. Nothing secret is committed; the external ID is marked sensitive.

## Notes

- The review script flags roles with no policies at all. That is usually a leftover role, but check before removing anything. A role with no policies can still be assumed, and something may depend on the assume itself.
- Access Advisor data lags by a few hours. Treat "no activity" as a signal to investigate, not proof a role is unused.
- For production use, add a scheduled run of the review script (for example a weekly CI job) and send the output to the team that owns the account.

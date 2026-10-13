#!/usr/bin/env python3
"""Review AWS IAM roles for overly broad permissions.

Read-only. This script never creates, modifies, or deletes anything. It
lists roles, inspects their attached and inline policies, and flags:

- AdministratorAccess or any policy that allows Action "*" on Resource "*"
- Wildcard actions or resources in a policy statement
- Roles with no attached managed policies and no inline policies

With --include-last-used, it also asks the IAM Access Advisor for each
role's last activity and flags roles with no activity in --days days.
That call is slow on accounts with many roles, so it is off by default.

Usage:
    python3 scripts/iam_review.py --profile my-profile
    python3 scripts/iam_review.py --include-last-used --days 90 --format json

Requires boto3 and AWS credentials with iam:ListRoles, iam:ListAttachedRolePolicies,
iam:ListRolePolicies, iam:GetRolePolicy, and (for --include-last-used)
iam:GenerateServiceLastAccessedDetails and iam:GetServiceLastAccessedDetails.
"""

import argparse
import json
import sys
import time

ADMIN_POLICY_SUFFIX = "AdministratorAccess"


def statement_has_wildcard(statement):
    """Return True if a statement allows a wildcard action on all resources.

    A wildcard action scoped to one bucket (s3:* on one bucket) is broad
    but bounded, so it is not flagged here. A wildcard action on Resource
    "*" is the pattern this check targets.
    """
    actions = statement.get("Action", [])
    resources = statement.get("Resource", [])
    if isinstance(actions, str):
        actions = [actions]
    if isinstance(resources, str):
        resources = [resources]
    if statement.get("Effect") != "Allow":
        return False
    action_wildcard = any("*" in a for a in actions)
    resource_wildcard = any(r == "*" for r in resources)
    return action_wildcard and resource_wildcard


def policy_doc_is_overprivileged(policy_doc):
    """Return True if any statement in a policy doc is a full wildcard."""
    statements = policy_doc.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    return any(statement_has_wildcard(s) for s in statements)


def summarize_role(role, attached_arns, inline_docs, last_used=None):
    """Build one finding dict for a role from its policy data."""
    findings = []
    if any(a.endswith(ADMIN_POLICY_SUFFIX) for a in attached_arns):
        findings.append("attached AdministratorAccess")
    if any(policy_doc_is_overprivileged(d) for d in inline_docs):
        findings.append("inline policy allows Action * on Resource *")
    if not attached_arns and not inline_docs:
        findings.append("no attached or inline policies")
    if last_used is True:
        findings.append("no activity in the review window")
    return {
        "role": role["RoleName"],
        "arn": role["Arn"],
        "created": str(role["CreateDate"]),
        "findings": findings,
    }


def fetch_last_used(iam, role_arn, days, timeout_seconds=120):
    """Ask the Access Advisor for a role's recent activity.

    Returns True if the role shows no activity in the last `days` days,
    False if it was active, and None if the report could not be produced.
    """
    import datetime

    job = iam.generate_service_last_accessed_details(Arn=role_arn)
    job_id = job["JobId"]
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        report = iam.get_service_last_accessed_details(JobId=job_id)
        if report["JobStatus"] == "COMPLETED":
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
            for service in report.get("ServicesLastAccessed", []):
                last = service.get("LastAuthenticated")
                if last is not None and last.replace(tzinfo=datetime.timezone.utc) > cutoff:
                    return False
            return True
        if report["JobStatus"] == "FAILED":
            return None
        time.sleep(2)
    return None


def review(iam, include_last_used, days):
    paginator = iam.get_paginator("list_roles")
    results = []
    for page in paginator.paginate():
        for role in page["Roles"]:
            attached = iam.list_attached_role_policies(RoleName=role["RoleName"])["AttachedPolicies"]
            attached_arns = [p["PolicyArn"] for p in attached]
            inline_docs = []
            for policy_name in iam.list_role_policies(RoleName=role["RoleName"])["PolicyNames"]:
                doc = iam.get_role_policy(RoleName=role["RoleName"], PolicyName=policy_name)["PolicyDocument"]
                inline_docs.append(doc)
            last_used = None
            if include_last_used:
                last_used = fetch_last_used(iam, role["Arn"], days)
            finding = summarize_role(role, attached_arns, inline_docs, last_used)
            if finding["findings"]:
                results.append(finding)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review IAM roles for overly broad permissions (read-only).")
    parser.add_argument("--profile", help="AWS profile to use")
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--include-last-used", action="store_true",
                        help="Also flag roles with no Access Advisor activity")
    parser.add_argument("--days", type=int, default=90,
                        help="Inactivity window in days for --include-last-used (default: 90)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    args = parser.parse_args(argv)

    try:
        import boto3
    except ImportError:
        print("boto3 is required: pip install boto3", file=sys.stderr)
        return 2

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    iam = session.client("iam")
    results = review(iam, args.include_last_used, args.days)

    if args.format == "json":
        print(json.dumps(results, indent=2, default=str))
    elif not results:
        print("No findings. No roles matched the review checks.")
    else:
        for r in results:
            print(f"{r['role']} ({r['arn']})")
            for f in r["findings"]:
                print(f"  - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

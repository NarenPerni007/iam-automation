import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from iam_review import policy_doc_is_overprivileged, statement_has_wildcard, summarize_role


class TestPolicyChecks(unittest.TestCase):
    def test_full_wildcard_statement(self):
        stmt = {"Effect": "Allow", "Action": "*", "Resource": "*"}
        self.assertTrue(statement_has_wildcard(stmt))

    def test_scoped_statement_is_not_wildcard(self):
        stmt = {
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::my-bucket/*"],
        }
        self.assertFalse(statement_has_wildcard(stmt))

    def test_deny_statement_is_not_flagged(self):
        stmt = {"Effect": "Deny", "Action": "*", "Resource": "*"}
        self.assertFalse(statement_has_wildcard(stmt))

    def test_wildcard_action_with_scoped_resource(self):
        stmt = {"Effect": "Allow", "Action": ["s3:*"], "Resource": ["arn:aws:s3:::my-bucket/*"]}
        self.assertFalse(statement_has_wildcard(stmt))

    def test_policy_doc_with_one_bad_statement(self):
        doc = {"Statement": [
            {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": ["arn:aws:s3:::b/*"]},
            {"Effect": "Allow", "Action": "*", "Resource": "*"},
        ]}
        self.assertTrue(policy_doc_is_overprivileged(doc))

    def test_admin_attachment_flagged(self):
        role = {"RoleName": "x", "Arn": "arn:aws:iam::1:role/x", "CreateDate": "2024-01-01"}
        result = summarize_role(role, ["arn:aws:iam::aws:policy/AdministratorAccess"], [], None)
        self.assertIn("attached AdministratorAccess", result["findings"])

    def test_role_with_no_policies_flagged(self):
        role = {"RoleName": "x", "Arn": "arn:aws:iam::1:role/x", "CreateDate": "2024-01-01"}
        result = summarize_role(role, [], [], None)
        self.assertIn("no attached or inline policies", result["findings"])

    def test_clean_role_has_no_findings(self):
        role = {"RoleName": "x", "Arn": "arn:aws:iam::1:role/x", "CreateDate": "2024-01-01"}
        result = summarize_role(role, ["arn:aws:iam::aws:policy/ReadOnlyAccess"], [], None)
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()

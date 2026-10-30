# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe

IMB_ROLES = (
	"IMB Accounts",
	"IMB Approver",
)


def ensure_imb_roles():
	"""Create desk roles for Imprest Book (idempotent)."""
	created = 0
	for role_name in IMB_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
				"is_custom": 1,
			}
		).insert(ignore_permissions=True)
		created += 1
	if created:
		frappe.db.commit()
		print(f"[imprest_book] Created {created} IMB role(s).")

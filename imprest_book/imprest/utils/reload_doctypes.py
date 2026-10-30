# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe

# Child fields Accounts must edit after the Imprest Book is submitted (docstatus 1).
_SUBMITTABLE_ROW_FIELDS = (
	"account",
	"cost_center",
	"party_type",
	"party",
	"against_voucher_type",
	"against_voucher",
	"beneficiary_name",
	"bank_name",
	"bank_account_no",
	"md_remarks",
)


def reload():
	"""Reload IMB doctypes from app JSON into the site database."""
	frappe.reload_doc("Imprest", "doctype", "imb_imprest_item", force=True)
	frappe.reload_doc("Imprest", "doctype", "imb_imprest_book", force=True)
	_sync_imprest_item_meta()
	frappe.clear_cache(doctype="IMB Imprest Item")
	frappe.clear_cache(doctype="IMB Imprest Book")
	frappe.db.commit()
	print("RELOAD_OK")


def _sync_imprest_item_meta():
	"""Ensure grid + allow_on_submit match app (migrate alone can lag on child tables)."""
	if not frappe.db.exists("DocType", "IMB Imprest Item"):
		return

	frappe.db.set_value("DocType", "IMB Imprest Item", "editable_grid", 0)

	for fieldname in _SUBMITTABLE_ROW_FIELDS:
		if frappe.db.exists(
			"DocField", {"parent": "IMB Imprest Item", "fieldname": fieldname}
		):
			frappe.db.set_value(
				"DocField",
				{"parent": "IMB Imprest Item", "fieldname": fieldname},
				"allow_on_submit",
				1,
			)

	if frappe.db.exists("DocField", {"parent": "IMB Imprest Book", "fieldname": "items"}):
		frappe.db.set_value(
			"DocField",
			{"parent": "IMB Imprest Book", "fieldname": "items"},
			"allow_on_submit",
			1,
		)

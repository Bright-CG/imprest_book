# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe

WORKSPACE_NAME = "Imprest Book"
ACCOUNTING_WORKSPACE = "Accounting"


def create_workspace():
	shortcuts = [
		{
			"label": "Imprest Book",
			"link_to": "IMB Imprest Book",
			"type": "DocType",
			"icon": "money",
		},
	]
	links = [
		{"label": "Imprest", "is_header": 1},
		{
			"label": "IMB Imprest Book",
			"link_to": "IMB Imprest Book",
			"link_type": "DocType",
			"type": "Link",
		},
	]
	content = (
		"["
		'{"id":"imb-h","type":"header","data":{"text":"Imprest Book","col":12}},'
		'{"id":"imb-s","type":"shortcut","data":{"shortcut_name":"Imprest Book","col":4}}'
		"]"
	)

	schema = {
		"doctype": "Workspace",
		"name": WORKSPACE_NAME,
		"label": WORKSPACE_NAME,
		"title": WORKSPACE_NAME,
		"module": "Imprest",
		"public": 1,
		"is_hidden": 0,
		"icon": "money",
		"content": content,
	}

	if frappe.db.exists("Workspace", WORKSPACE_NAME):
		doc = frappe.get_doc("Workspace", WORKSPACE_NAME)
	else:
		doc = frappe.new_doc("Workspace")
		doc.name = WORKSPACE_NAME

	doc.update(schema)
	doc.set("shortcuts", [])
	doc.set("links", [])
	for row in shortcuts:
		doc.append("shortcuts", row)
	for row in links:
		doc.append("links", row)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	print("[imprest_book] Synced workspace Imprest Book.")


def add_accounting_shortcut():
	"""Add a Desk shortcut on the standard Accounting workspace when it exists."""
	if not frappe.db.exists("Workspace", ACCOUNTING_WORKSPACE):
		return
	if not frappe.db.exists("DocType", "IMB Imprest Book"):
		return

	doc = frappe.get_doc("Workspace", ACCOUNTING_WORKSPACE)
	for row in doc.get("shortcuts") or []:
		if row.get("link_to") == "IMB Imprest Book":
			return
	doc.append(
		"shortcuts",
		{
			"label": "Imprest Book",
			"link_to": "IMB Imprest Book",
			"type": "DocType",
			"icon": "money",
		},
	)
	try:
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		print("[imprest_book] Added Imprest Book shortcut to Accounting workspace.")
	except Exception:
		frappe.log_error(title="imprest_book Accounting shortcut failed")

# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe


def reload():
	frappe.reload_doc("Imprest", "doctype", "imb_imprest_item", force=True)
	frappe.reload_doc("Imprest", "doctype", "imb_imprest_book", force=True)
	frappe.clear_cache()
	frappe.db.commit()
	print("RELOAD_OK")

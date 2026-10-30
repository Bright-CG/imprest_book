# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe

from imprest_book.setup_defaults import ensure_imb_roles
from imprest_book.setup_workspace import add_accounting_shortcut, create_workspace


def run_after_install():
	"""Isolated install steps so one failure cannot abort the rest."""
	for fn, label in (
		(ensure_imb_roles, "roles"),
		(create_workspace, "workspace"),
		(add_accounting_shortcut, "Accounting shortcut"),
	):
		try:
			fn()
		except Exception:
			frappe.log_error(title=f"imprest_book after_install {label} failed")
			print(f"[imprest_book after_install] {label} skipped (non-fatal).")

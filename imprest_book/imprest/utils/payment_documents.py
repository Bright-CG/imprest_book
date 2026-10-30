# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

"""Create Draft Payment Entry / Journal Entry from an approved Imprest row.

Imprest Book itself never posts GL. These helpers only map filled fields and
leave the rest for Accounts to complete on the ERPNext document.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, nowdate

PAYMENT_ENTRY_TYPES = ("Supplier Payment", "Against Purchase Invoice", "Employee Loan")
JOURNAL_ENTRY_TYPES = ("Expense", "Other")


@frappe.whitelist()
def create_ledger_document(imprest_book: str, item_row: str):
	"""Create or open the Draft Payment Entry / Journal Entry for one approved row."""
	parent = frappe.get_doc("IMB Imprest Book", imprest_book)
	if parent.docstatus != 1:
		frappe.throw(_("Submit the Imprest Book before creating Payment Entry or Journal Entry."))

	row = next((r for r in parent.items if r.name == item_row), None)
	if not row:
		frappe.throw(_("Imprest row not found."))
	if row.md_decision != "Approved":
		frappe.throw(_("Only Approved rows can create a Payment Entry or Journal Entry."))

	if row.payment_document and row.payment_document_type:
		if frappe.db.exists(row.payment_document_type, row.payment_document):
			return {"doctype": row.payment_document_type, "name": row.payment_document}

	if row.payment_type in PAYMENT_ENTRY_TYPES:
		doc = _make_payment_entry(parent, row)
	else:
		doc = _make_journal_entry(parent, row)

	frappe.db.set_value(
		"IMB Imprest Item",
		row.name,
		{
			"payment_document_type": doc.doctype,
			"payment_document": doc.name,
			"posting_status": "Draft",
		},
	)

	return {"doctype": doc.doctype, "name": doc.name}


def sync_row_from_ledger_doc(doc, method=None):
	"""Keep child posting_status in sync when PE/JE is saved, submitted, or cancelled."""
	if not frappe.db.exists("DocType", "IMB Imprest Item"):
		return
	if not frappe.db.has_column("IMB Imprest Item", "payment_document"):
		return

	status = "Draft"
	if doc.docstatus == 1:
		status = "Submitted"
	elif doc.docstatus == 2:
		status = "Cancelled"

	frappe.db.sql(
		"""
		UPDATE `tabIMB Imprest Item`
		SET posting_status = %s
		WHERE payment_document = %s AND payment_document_type = %s
		""",
		(status, doc.name, doc.doctype),
	)


def _make_payment_entry(parent, row):
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = parent.company
	pe.posting_date = nowdate()
	pe.mode_of_payment = None

	if row.party_type and row.party:
		pe.party_type = row.party_type
		pe.party = row.party

	if parent.paid_from_account:
		pe.paid_from = parent.paid_from_account
		_copy_account_currency(pe, "paid_from", "paid_from_account_currency")

	paid_to = row.account
	if not paid_to and row.party_type and row.party:
		paid_to = _safe_party_account(row.party_type, row.party, parent.company)
	if paid_to:
		pe.paid_to = paid_to
		_copy_account_currency(pe, "paid_to", "paid_to_account_currency")

	amount = flt(row.amount)
	pe.paid_amount = amount
	pe.received_amount = amount
	pe.source_exchange_rate = 1
	pe.target_exchange_rate = 1
	if row.cost_center:
		pe.cost_center = row.cost_center
	pe.reference_no = parent.name
	pe.reference_date = parent.imprest_date or nowdate()
	pe.remarks = row.purpose or parent.name

	if (
		row.payment_type == "Against Purchase Invoice"
		and row.against_voucher
		and frappe.db.exists("Purchase Invoice", row.against_voucher)
	):
		pe.append(
			"references",
			{
				"reference_doctype": "Purchase Invoice",
				"reference_name": row.against_voucher,
				"allocated_amount": amount,
			},
		)

	pe.flags.ignore_mandatory = True
	pe.insert(ignore_permissions=True, ignore_mandatory=True)
	return pe


def _make_journal_entry(parent, row):
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Bank Entry"
	je.company = parent.company
	je.posting_date = nowdate()
	je.cheque_no = parent.name
	je.cheque_date = parent.imprest_date or nowdate()
	je.user_remark = row.purpose or parent.name
	amount = flt(row.amount)

	debit = {
		"debit_in_account_currency": amount,
		"credit_in_account_currency": 0,
		"user_remark": row.purpose,
	}
	if row.account:
		debit["account"] = row.account
	if row.cost_center:
		debit["cost_center"] = row.cost_center
	if row.party_type and row.party:
		debit["party_type"] = row.party_type
		debit["party"] = row.party
	je.append("accounts", debit)

	credit = {
		"debit_in_account_currency": 0,
		"credit_in_account_currency": amount,
		"user_remark": row.purpose,
	}
	if parent.paid_from_account:
		credit["account"] = parent.paid_from_account
	if row.cost_center:
		credit["cost_center"] = row.cost_center
	je.append("accounts", credit)

	je.flags.ignore_mandatory = True
	je.insert(ignore_permissions=True, ignore_mandatory=True)
	return je


def _copy_account_currency(doc, account_field, currency_field):
	account = doc.get(account_field)
	if not account:
		return
	currency = frappe.db.get_value("Account", account, "account_currency")
	if currency:
		doc.set(currency_field, currency)


def _safe_party_account(party_type, party, company):
	try:
		from erpnext.accounts.party import get_party_account

		return get_party_account(party_type, party, company)
	except Exception:
		return None

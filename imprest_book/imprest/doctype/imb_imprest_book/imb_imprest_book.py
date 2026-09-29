# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

STATE_DRAFT = "Draft"
STATE_PENDING = "Pending"
STATE_COMPLETED = "Completed"


class IMBImprestBook(Document):
	def before_insert(self):
		if not self.requested_by:
			self.requested_by = frappe.session.user

	def validate(self):
		self._apply_row_defaults()
		self._recalculate_totals()
		self._stamp_authorization_users()
		self._validate_rows()

	def before_submit(self):
		self._validate_md_decisions_for_submit()
		if not self.approved_by:
			self.approved_by = frappe.session.user
		self.workflow_state = STATE_COMPLETED

	def on_submit(self):
		pass

	def before_cancel(self):
		self._assert_no_ledger_documents()

	def on_trash(self):
		if self.docstatus != 0:
			frappe.throw(_("Cannot delete a submitted Imprest Book."))
		state = (self.workflow_state or STATE_DRAFT).strip()
		if state not in (STATE_DRAFT, STATE_PENDING):
			frappe.throw(_("Only Draft or Pending Imprest Books can be deleted."))

	def _apply_row_defaults(self):
		for row in self.items or []:
			row.party_type = _party_type_for_payment_type(row.payment_type) or row.party_type
			if row.payment_type == "Against Purchase Invoice":
				row.against_voucher_type = row.against_voucher_type or "Purchase Invoice"
			elif row.payment_type != "Against Purchase Invoice":
				row.against_voucher_type = None
				row.against_voucher = None
			if not row.md_decision:
				row.md_decision = "Pending"
			if not row.posting_status:
				row.posting_status = "Not Created"

	def _recalculate_totals(self):
		requested = approved = rejected = 0.0
		for row in self.items or []:
			amount = flt(row.amount)
			requested += amount
			if row.md_decision == "Approved":
				approved += amount
			elif row.md_decision == "Rejected":
				rejected += amount
		self.total_requested = requested
		self.total_approved = approved
		self.total_rejected = rejected

	def _stamp_authorization_users(self):
		state = (self.workflow_state or STATE_DRAFT).strip()
		if state == STATE_PENDING and not self.authorized_by:
			self.authorized_by = frappe.session.user
		if (
			state == STATE_DRAFT
			and not self.is_new()
			and self.has_value_changed("workflow_state")
			and self.get_doc_before_save()
			and self.get_doc_before_save().workflow_state == STATE_PENDING
		):
			self.authorized_by = None
		if self.docstatus == 1 or state == STATE_COMPLETED:
			if not self.approved_by:
				self.approved_by = frappe.session.user

	def _validate_rows(self):
		if not self.items:
			frappe.throw(_("Add at least one payment row."))
		for row in self.items:
			if flt(row.amount) <= 0:
				frappe.throw(_("Amount must be greater than zero on row {0}.").format(row.idx))
			expected_party_type = _party_type_for_payment_type(row.payment_type)
			if expected_party_type:
				if not row.party:
					frappe.throw(
						_("Select a {0} on row {1}.").format(expected_party_type, row.idx)
					)
			if row.payment_type == "Against Purchase Invoice" and not row.against_voucher:
				frappe.throw(_("Select a Purchase Invoice on row {0}.").format(row.idx))

	def _validate_md_decisions_for_submit(self):
		approved = 0
		for row in self.items or []:
			if row.md_decision == "Pending":
				frappe.throw(
					_(
						"Set Approved or Rejected on every row before Submit. Row {0} is still Pending."
					).format(row.idx)
				)
			if row.md_decision == "Approved":
				approved += 1
		if not approved:
			frappe.throw(_("Approve at least one row before Submit."))

	def _assert_no_ledger_documents(self):
		linked = [
			row.payment_document
			for row in self.items or []
			if row.payment_document
		]
		if linked:
			frappe.throw(
				_(
					"Cannot cancel this Imprest Book because Payment Entry / Journal Entry documents already exist: {0}"
				).format(", ".join(linked))
			)


def _party_type_for_payment_type(payment_type):
	if payment_type in ("Supplier Payment", "Against Purchase Invoice"):
		return "Supplier"
	if payment_type == "Employee Loan":
		return "Employee"
	return ""

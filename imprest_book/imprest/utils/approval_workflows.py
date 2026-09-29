# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

"""Frappe Workflow for IMB Imprest Book.

Draft → Pending (accounts authorize) → Completed (MD Submit).
Submit does not post GL.
"""

from __future__ import annotations

import frappe

from imprest_book.setup_defaults import ensure_imb_roles

STATE_DRAFT = "Draft"
STATE_PENDING = "Pending"
STATE_COMPLETED = "Completed"

WORKFLOW_NAME = "IMB Imprest Book Approval"
DOCTYPE = "IMB Imprest Book"

DRAFT_ROLES = [
	"IMB Accounts",
	"Accounts User",
	"Accounts Manager",
	"System Manager",
]
AUTHORIZE_ROLES = [
	"Accounts Manager",
	"System Manager",
]
MD_ROLES = [
	"IMB Approver",
	"System Manager",
]
COMPLETED_EDIT_ROLES = ["System Manager"]


def ensure_imb_approval_workflow():
	ensure_imb_roles()
	_ensure_states()
	_ensure_actions(("Send for Authorization", "Return to Draft", "Submit"))
	if not frappe.db.exists("DocType", DOCTYPE):
		return
	_ensure_workflow()
	frappe.clear_cache()
	print("[imprest_book] Ensured IMB Imprest Book Workflow.")


def _ensure_states():
	styles = {
		STATE_DRAFT: "",
		STATE_PENDING: "Warning",
		STATE_COMPLETED: "Success",
	}
	for state, style in styles.items():
		if frappe.db.exists("Workflow State", state):
			continue
		frappe.get_doc(
			{
				"doctype": "Workflow State",
				"workflow_state_name": state,
				"style": style,
			}
		).insert(ignore_permissions=True)


def _ensure_actions(actions):
	for action in actions:
		if frappe.db.exists("Workflow Action Master", action):
			continue
		frappe.get_doc(
			{"doctype": "Workflow Action Master", "workflow_action_name": action}
		).insert(ignore_permissions=True)


def _state_rows(state, doc_status, roles):
	return [
		{
			"state": state,
			"doc_status": doc_status,
			"allow_edit": role,
			"is_optional_state": 0,
		}
		for role in roles
	]


def _transition_rows(state, action, next_state, roles):
	return [
		{
			"state": state,
			"action": action,
			"next_state": next_state,
			"allowed": role,
			"allow_self_approval": 1,
		}
		for role in roles
	]


def _ensure_workflow():
	# Pending is still docstatus 0 so MD can set row decisions, then Submit sets docstatus 1.
	pending_edit = list(dict.fromkeys(AUTHORIZE_ROLES + MD_ROLES))
	states = []
	states.extend(_state_rows(STATE_DRAFT, "0", DRAFT_ROLES))
	states.extend(_state_rows(STATE_PENDING, "0", pending_edit))
	states.extend(_state_rows(STATE_COMPLETED, "1", COMPLETED_EDIT_ROLES))

	transitions = []
	transitions.extend(
		_transition_rows(STATE_DRAFT, "Send for Authorization", STATE_PENDING, AUTHORIZE_ROLES)
	)
	transitions.extend(
		_transition_rows(STATE_PENDING, "Return to Draft", STATE_DRAFT, AUTHORIZE_ROLES)
	)
	transitions.extend(_transition_rows(STATE_PENDING, "Submit", STATE_COMPLETED, MD_ROLES))

	payload = {
		"doctype": "Workflow",
		"workflow_name": WORKFLOW_NAME,
		"document_type": DOCTYPE,
		"is_active": 1,
		"override_status": 0,
		"send_email_alert": 0,
		"workflow_state_field": "workflow_state",
	}

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		doc = frappe.get_doc("Workflow", WORKFLOW_NAME)
		doc.update(payload)
		doc.states = []
		doc.transitions = []
		for row in states:
			doc.append("states", row)
		for row in transitions:
			doc.append("transitions", row)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(payload)
		for row in states:
			doc.append("states", row)
		for row in transitions:
			doc.append("transitions", row)
		doc.insert(ignore_permissions=True)

	others = frappe.get_all(
		"Workflow",
		filters={"document_type": DOCTYPE, "is_active": 1, "name": ["!=", WORKFLOW_NAME]},
		pluck="name",
	)
	for other in others:
		frappe.db.set_value("Workflow", other, "is_active", 0)

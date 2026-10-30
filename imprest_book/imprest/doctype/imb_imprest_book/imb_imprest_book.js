// Copyright (c) 2026, Bright and contributors
// For license information, please see license.txt

frappe.ui.form.on("IMB Imprest Book", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.requested_by) {
			frm.set_value("requested_by", frappe.session.user);
		}

		frm.set_query("paid_from_account", () => ({
			filters: {
				account_type: "Bank",
				company: frm.doc.company,
				is_group: 0,
			},
		}));
	},

	refresh(frm) {
		configure_item_grid(frm);
		frm.set_query("account", "items", () => ({
			filters: {
				company: frm.doc.company,
				is_group: 0,
			},
		}));
		frm.set_query("cost_center", "items", () => ({
			filters: {
				company: frm.doc.company,
				is_group: 0,
			},
		}));
		frm.set_query("against_voucher", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn] || {};
			const filters = { docstatus: 1, company: doc.company };
			if (row.party) {
				filters.supplier = row.party;
			}
			return { filters };
		});

		try {
			lock_md_columns(frm);
		} catch (e) {
			console.error("IMB Imprest Book MD column lock failed", e);
		}

		if (frm.doc.docstatus === 1) {
			(frm.doc.items || []).forEach((row) => {
				if (row.md_decision !== "Approved") {
					return;
				}
				const label = row.payment_document
					? __("Open {0}", [row.payment_document])
					: __("Row {0}: {1}", [row.idx, row.party || row.payment_type]);
				frm.add_custom_button(label, () => create_ledger_for_row(frm, row.name), __("Create Payment / Journal"));
			});
		}
	},

	company(frm) {
		frm.set_query("paid_from_account", () => ({
			filters: {
				account_type: "Bank",
				company: frm.doc.company,
				is_group: 0,
			},
		}));
	},
});

frappe.ui.form.on("IMB Imprest Item", {
	payment_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const party_type = party_type_for(row.payment_type);
		frappe.model.set_value(cdt, cdn, "party_type", party_type);
		if (!party_type) {
			frappe.model.set_value(cdt, cdn, "party", "");
		}
		if (row.payment_type === "Against Purchase Invoice") {
			frappe.model.set_value(cdt, cdn, "against_voucher_type", "Purchase Invoice");
		} else {
			frappe.model.set_value(cdt, cdn, "against_voucher_type", "");
			frappe.model.set_value(cdt, cdn, "against_voucher", "");
		}
	},

	party_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.party_type) {
			frappe.model.set_value(cdt, cdn, "party", "");
		}
	},

	create_ledger_document(frm, cdt, cdn) {
		create_ledger_for_row(frm, cdn);
	},
});

function can_set_md_decision(frm) {
	const roles = frappe.user_roles || [];
	const allowed = roles.includes("IMB Approver") || roles.includes("System Manager");
	return allowed && frm.doc.docstatus === 0 && (frm.doc.workflow_state || "Draft") === "Pending";
}

function lock_md_columns(frm) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid || !grid.update_docfield_property) {
		return;
	}
	const read_only = can_set_md_decision(frm) ? 0 : 1;
	grid.update_docfield_property("md_decision", "read_only", read_only);
	grid.update_docfield_property("md_remarks", "read_only", read_only);
}

function configure_item_grid(frm) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid || !grid.update_docfield_property) {
		return;
	}
	// Frappe hides empty read-only child fields on submitted parents unless allow_on_submit is set.
	const editable_after_submit = [
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
	];
	editable_after_submit.forEach((fieldname) => {
		grid.update_docfield_property(fieldname, "allow_on_submit", 1);
		grid.update_docfield_property(fieldname, "hidden", 0);
	});
	if (grid.meta) {
		grid.meta.editable_grid = 0;
	}
	const can_edit_ledger_fields =
		frm.doc.docstatus === 0 ||
		frappe.user.has_role("Accounts Manager") ||
		frappe.user.has_role("Accounts User") ||
		frappe.user.has_role("IMB Accounts") ||
		frappe.user.has_role("System Manager");
	grid.update_docfield_property("account", "read_only", can_edit_ledger_fields ? 0 : 1);
	grid.update_docfield_property("cost_center", "read_only", can_edit_ledger_fields ? 0 : 1);
}

function party_type_for(payment_type) {
	if (payment_type === "Supplier Payment" || payment_type === "Against Purchase Invoice") {
		return "Supplier";
	}
	if (payment_type === "Employee Loan") {
		return "Employee";
	}
	return "";
}

function create_ledger_for_row(frm, row_name) {
	if (frm.doc.docstatus !== 1) {
		frappe.msgprint(__("Submit the Imprest Book before creating Payment Entry or Journal Entry."));
		return;
	}
	frappe.call({
		method: "imprest_book.imprest.utils.payment_documents.create_ledger_document",
		args: { imprest_book: frm.doc.name, item_row: row_name },
		freeze: true,
		freeze_message: __("Creating draft document..."),
		callback(r) {
			if (!r.message) {
				return;
			}
			frm.reload_doc();
			frappe.set_route("Form", r.message.doctype, r.message.name);
		},
	});
}

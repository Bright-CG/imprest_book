# Copyright (c) 2026, Bright and contributors
# For license information, please see license.txt

frappe.ui.form.on("IMB Imprest Book", {
	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.company) {
				const company = frappe.defaults.get_user_default("Company");
				if (company) {
					frm.set_value("company", company);
				}
			}
			if (!frm.doc.requested_by) {
				frm.set_value("requested_by", frappe.session.user);
			}
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
			const row = locals[cdt][cdn];
			const filters = { docstatus: 1, company: doc.company };
			if (row.party) {
				filters.supplier = row.party;
			}
			return { filters };
		});

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

		if (frm.dashboard && frm.dashboard.set_headline) {
			if (frm.doc.docstatus === 0) {
				frm.dashboard.set_headline(
					__(
						"Imprest Book does not post to accounts. Use Actions: Send for Authorization, then MD Submit. Create Payment Entry / Journal Entry only after Completed."
					)
				);
			} else if (frm.doc.docstatus === 1) {
				frm.dashboard.set_headline(
					__("Completed. Print approved rows for the bank. Create Draft Payment Entry or Journal Entry per approved row — those documents post GL.")
				);
			}
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

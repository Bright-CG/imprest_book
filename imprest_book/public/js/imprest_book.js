// Desk asset: do not register before_load. That event is awaited and will
// skip Form.render_form while any frappe.call is still in flight.
frappe.ui.form.on("IMB Imprest Book", {
	refresh(frm) {
		if (!frm || frm.doctype !== "IMB Imprest Book") {
			return;
		}
		if (frm.doc && cint(frm.doc.docstatus) === 0) {
			frm.read_only = 0;
		}
	},
});

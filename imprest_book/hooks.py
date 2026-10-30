app_name = "imprest_book"
app_title = "Imprest Book"
app_publisher = "Bright Godwin"
app_description = "MD-approved disbursement book. Does not post GL; Payment Entry and Journal Entry remain the ledger documents."
app_email = "brightgodwin9@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

app_include_css = ["/assets/imprest_book/css/imprest_book.css"]
app_include_js = ["/assets/imprest_book/js/imprest_book.js"]

fixtures = [
	{
		"dt": "Role",
		"filters": [["name", "in", ["IMB Accounts", "IMB Approver"]]],
	}
]

after_install = ["imprest_book.install.run_after_install"]

after_migrate = [
	"imprest_book.setup_defaults.ensure_imb_roles",
	"imprest_book.imprest.utils.approval_workflows.ensure_imb_approval_workflow",
	"imprest_book.imprest.utils.reload_doctypes.reload",
	"imprest_book.setup_workspace.create_workspace",
	"imprest_book.setup_workspace.add_accounting_shortcut",
]

doctype_js = {
	"IMB Imprest Book": "imprest/doctype/imb_imprest_book/imb_imprest_book.js",
}

doc_events = {
	"Payment Entry": {
		"on_submit": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
		"on_cancel": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
		"on_update": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
	},
	"Journal Entry": {
		"on_submit": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
		"on_cancel": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
		"on_update": "imprest_book.imprest.utils.payment_documents.sync_row_from_ledger_doc",
	},
}

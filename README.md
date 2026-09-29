# Imprest Book

**Imprest Book** is a custom [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/) app for daily disbursement requests. Clerks list payments (suppliers, purchase invoices, expenses, employee loans). A senior accountant authorizes the book. The MD approves or rejects **each row**, then submits. Accounts print a bank letter from the approved rows, then create **Draft** Payment Entries or Journal Entries. Those ERPNext documents — not this app — post to the ledger.

| | |
|---|---|
| **App name** | `imprest_book` |
| **Prefix** | **IMB** (Imprest Book) |
| **Desk workspace** | Imprest Book (plus a shortcut on Accounting) |
| **ERPNext** | v15 |

This app is separate from [PU Foam Master](https://github.com/Bright-CG/pu_foam_master). Both can run on the same site.

## What it does not do

- It does **not** debit or credit any account.
- Submit only locks the approved list for print and for creating Draft PE/JE.

## Workflow

`Draft` → **Send for Authorization** → `Pending` → MD sets Approved/Rejected on rows → **Submit** → `Completed`

From Pending, Accounts Manager can **Return to Draft** to amend. Completed books cannot be amended. Cancel is blocked if a PE/JE already exists.

## Roles

| Role | Use |
|------|-----|
| **Accounts User** / **IMB Accounts** | Create and edit Draft |
| **Accounts Manager** | Send for Authorization / Return to Draft |
| **IMB Approver** | MD: row decisions + Submit |
| **System Manager** | Full access |

Assign **IMB Approver** to the MD user after install.

## Payment types (v1)

Supplier Payment, Against Purchase Invoice, Expense, Employee Loan, Other.

Type filters the Party field (Supplier vs Employee). Expense and Other do not require a party.

## Install

From a Frappe bench that already has ERPNext:

```bash
bench get-app https://github.com/Bright-CG/imprest_book.git
bench --site <site> install-app imprest_book
bench --site <site> migrate
bench build --app imprest_book
```

For a local checkout, symlink the repo into `apps/imprest_book` instead of `get-app`.

## License

MIT

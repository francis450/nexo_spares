// Simplified Purchase Invoice for Nexo Auto Spares.
// Hides fields irrelevant to a small shop, auto-fills company and warehouse.

frappe.ui.form.on("Purchase Invoice", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.set_value("company", "Nexo Autospares");
			frm.set_value("update_stock", 1);
			frm.set_value("set_warehouse", "Stores - NA");
		}
	},
	refresh: function (frm) {
		nexo_hide_purchase_invoice_fields(frm);
	},
});

function nexo_hide_purchase_invoice_fields(frm) {
	const hide = [
		// GL / Accounting
		"credit_to",
		"party_account_currency",
		"is_internal_supplier",
		"inter_company_invoice_reference",
		// Tax
		"taxes_and_charges",
		"taxes",
		"tax_category",
		"shipping_rule",
		"incoterm",
		"named_place",
		// Print / Misc
		"letter_head",
		"select_print_heading",
		"language",
		"terms_and_conditions",
		"terms",
		// Discounts / Advance
		"apply_discount_on",
		"base_discount_amount",
		"additional_discount_percentage",
		"discount_amount",
		"advances",
		// PO / PR links — not using that flow
		"purchase_order",
		"purchase_receipt",
		// Amended
		"amended_from",
		// Posting time
		"set_posting_time",
		// Dimensions
		"cost_center",
		"project",
		"accounting_dimensions_section",
		// Supplier invoice ref
		"supplier_invoice_no",
		"supplier_invoice_date",
		// Other info
		"scan_barcode",
		"against_expense_account",
	];
	frm.toggle_display(hide, false);
}

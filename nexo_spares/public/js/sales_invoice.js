// Simplified Sales Invoice for Nexo Auto Spares.
// Used for credit sales (walk-in cash/M-Pesa goes through POSAwesome).

frappe.ui.form.on("Sales Invoice", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.set_value("company", "Nexo Autospares");
			frm.set_value("update_stock", 1);
			frm.set_value("set_warehouse", "Stores - NA");
		}
	},
	refresh: function (frm) {
		nexo_hide_sales_invoice_fields(frm);
	},
});

function nexo_hide_sales_invoice_fields(frm) {
	const hide = [
		// GL / Accounting
		"debit_to",
		"party_account_currency",
		"is_internal_customer",
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
		"additional_discount_percentage",
		"discount_amount",
		"advances",
		// SO / DN links
		"sales_order",
		"delivery_note",
		// Amended
		"amended_from",
		"set_posting_time",
		// Dimensions
		"cost_center",
		"project",
		"accounting_dimensions_section",
		// Commission / Loyalty
		"commission_rate",
		"total_commission",
		"loyalty_points",
		"loyalty_amount",
		"redeem_loyalty_points",
		// Standard POS profile (using POSAwesome)
		"pos_profile",
		"scan_barcode",
	];
	frm.toggle_display(hide, false);
}

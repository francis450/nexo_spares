// Simplified Payment Entry for Nexo Auto Spares.
// Used only to settle outstanding credit sales invoices.

frappe.ui.form.on("Payment Entry", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.set_value("company", "Nexo Autospares");
			frm.set_value("payment_type", "Receive");
		}
	},
	refresh: function (frm) {
		nexo_hide_payment_entry_fields(frm);
	},
});

function nexo_hide_payment_entry_fields(frm) {
	const hide = [
		// GL accounts
		"paid_from",
		"paid_to",
		"paid_from_account_currency",
		"paid_to_account_currency",
		"source_exchange_rate",
		"target_exchange_rate",
		"base_paid_amount",
		"base_received_amount",
		// Difference / write-off
		"difference_amount",
		"difference_account",
		"write_off_difference_amount",
		// Dimensions
		"cost_center",
		"project",
		"accounting_dimensions_section",
		// Print
		"letter_head",
		// Amended
		"amended_from",
		"custom_remarks",
	];
	frm.toggle_display(hide, false);
}

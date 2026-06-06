frappe.query_reports["Expense Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "expense_category",
			label: __("Expense Category"),
			fieldtype: "Link",
			options: "Expense Category",
		},
		{
			fieldname: "mode_of_payment",
			label: __("Mode of Payment"),
			fieldtype: "Link",
			options: "Mode of Payment",
		},
	],
};

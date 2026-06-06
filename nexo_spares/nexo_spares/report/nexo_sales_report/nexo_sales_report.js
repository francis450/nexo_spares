frappe.query_reports["Nexo Sales Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "mode_of_payment",
			label: __("Mode of Payment"),
			fieldtype: "Link",
			options: "Mode of Payment",
		},
		{
			fieldname: "include_credit_sales",
			label: __("Include Credit Sales"),
			fieldtype: "Check",
			default: 1,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.type === "Credit Sale") {
			value = `<span style="color: var(--text-muted);">${value}</span>`;
		} else if (data && data.type === "Expense") {
			value = `<span style="color: #e74c3c;">${value}</span>`;
		}
		return value;
	},
};

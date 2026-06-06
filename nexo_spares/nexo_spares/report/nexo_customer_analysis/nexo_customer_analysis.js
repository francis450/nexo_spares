frappe.query_reports["Nexo Customer Analysis"] = {
	filters: [
		{
			fieldname: "report_type",
			label: __("Report Type"),
			fieldtype: "Select",
			options: "Top Customers\nDebt Ageing",
			default: "Top Customers",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			depends_on: "eval:doc.report_type === 'Top Customers'",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			depends_on: "eval:doc.report_type === 'Top Customers'",
		},
		{
			fieldname: "as_of_date",
			label: __("As of Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			depends_on: "eval:doc.report_type === 'Debt Ageing'",
		},
		{
			fieldname: "limit",
			label: __("Show Top N"),
			fieldtype: "Int",
			default: 50,
			depends_on: "eval:doc.report_type === 'Top Customers'",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldname === "outstanding" && parseFloat(data.outstanding || 0) > 0) {
			value = `<span style="color:#e74c3c;font-weight:600;">${value}</span>`;
		}
		if (column.fieldname === "age_91_plus" && parseFloat(data.age_91_plus || 0) > 0) {
			value = `<span style="color:#e74c3c;font-weight:600;">${value}</span>`;
		}
		return value;
	},
};

frappe.query_reports["Nexo Profit and Loss"] = {
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
			fieldname: "period",
			label: __("Group By"),
			fieldtype: "Select",
			options: "Daily\nWeekly\nMonthly",
			default: "Daily",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldname === "net_profit") {
			const num = data._net_profit_raw || 0;
			const color = num >= 0 ? "#27ae60" : "#e74c3c";
			value = `<span style="font-weight:600; color:${color};">${value}</span>`;
		}
		if (column.fieldname === "margin_pct" && data._net_profit_raw !== undefined) {
			const num = data._net_profit_raw || 0;
			const color = num >= 0 ? "#27ae60" : "#e74c3c";
			value = `<span style="color:${color};">${value}</span>`;
		}
		return value;
	},
};

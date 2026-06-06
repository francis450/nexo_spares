frappe.query_reports["Nexo Top Items"] = {
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
			fieldname: "sort_by",
			label: __("Rank By"),
			fieldtype: "Select",
			options: "Revenue\nGross Profit\nQTY Sold",
			default: "Revenue",
		},
		{
			fieldname: "limit",
			label: __("Show Top N"),
			fieldtype: "Int",
			default: 50,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldname === "margin_pct") {
			const num = parseFloat(data.margin_pct || 0);
			const color = num >= 20 ? "#27ae60" : num >= 0 ? "#e67e22" : "#e74c3c";
			value = `<span style="font-weight:600; color:${color};">${value}</span>`;
		}
		if (column.fieldname === "gross_profit") {
			const num = parseFloat(data.gross_profit || 0);
			if (num < 0) value = `<span style="color:#e74c3c;">${value}</span>`;
		}
		return value;
	},
};

frappe.query_reports["Nexo Slow Stock"] = {
	filters: [
		{
			fieldname: "slow_days",
			label: __("Slow After (days)"),
			fieldtype: "Int",
			default: 30,
			description: "Items with no sale in this many days are flagged as Slow",
		},
		{
			fieldname: "dead_days",
			label: __("Dead After (days)"),
			fieldtype: "Int",
			default: 90,
			description: "Items with no sale in this many days are flagged as Dead",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "status_filter",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDead\nSlow\nAll with Stock",
			default: "",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldname === "status") {
			if (data.status === "Dead") {
				value = `<span style="background:#e74c3c;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">Dead</span>`;
			} else if (data.status === "Slow") {
				value = `<span style="background:#e67e22;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">Slow</span>`;
			}
		}
		if (column.fieldname === "days_since_sale" && data.status === "Dead") {
			value = `<span style="color:#e74c3c;font-weight:600;">${value}</span>`;
		}
		return value;
	},
};

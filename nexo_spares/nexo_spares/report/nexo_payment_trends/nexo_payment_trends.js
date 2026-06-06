frappe.query_reports["Nexo Payment Trends"] = {
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
			default: "Weekly",
		},
	],
};

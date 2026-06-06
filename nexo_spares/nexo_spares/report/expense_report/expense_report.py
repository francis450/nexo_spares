import frappe
from frappe import _
from frappe.utils import fmt_money


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	message = get_summary_html(data)
	return columns, data, message


def get_columns():
	return [
		{
			"label": _("Type"),
			"fieldname": "type",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Reference Name"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Expense Entry",
			"width": 180,
		},
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Datetime",
			"width": 160,
		},
		{
			"label": _("Expense Category"),
			"fieldname": "expense_category",
			"fieldtype": "Link",
			"options": "Expense Category",
			"width": 160,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Payment Mode"),
			"fieldname": "mode_of_payment",
			"fieldtype": "Link",
			"options": "Mode of Payment",
			"width": 140,
		},
	]


def get_data(filters):
	conditions = get_conditions(filters)

	data = frappe.db.sql(
		f"""
		SELECT
			'Expense Entry' AS type,
			name,
			posting_date,
			expense_category,
			amount,
			mode_of_payment
		FROM
			`tabExpense Entry`
		WHERE
			docstatus = 1
			{conditions}
		ORDER BY
			posting_date DESC
		""",
		filters,
		as_dict=1,
	)

	return data


def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " AND DATE(posting_date) >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " AND DATE(posting_date) <= %(to_date)s"

	if filters.get("expense_category"):
		conditions += " AND expense_category = %(expense_category)s"

	if filters.get("mode_of_payment"):
		conditions += " AND mode_of_payment = %(mode_of_payment)s"

	return conditions


def get_summary_html(data):
	if not data:
		return ""

	currency = frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency") or "KES"

	total = sum(row.get("amount") or 0 for row in data)

	# per-category totals
	category_totals = {}
	for row in data:
		cat = row.get("expense_category") or "Uncategorized"
		category_totals[cat] = category_totals.get(cat, 0) + (row.get("amount") or 0)

	def money(val):
		return fmt_money(val, currency=currency)

	# Build summary cards
	cards_html = f"""
		<div style="display:flex; flex-wrap:wrap; gap:16px; padding:16px 0;">
			<div style="min-width:160px; text-align:center;">
				<div style="font-size:13px; color:#8D99A6; margin-bottom:4px;">Total Expenses</div>
				<div style="font-size:20px; font-weight:600; color:#e74c3c;">{money(total)}</div>
			</div>
	"""

	for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1]):
		cards_html += f"""
			<div style="min-width:160px; text-align:center;">
				<div style="font-size:13px; color:#8D99A6; margin-bottom:4px;">{cat}</div>
				<div style="font-size:20px; font-weight:600; color:#1f272e;">{money(amt)}</div>
			</div>
		"""

	cards_html += "</div>"
	return cards_html

import frappe
from frappe import _
from frappe.utils import fmt_money


def execute(filters=None):
	filters = filters or {}
	_set_defaults(filters)
	columns = get_columns()
	data = get_data(filters)
	message = build_summary(data, filters)
	return columns, data, message


def _set_defaults(filters):
	if not filters.get("from_date"):
		filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
	if not filters.get("to_date"):
		filters["to_date"] = frappe.utils.nowdate()


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

def get_columns():
	return [
		{
			"label": _("Type"),
			"fieldname": "type",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Reference"),
			"fieldname": "name",
			"fieldtype": "Dynamic Link",
			"options": "doctype_ref",
			"width": 190,
		},
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Customer / Category"),
			"fieldname": "party",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Mode of Payment"),
			"fieldname": "mode_of_payment",
			"fieldtype": "Link",
			"options": "Mode of Payment",
			"width": 150,
		},
		{
			"label": _("Sales / Receipt (KES)"),
			"fieldname": "inflow",
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"label": _("Expense (KES)"),
			"fieldname": "outflow",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def get_data(filters):
	rows = []
	rows += _get_pos_sales(filters)
	rows += _get_payment_entries(filters)
	if filters.get("include_credit_sales"):
		rows += _get_credit_sales(filters)
	rows += _get_expenses(filters)
	rows.sort(key=lambda r: (str(r.get("posting_date") or ""), r.get("type") or ""))
	return rows


def _mode_condition(filters, alias=""):
	"""Returns an extra AND clause when mode_of_payment filter is set."""
	col = f"{alias}.mode_of_payment" if alias else "mode_of_payment"
	if filters.get("mode_of_payment"):
		return f" AND {col} = %(mode_of_payment)s"
	return ""


def _get_pos_sales(filters):
	mode_cond = _mode_condition(filters, "sip")
	return frappe.db.sql(
		f"""
		SELECT
			'POS Sale'            AS type,
			si.name               AS name,
			'Sales Invoice'       AS doctype_ref,
			si.posting_date       AS posting_date,
			si.customer           AS party,
			sip.mode_of_payment   AS mode_of_payment,
			sip.amount            AS inflow,
			0                     AS outflow
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
		WHERE si.docstatus = 1
		  AND si.is_pos = 1
		  AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		  {mode_cond}
		ORDER BY si.posting_date, si.name
		""",
		filters,
		as_dict=True,
	)


def _get_payment_entries(filters):
	mode_cond = _mode_condition(filters, "pe")
	return frappe.db.sql(
		f"""
		SELECT
			'Payment Received'    AS type,
			pe.name               AS name,
			'Payment Entry'       AS doctype_ref,
			pe.posting_date       AS posting_date,
			pe.party              AS party,
			pe.mode_of_payment    AS mode_of_payment,
			pe.paid_amount        AS inflow,
			0                     AS outflow
		FROM `tabPayment Entry` pe
		WHERE pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		  AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
		  {mode_cond}
		ORDER BY pe.posting_date, pe.name
		""",
		filters,
		as_dict=True,
	)


def _get_credit_sales(filters):
	# Credit sales: no immediate cash impact — shown for informational context only.
	# mode_of_payment filter does not apply here (credit invoices have no payment mode).
	if filters.get("mode_of_payment"):
		return []
	return frappe.db.sql(
		"""
		SELECT
			'Credit Sale'         AS type,
			si.name               AS name,
			'Sales Invoice'       AS doctype_ref,
			si.posting_date       AS posting_date,
			si.customer           AS party,
			'Credit'              AS mode_of_payment,
			0                     AS inflow,
			0                     AS outflow,
			si.grand_total        AS credit_amount,
			si.outstanding_amount AS outstanding_amount
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		  AND si.is_pos = 0
		  AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY si.posting_date, si.name
		""",
		filters,
		as_dict=True,
	)


def _get_expenses(filters):
	mode_cond = _mode_condition(filters, "ee")
	return frappe.db.sql(
		f"""
		SELECT
			'Expense'             AS type,
			ee.name               AS name,
			'Expense Entry'       AS doctype_ref,
			DATE(ee.posting_date) AS posting_date,
			ee.expense_category   AS party,
			ee.mode_of_payment    AS mode_of_payment,
			0                     AS inflow,
			ee.amount             AS outflow
		FROM `tabExpense Entry` ee
		WHERE ee.docstatus = 1
		  AND DATE(ee.posting_date) BETWEEN %(from_date)s AND %(to_date)s
		  {mode_cond}
		ORDER BY ee.posting_date, ee.name
		""",
		filters,
		as_dict=True,
	)


# ---------------------------------------------------------------------------
# Summary HTML
# ---------------------------------------------------------------------------

def build_summary(rows, filters):
	currency = (
		frappe.get_cached_value(
			"Company",
			frappe.defaults.get_user_default("Company"),
			"default_currency",
		)
		or "KES"
	)

	def money(val):
		return fmt_money(val or 0, currency=currency)

	# Aggregate per mode (exclude Credit Sale rows from cash totals)
	mode_totals = {}
	credit_rows = []

	for row in rows:
		if row.get("type") == "Credit Sale":
			credit_rows.append(row)
			continue
		mode = row.get("mode_of_payment") or "Unknown"
		if mode not in mode_totals:
			mode_totals[mode] = {"inflow": 0, "outflow": 0}
		mode_totals[mode]["inflow"] += row.get("inflow") or 0
		mode_totals[mode]["outflow"] += row.get("outflow") or 0

	if not mode_totals and not credit_rows:
		return ""

	grand_in = sum(v["inflow"] for v in mode_totals.values())
	grand_out = sum(v["outflow"] for v in mode_totals.values())
	grand_bal = grand_in - grand_out

	# Build mode rows
	mode_rows_html = ""
	for mode, totals in sorted(mode_totals.items()):
		balance = totals["inflow"] - totals["outflow"]
		bal_color = "#27ae60" if balance >= 0 else "#e74c3c"
		mode_rows_html += f"""
			<tr>
				<td style="padding:8px 12px;">{mode}</td>
				<td style="padding:8px 12px; text-align:right; color:#2563eb;">{money(totals['inflow'])}</td>
				<td style="padding:8px 12px; text-align:right; color:#e74c3c;">{money(totals['outflow'])}</td>
				<td style="padding:8px 12px; text-align:right; font-weight:600; color:{bal_color};">{money(balance)}</td>
			</tr>"""

	bal_color_grand = "#27ae60" if grand_bal >= 0 else "#e74c3c"

	# Credit sales footer
	credit_html = ""
	if credit_rows:
		credit_total = sum(r.get("credit_amount") or 0 for r in credit_rows)
		credit_outstanding = sum(r.get("outstanding_amount") or 0 for r in credit_rows)
		credit_html = f"""
		<div style="margin-top:12px; padding:10px 14px; background:var(--subtle-fg); border-radius:4px; font-size:13px; color:var(--text-muted);">
			<strong>Credit Sales (not yet reflected in cash balance):</strong>
			{len(credit_rows)} invoice(s) totalling {money(credit_total)}
			&mdash; outstanding: <span style="color:#e74c3c; font-weight:600;">{money(credit_outstanding)}</span>
		</div>"""

	html = f"""
	<div style="padding:16px 0;">
		<div style="
			background: var(--card-bg);
			border-radius: 6px;
			box-shadow: var(--card-shadow);
			overflow: hidden;
			max-width: 680px;
		">
			<div style="
				padding: 12px 16px;
				border-bottom: 1px solid var(--border-color);
				font-weight: 600;
				font-size: 14px;
			">
				{_("Sales &amp; Expense Summary")}
				<span style="font-weight:400; color:var(--text-muted); font-size:12px; margin-left:8px;">
					{filters.get('from_date')} &mdash; {filters.get('to_date')}
				</span>
			</div>
			<table style="width:100%; border-collapse:collapse;">
				<thead style="background:var(--subtle-fg); font-size:12px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-muted);">
					<tr>
						<th style="padding:8px 12px; text-align:left;">{_("Mode of Payment")}</th>
						<th style="padding:8px 12px; text-align:right;">{_("Total Sales")}</th>
						<th style="padding:8px 12px; text-align:right;">{_("Total Expenses")}</th>
						<th style="padding:8px 12px; text-align:right;">{_("Net Balance")}</th>
					</tr>
				</thead>
				<tbody>
					{mode_rows_html}
				</tbody>
				<tfoot style="border-top: 2px solid var(--border-color); font-weight:700; font-size:14px;">
					<tr>
						<td style="padding:10px 12px;">{_("TOTAL")}</td>
						<td style="padding:10px 12px; text-align:right; color:#2563eb;">{money(grand_in)}</td>
						<td style="padding:10px 12px; text-align:right; color:#e74c3c;">{money(grand_out)}</td>
						<td style="padding:10px 12px; text-align:right; color:{bal_color_grand};">{money(grand_bal)}</td>
					</tr>
				</tfoot>
			</table>
		</div>
		{credit_html}
	</div>"""

	return html

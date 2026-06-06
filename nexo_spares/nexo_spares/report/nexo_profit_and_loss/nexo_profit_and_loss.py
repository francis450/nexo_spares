import frappe
from frappe import _
from frappe.utils import fmt_money, flt


def execute(filters=None):
    filters = filters or {}
    if not filters.get("from_date"):
        filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not filters.get("to_date"):
        filters["to_date"] = frappe.utils.nowdate()
    period = filters.get("period") or "Daily"

    columns = _get_columns()
    sales_rows = _get_sales(filters, period)
    expense_rows = _get_expenses(filters, period)

    # Merge by period key
    keys = sorted(set(list(sales_rows.keys()) + list(expense_rows.keys())))
    data = []
    for key in keys:
        s = sales_rows.get(key, {})
        e = expense_rows.get(key, {})
        total_sales = flt(s.get("total_sales"))
        net_sales = flt(s.get("net_sales"))
        vat = flt(s.get("vat"))
        cogs = flt(s.get("cogs"))
        gross_profit = total_sales - cogs
        expenses = flt(e.get("expenses"))
        net_profit = gross_profit - expenses
        margin_pct = (net_profit / total_sales * 100) if total_sales else 0

        data.append({
            "period": str(s.get("period_label") or e.get("period_label") or key),
            "total_sales": total_sales,
            "net_sales": net_sales,
            "vat": vat,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": expenses,
            "net_profit": net_profit,
            "margin_pct": margin_pct,
            "_net_profit_raw": net_profit,
        })

    message = _build_summary(data, filters)
    return columns, data, message


def _period_expr(period):
    if period == "Monthly":
        return "DATE_FORMAT(si.posting_date, '%%Y-%%m')", "DATE_FORMAT(si.posting_date, '%%Y-%%m')"
    if period == "Weekly":
        return "YEARWEEK(si.posting_date, 1)", "MIN(DATE(si.posting_date))"
    return "DATE(si.posting_date)", "DATE(si.posting_date)"


def _get_sales(filters, period):
    key_expr, label_expr = _period_expr(period)
    rows = frappe.db.sql(
        f"""
        SELECT
            {key_expr}                               AS period_key,
            {label_expr}                             AS period_label,
            COALESCE(SUM(si.grand_total), 0)         AS total_sales,
            COALESCE(SUM(si.net_total), 0)           AS net_sales,
            COALESCE(SUM(si.total_taxes_and_charges), 0) AS vat,
            COALESCE(SUM(sii.stock_qty * sii.incoming_rate), 0) AS cogs
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY {key_expr}
        ORDER BY {key_expr}
        """,
        filters,
        as_dict=True,
    )
    return {str(r.period_key): r for r in rows}


def _get_expenses(filters, period):
    if period == "Monthly":
        key_expr = "DATE_FORMAT(DATE(ee.posting_date), '%%Y-%%m')"
        label_expr = "DATE_FORMAT(DATE(ee.posting_date), '%%Y-%%m')"
    elif period == "Weekly":
        key_expr = "YEARWEEK(DATE(ee.posting_date), 1)"
        label_expr = "MIN(DATE(ee.posting_date))"
    else:
        key_expr = "DATE(ee.posting_date)"
        label_expr = "DATE(ee.posting_date)"

    rows = frappe.db.sql(
        f"""
        SELECT
            {key_expr}                      AS period_key,
            {label_expr}                    AS period_label,
            COALESCE(SUM(ee.amount), 0)     AS expenses
        FROM `tabExpense Entry` ee
        WHERE ee.docstatus = 1
          AND DATE(ee.posting_date) BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY {key_expr}
        ORDER BY {key_expr}
        """,
        filters,
        as_dict=True,
    )
    return {str(r.period_key): r for r in rows}


def _get_columns():
    return [
        {"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 120},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Net Sales (ex-VAT)"), "fieldname": "net_sales", "fieldtype": "Currency", "width": 150},
        {"label": _("VAT"), "fieldname": "vat", "fieldtype": "Currency", "width": 110},
        {"label": _("Cost of Goods"), "fieldname": "cogs", "fieldtype": "Currency", "width": 130},
        {"label": _("Gross Profit"), "fieldname": "gross_profit", "fieldtype": "Currency", "width": 130},
        {"label": _("Expenses"), "fieldname": "expenses", "fieldtype": "Currency", "width": 120},
        {"label": _("Net Profit"), "fieldname": "net_profit", "fieldtype": "Currency", "width": 120},
        {"label": _("Net Margin %"), "fieldname": "margin_pct", "fieldtype": "Percent", "width": 120},
    ]


def _build_summary(data, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    total_sales = sum(flt(r["total_sales"]) for r in data)
    net_sales = sum(flt(r["net_sales"]) for r in data)
    vat = sum(flt(r["vat"]) for r in data)
    cogs = sum(flt(r["cogs"]) for r in data)
    gross_profit = sum(flt(r["gross_profit"]) for r in data)
    expenses = sum(flt(r["expenses"]) for r in data)
    net_profit = sum(flt(r["net_profit"]) for r in data)
    margin_pct = (net_profit / total_sales * 100) if total_sales else 0
    profit_color = "#27ae60" if net_profit >= 0 else "#e74c3c"

    def card(label, value, color="#2563eb", sub=None):
        sub_html = f'<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{sub}</div>' if sub else ""
        return f"""
        <div style="background:var(--card-bg);border-radius:6px;box-shadow:var(--card-shadow);
                    padding:14px 18px;flex:1;min-width:140px;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);">{label}</div>
          <div style="font-size:18px;font-weight:700;color:{color};margin-top:4px;">{value}</div>
          {sub_html}
        </div>"""

    cards = (
        card("Total Sales", money(total_sales), sub=f"VAT: {money(vat)}")
        + card("Gross Profit", money(gross_profit), "#27ae60" if gross_profit >= 0 else "#e74c3c",
               sub=f"COGS: {money(cogs)}")
        + card("Expenses", money(expenses), "#e67e22")
        + card("Net Profit", money(net_profit), profit_color, sub=f"Margin: {margin_pct:.1f}%")
    )

    return f"""
    <div style="padding:16px 0;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div>
      <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">
        {filters.get('from_date')} &mdash; {filters.get('to_date')}
        &nbsp;·&nbsp; Net Sales (ex-VAT): {money(net_sales)}
      </div>
    </div>"""

import frappe
from frappe import _
from frappe.utils import fmt_money, flt


def execute(filters=None):
    filters = filters or {}
    if not filters.get("from_date"):
        filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not filters.get("to_date"):
        filters["to_date"] = frappe.utils.nowdate()
    period = filters.get("period") or "Weekly"

    sales_map = _get_sales(filters, period)
    expense_map = _get_expenses(filters, period)

    keys = sorted(set(list(sales_map.keys()) + list(expense_map.keys())))
    data = []
    for key in keys:
        s = sales_map.get(key, {})
        e = expense_map.get(key, {})
        sales = flt(s.get("sales"))
        expenses = flt(e.get("expenses"))
        net_balance = sales - expenses
        expense_ratio = (expenses / sales * 100) if sales else 0
        data.append({
            "period": str(s.get("period_label") or e.get("period_label") or key),
            "sales": sales,
            "expenses": expenses,
            "net_balance": net_balance,
            "expense_ratio": expense_ratio,
            "_net_balance_raw": net_balance,
        })

    columns = _get_columns()
    message = _build_summary(data, filters)
    return columns, data, message


def _period_exprs(period, table_alias):
    if period == "Monthly":
        return (
            f"DATE_FORMAT({table_alias}.posting_date, '%%Y-%%m')",
            f"DATE_FORMAT({table_alias}.posting_date, '%%Y-%%m')",
        )
    if period == "Weekly":
        return (
            f"YEARWEEK({table_alias}.posting_date, 1)",
            f"MIN(DATE({table_alias}.posting_date))",
        )
    return (
        f"DATE({table_alias}.posting_date)",
        f"DATE({table_alias}.posting_date)",
    )


def _get_sales(filters, period):
    key_expr, label_expr = _period_exprs(period, "si")
    rows = frappe.db.sql(
        f"""
        SELECT
            {key_expr}                          AS period_key,
            {label_expr}                        AS period_label,
            COALESCE(SUM(si.grand_total), 0)    AS sales
        FROM `tabSales Invoice` si
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
        {"label": _("Total Sales"), "fieldname": "sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Expenses"), "fieldname": "expenses", "fieldtype": "Currency", "width": 130},
        {"label": _("Net Balance"), "fieldname": "net_balance", "fieldtype": "Currency", "width": 130},
        {"label": _("Expense Ratio %"), "fieldname": "expense_ratio", "fieldtype": "Percent", "width": 130},
    ]


def _build_summary(data, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    total_sales = sum(flt(r["sales"]) for r in data)
    total_expenses = sum(flt(r["expenses"]) for r in data)
    net_balance = total_sales - total_expenses
    avg_ratio = (total_expenses / total_sales * 100) if total_sales else 0
    periods_with_loss = sum(1 for r in data if flt(r["_net_balance_raw"]) < 0)

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
        card("Total Sales", money(total_sales))
        + card("Total Expenses", money(total_expenses), "#e67e22")
        + card("Net Balance", money(net_balance), "#27ae60" if net_balance >= 0 else "#e74c3c")
        + card("Avg Expense Ratio", f"{avg_ratio:.1f}%",
               "#27ae60" if avg_ratio <= 20 else "#e67e22" if avg_ratio <= 40 else "#e74c3c",
               sub=f"{periods_with_loss} period(s) with loss" if periods_with_loss else "No loss periods")
    )

    return f'<div style="padding:16px 0;"><div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div></div>'

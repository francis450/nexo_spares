import frappe
from frappe import _
from frappe.utils import fmt_money, flt, cint, nowdate, date_diff


def execute(filters=None):
    filters = filters or {}
    report_type = filters.get("report_type") or "Top Customers"

    if report_type == "Debt Ageing":
        return _debt_ageing(filters)
    return _top_customers(filters)


# ---------------------------------------------------------------------------
# Top Customers
# ---------------------------------------------------------------------------

def _top_customers(filters):
    if not filters.get("from_date"):
        filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not filters.get("to_date"):
        filters["to_date"] = frappe.utils.nowdate()
    limit = cint(filters.get("limit") or 50) or 50

    rows = frappe.db.sql(
        """
        SELECT
            si.customer,
            si.customer_name,
            COUNT(DISTINCT si.name)             AS invoice_count,
            COALESCE(SUM(si.grand_total), 0)    AS total_sales,
            COALESCE(SUM(si.outstanding_amount), 0) AS outstanding,
            MAX(si.posting_date)                AS last_purchase
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY si.customer, si.customer_name
        ORDER BY total_sales DESC
        LIMIT %(limit)s
        """,
        {**filters, "limit": limit},
        as_dict=True,
    )

    columns = [
        {"label": _("#"), "fieldname": "rank", "fieldtype": "Int", "width": 55},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": _("Invoices"), "fieldname": "invoice_count", "fieldtype": "Int", "width": 90},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Outstanding"), "fieldname": "outstanding", "fieldtype": "Currency", "width": 130},
        {"label": _("Last Purchase"), "fieldname": "last_purchase", "fieldtype": "Date", "width": 120},
    ]

    data = []
    for rank, row in enumerate(rows, 1):
        data.append({
            "rank": rank,
            "customer": row.customer,
            "customer_name": row.customer_name,
            "invoice_count": cint(row.invoice_count),
            "total_sales": flt(row.total_sales),
            "outstanding": flt(row.outstanding),
            "last_purchase": row.last_purchase,
        })

    message = _top_summary(data, filters)
    return columns, data, message


def _top_summary(data, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    total_sales = sum(flt(r["total_sales"]) for r in data)
    total_outstanding = sum(flt(r["outstanding"]) for r in data)
    customers_with_debt = sum(1 for r in data if flt(r["outstanding"]) > 0)

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
        card("Customers", str(len(data)), "#555")
        + card("Total Sales", money(total_sales))
        + card("Outstanding Debt", money(total_outstanding), "#e74c3c" if total_outstanding > 0 else "#27ae60",
               sub=f"{customers_with_debt} customers with debt")
    )
    return f'<div style="padding:16px 0;"><div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div></div>'


# ---------------------------------------------------------------------------
# Debt Ageing
# ---------------------------------------------------------------------------

def _debt_ageing(filters):
    as_of = filters.get("as_of_date") or nowdate()

    rows = frappe.db.sql(
        """
        SELECT
            si.customer,
            si.customer_name,
            si.name                 AS invoice,
            si.posting_date,
            si.due_date,
            si.grand_total,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.outstanding_amount > 0
          AND si.posting_date <= %(as_of)s
        ORDER BY si.customer, si.posting_date
        """,
        {"as_of": as_of},
        as_dict=True,
    )

    # Bucket per customer
    customers = {}
    for row in rows:
        c = row.customer
        if c not in customers:
            customers[c] = {
                "customer": c,
                "customer_name": row.customer_name,
                "total": 0,
                "age_0_30": 0,
                "age_31_60": 0,
                "age_61_90": 0,
                "age_91_plus": 0,
            }
        age = date_diff(as_of, str(row.posting_date))
        amt = flt(row.outstanding_amount)
        customers[c]["total"] += amt
        if age <= 30:
            customers[c]["age_0_30"] += amt
        elif age <= 60:
            customers[c]["age_31_60"] += amt
        elif age <= 90:
            customers[c]["age_61_90"] += amt
        else:
            customers[c]["age_91_plus"] += amt

    data = sorted(customers.values(), key=lambda r: -r["total"])

    columns = [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": _("Total Outstanding"), "fieldname": "total", "fieldtype": "Currency", "width": 150},
        {"label": _("0-30 Days"), "fieldname": "age_0_30", "fieldtype": "Currency", "width": 120},
        {"label": _("31-60 Days"), "fieldname": "age_31_60", "fieldtype": "Currency", "width": 120},
        {"label": _("61-90 Days"), "fieldname": "age_61_90", "fieldtype": "Currency", "width": 120},
        {"label": _(">90 Days"), "fieldname": "age_91_plus", "fieldtype": "Currency", "width": 120},
    ]

    message = _ageing_summary(data, as_of)
    return columns, data, message


def _ageing_summary(data, as_of):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    total = sum(flt(r["total"]) for r in data)
    overdue_91 = sum(flt(r["age_91_plus"]) for r in data)

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
        card("Customers with Debt", str(len(data)), "#555")
        + card("Total Outstanding", money(total), "#e74c3c" if total > 0 else "#27ae60")
        + card(">90 Days Overdue", money(overdue_91), "#e74c3c" if overdue_91 > 0 else "#27ae60",
               sub="Requires urgent follow-up")
    )

    return f"""
    <div style="padding:16px 0;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div>
      <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">As of {as_of}</div>
    </div>"""

import frappe
from frappe import _
from frappe.utils import fmt_money, flt, cint


def execute(filters=None):
    filters = filters or {}
    if not filters.get("from_date"):
        filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not filters.get("to_date"):
        filters["to_date"] = frappe.utils.nowdate()

    sort_by = filters.get("sort_by") or "Revenue"
    limit = cint(filters.get("limit") or 50) or 50

    sort_col = {"Revenue": "revenue", "Gross Profit": "gross_profit", "QTY Sold": "qty_sold"}.get(sort_by, "revenue")

    rows = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            MAX(sii.item_name)                               AS item_name,
            COALESCE(SUM(sii.qty), 0)                        AS qty_sold,
            COALESCE(SUM(sii.base_amount), 0)                AS revenue,
            COALESCE(SUM(sii.stock_qty * sii.incoming_rate), 0) AS cogs,
            COALESCE(SUM(sii.base_amount - sii.stock_qty * sii.incoming_rate), 0) AS gross_profit
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY sii.item_code
        ORDER BY {sort_col} DESC
        LIMIT %(limit)s
        """,
        {**filters, "limit": limit},
        as_dict=True,
    )

    columns = _get_columns()
    data = []
    for rank, row in enumerate(rows, 1):
        revenue = flt(row.revenue)
        margin_pct = (flt(row.gross_profit) / revenue * 100) if revenue else 0
        data.append({
            "rank": rank,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "qty_sold": flt(row.qty_sold),
            "revenue": revenue,
            "cogs": flt(row.cogs),
            "gross_profit": flt(row.gross_profit),
            "margin_pct": margin_pct,
        })

    message = _build_summary(data, filters)
    return columns, data, message


def _get_columns():
    return [
        {"label": _("#"), "fieldname": "rank", "fieldtype": "Int", "width": 55},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": _("QTY Sold"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 100},
        {"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
        {"label": _("Cost of Goods"), "fieldname": "cogs", "fieldtype": "Currency", "width": 130},
        {"label": _("Gross Profit"), "fieldname": "gross_profit", "fieldtype": "Currency", "width": 130},
        {"label": _("Margin %"), "fieldname": "margin_pct", "fieldtype": "Percent", "width": 110},
    ]


def _build_summary(data, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    total_revenue = sum(flt(r["revenue"]) for r in data)
    total_cogs = sum(flt(r["cogs"]) for r in data)
    total_profit = sum(flt(r["gross_profit"]) for r in data)
    avg_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    profit_color = "#27ae60" if total_profit >= 0 else "#e74c3c"

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
        card("Items Shown", str(len(data)), "#555")
        + card("Total Revenue", money(total_revenue))
        + card("Total COGS", money(total_cogs), "#e67e22")
        + card("Gross Profit", money(total_profit), profit_color, sub=f"Avg margin: {avg_margin:.1f}%")
    )

    return f'<div style="padding:16px 0;"><div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div></div>'

import frappe
from frappe import _
from frappe.utils import fmt_money, flt, cint, nowdate, date_diff


def execute(filters=None):
    filters = filters or {}
    slow_days = cint(filters.get("slow_days") or 30)
    dead_days = cint(filters.get("dead_days") or 90)
    warehouse = filters.get("warehouse")
    status_filter = filters.get("status_filter") or ""
    today = nowdate()

    warehouse_bin = "AND bin.warehouse = %(warehouse)s" if warehouse else ""
    warehouse_params = {"warehouse": warehouse} if warehouse else {}

    # Items with positive stock + their last sale date
    rows = frappe.db.sql(
        f"""
        SELECT
            item.name                                       AS item_code,
            item.item_name,
            item.stock_uom,
            COALESCE(SUM(bin.actual_qty), 0)               AS actual_qty,
            COALESCE(
                SUM(bin.stock_value) / NULLIF(SUM(bin.actual_qty), 0),
                item.valuation_rate, 0
            )                                               AS valuation_rate,
            COALESCE(SUM(bin.stock_value), 0)              AS stock_value,
            (
                SELECT MAX(si.posting_date)
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                WHERE sii.item_code = item.name
                  AND si.docstatus = 1
            )                                               AS last_sale_date,
            (
                SELECT ip.price_list_rate
                FROM `tabItem Price` ip
                WHERE ip.item_code = item.name
                  AND ip.selling = 1
                ORDER BY ip.modified DESC
                LIMIT 1
            )                                               AS selling_price
        FROM `tabItem` item
        LEFT JOIN `tabBin` bin ON bin.item_code = item.name {warehouse_bin}
        WHERE item.disabled = 0
          AND item.is_stock_item = 1
        GROUP BY item.name, item.item_name, item.stock_uom, item.valuation_rate
        HAVING actual_qty > 0
        ORDER BY last_sale_date ASC, stock_value DESC
        """,
        warehouse_params,
        as_dict=True,
    )

    columns = _get_columns()
    data = []
    for row in rows:
        last_sale = row.last_sale_date
        if last_sale:
            days_since = date_diff(today, str(last_sale))
        else:
            days_since = 9999  # Never sold

        if days_since >= dead_days:
            status = "Dead"
        elif days_since >= slow_days:
            status = "Slow"
        else:
            continue  # Moving fine — skip

        if status_filter and status_filter != status:
            if not (status_filter == "All with Stock"):
                continue

        data.append({
            "item_code": row.item_code,
            "item_name": row.item_name,
            "actual_qty": flt(row.actual_qty),
            "stock_uom": row.stock_uom,
            "valuation_rate": flt(row.valuation_rate),
            "stock_value": flt(row.stock_value),
            "selling_price": flt(row.selling_price),
            "last_sale_date": str(last_sale) if last_sale else "Never",
            "days_since_sale": days_since if days_since < 9999 else None,
            "status": status,
        })

    message = _build_summary(data, filters)
    return columns, data, message


def _get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": _("Days Since Sale"), "fieldname": "days_since_sale", "fieldtype": "Int", "width": 130},
        {"label": _("Last Sale Date"), "fieldname": "last_sale_date", "fieldtype": "Data", "width": 120},
        {"label": _("QTY in Stock"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 110},
        {"label": _("UOM"), "fieldname": "stock_uom", "fieldtype": "Data", "width": 70},
        {"label": _("Cost / Unit"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 130},
        {"label": _("Selling Price"), "fieldname": "selling_price", "fieldtype": "Currency", "width": 120},
    ]


def _build_summary(data, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    dead = [r for r in data if r["status"] == "Dead"]
    slow = [r for r in data if r["status"] == "Slow"]
    dead_value = sum(flt(r["stock_value"]) for r in dead)
    slow_value = sum(flt(r["stock_value"]) for r in slow)
    total_value = dead_value + slow_value

    def card(label, value, color, sub=None):
        sub_html = f'<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{sub}</div>' if sub else ""
        return f"""
        <div style="background:var(--card-bg);border-radius:6px;box-shadow:var(--card-shadow);
                    padding:14px 18px;flex:1;min-width:140px;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);">{label}</div>
          <div style="font-size:18px;font-weight:700;color:{color};margin-top:4px;">{value}</div>
          {sub_html}
        </div>"""

    cards = (
        card("Dead Items", str(len(dead)), "#e74c3c", sub=f"Value: {money(dead_value)}")
        + card("Slow Items", str(len(slow)), "#e67e22", sub=f"Value: {money(slow_value)}")
        + card("Total Idle Stock Value", money(total_value), "#8e44ad")
    )

    return f'<div style="padding:16px 0;"><div style="display:flex;gap:12px;flex-wrap:wrap;">{cards}</div></div>'

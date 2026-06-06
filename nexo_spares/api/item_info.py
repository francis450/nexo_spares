import frappe


@frappe.whitelist()
def get_item_hub(item_code):
    """
    Returns stock levels, cost, selling prices, and last 10 sales for an item.
    Called from the Item form client script (item_hub.js).
    """
    if not item_code:
        frappe.throw("item_code is required")

    stock_levels = frappe.db.sql(
        """
        SELECT warehouse, actual_qty, valuation_rate, stock_value
        FROM `tabBin`
        WHERE item_code = %s
          AND actual_qty != 0
        ORDER BY actual_qty DESC
        """,
        (item_code,),
        as_dict=True,
    )

    valuation_rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 0

    selling_prices = frappe.db.sql(
        """
        SELECT price_list, price_list_rate, currency
        FROM `tabItem Price`
        WHERE item_code = %s
          AND selling = 1
        ORDER BY price_list_rate DESC
        """,
        (item_code,),
        as_dict=True,
    )

    recent_sales = frappe.db.sql(
        """
        SELECT
            sii.parent     AS invoice,
            si.posting_date,
            sii.qty,
            sii.rate,
            sii.amount,
            si.customer
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.item_code = %s
          AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.creation DESC
        LIMIT 10
        """,
        (item_code,),
        as_dict=True,
    )

    return {
        "item_code": item_code,
        "stock_levels": stock_levels,
        "valuation_rate": float(valuation_rate),
        "selling_prices": selling_prices,
        "recent_sales": recent_sales,
    }

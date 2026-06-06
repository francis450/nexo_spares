import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def get_daily_summary(date=None):
    """
    Returns total POS sales and payment mode breakdown for a given date.
    POSAwesome stores sales in tabSales Invoice (is_pos=1), not tabPOS Invoice.
    """
    if not date:
        date = nowdate()

    summary = frappe.db.sql(
        """
        SELECT
            COUNT(name)      AS invoice_count,
            COALESCE(SUM(grand_total), 0) AS total_sales
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND is_pos = 1
          AND posting_date = %s
        """,
        (date,),
        as_dict=True,
    )[0]

    payment_breakdown = frappe.db.sql(
        """
        SELECT
            sip.mode_of_payment,
            COALESCE(SUM(sip.amount), 0) AS total_amount,
            COUNT(DISTINCT si.name)      AS tx_count
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
        WHERE si.docstatus = 1
          AND si.is_pos = 1
          AND si.posting_date = %s
        GROUP BY sip.mode_of_payment
        ORDER BY total_amount DESC
        """,
        (date,),
        as_dict=True,
    )

    return {
        "date": date,
        "invoice_count": int(summary.invoice_count or 0),
        "total_sales": float(summary.total_sales or 0),
        "payment_breakdown": payment_breakdown,
    }

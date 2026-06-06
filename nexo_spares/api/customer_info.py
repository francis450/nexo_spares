import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_customer_hub(customer):
    outstanding_invoices = frappe.db.sql("""
        SELECT name, posting_date, grand_total, outstanding_amount, status
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
        ORDER BY posting_date DESC
        LIMIT 20
    """, (customer,), as_dict=True)

    total_outstanding = sum(flt(r.outstanding_amount) for r in outstanding_invoices)

    recent_sales = frappe.db.sql("""
        SELECT name, posting_date, grand_total, outstanding_amount, status
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 15
    """, (customer,), as_dict=True)

    totals = frappe.db.sql("""
        SELECT SUM(grand_total) AS total_sales, COUNT(*) AS invoice_count
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1
    """, (customer,), as_dict=True)[0]

    return {
        "customer": customer,
        "total_outstanding": float(total_outstanding),
        "outstanding_invoices": outstanding_invoices,
        "recent_sales": recent_sales,
        "total_sales": float(totals.total_sales or 0),
        "invoice_count": int(totals.invoice_count or 0),
    }

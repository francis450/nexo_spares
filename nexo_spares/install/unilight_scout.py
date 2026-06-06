import frappe, openpyxl


def run():
	wb = openpyxl.load_workbook('/home/frappeuser/frappe-bench/UNILIGHT STOCK (1).xlsx')
	ws = wb.active
	rows = list(ws.iter_rows(values_only=True))
	# Items were imported using product_name as item_code in ERPNext
	product_names = [r[1] for r in rows[2:] if r[1]]
	print(f'Checking {len(product_names)} Unilight items (matched by product name)...\n')

	affected = frappe.db.sql("""
		SELECT DISTINCT si.name, si.posting_date, si.customer, si.grand_total, si.status
		FROM `tabSales Invoice` si
		JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE sii.item_code IN %(items)s
		  AND si.docstatus = 1
		  AND si.posting_date >= '2026-06-02'
		ORDER BY si.posting_date
	""", {'items': product_names}, as_dict=True)

	print(f'Affected submitted Sales Invoices: {len(affected)}\n')
	for inv in affected:
		line_items = frappe.db.sql("""
			SELECT item_code, item_name, qty, rate, amount
			FROM `tabSales Invoice Item`
			WHERE parent = %(parent)s AND item_code IN %(items)s
		""", {'parent': inv.name, 'items': product_names}, as_dict=True)

		payments = frappe.db.get_all('Payment Entry Reference',
			filters={'reference_name': inv.name, 'reference_doctype': 'Sales Invoice'},
			fields=['parent'])

		dns = frappe.db.get_all('Delivery Note Item',
			filters={'against_sales_invoice': inv.name},
			fields=['parent'], distinct=True)

		print(f"  {inv.name} | {inv.posting_date} | Customer: {inv.customer} | Total: {inv.grand_total}")
		print(f"    Linked Payments: {[p.parent for p in payments] or 'None'}")
		print(f"    Linked Delivery Notes: {[d.parent for d in dns] or 'None'}")
		for li in line_items:
			print(f"    Item: {li.item_code} | Qty: {li.qty} | Rate (wrong): {li.rate} | Amount: {li.amount}")
		print()

	if not affected:
		print('No affected invoices found — no sales have been made with these items yet.')

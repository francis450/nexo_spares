import frappe


def run():
	inv_name = 'ACC-SINV-2026-00066'
	si = frappe.get_doc('Sales Invoice', inv_name)

	print(f'Invoice: {si.name}')
	print(f'Date: {si.posting_date}')
	print(f'Customer: {si.customer}')
	print(f'Status: {si.status}')
	print(f'Grand Total: {si.grand_total}')
	print(f'Outstanding Amount: {si.outstanding_amount}')
	print()

	print('Line Items:')
	for item in si.items:
		print(f'  Item: {item.item_code}')
		print(f'  Qty: {item.qty}')
		print(f'  Rate charged: {item.rate}')
		print(f'  Amount: {item.amount}')
		# Get correct values from Excel
		correct_cost = frappe.db.get_value('Item', item.item_code, 'valuation_rate')
		correct_sell = frappe.db.get_value('Item Price', {
			'item_code': item.item_code, 'price_list': si.selling_price_list, 'selling': 1
		}, 'price_list_rate')
		print(f'  Correct cost (now): {correct_cost}')
		print(f'  Correct selling price (now): {correct_sell}')
		print()

	print('Stock Ledger entries for this invoice:')
	sle = frappe.db.sql("""
		SELECT item_code, actual_qty, valuation_rate, stock_value_difference, posting_date
		FROM `tabStock Ledger Entry`
		WHERE voucher_type = 'Sales Invoice' AND voucher_no = %s
	""", inv_name, as_dict=True)
	for s in sle:
		print(f'  {s.item_code} | Qty: {s.actual_qty} | Val Rate: {s.valuation_rate} | Stock diff: {s.stock_value_difference}')

	print()
	print('GL Entries for this invoice:')
	gle = frappe.db.sql("""
		SELECT account, debit, credit, remarks
		FROM `tabGL Entry`
		WHERE voucher_type = 'Sales Invoice' AND voucher_no = %s AND is_cancelled = 0
		LIMIT 10
	""", inv_name, as_dict=True)
	for g in gle:
		print(f'  {g.account} | Dr: {g.debit} | Cr: {g.credit}')

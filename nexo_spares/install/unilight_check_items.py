import frappe


def run():
	# Check items created on/after June 2, 2026
	recent_items = frappe.db.sql("""
		SELECT name, item_name, item_code, valuation_rate, standard_rate, creation
		FROM `tabItem`
		WHERE DATE(creation) >= '2026-06-02'
		ORDER BY creation
		LIMIT 30
	""", as_dict=True)

	print(f'Items created on/after 2026-06-02: {len(recent_items)}\n')
	for item in recent_items:
		print(f"  Code: {item.item_code} | Name: {item.item_name} | Cost: {item.valuation_rate} | Rate: {item.standard_rate} | Created: {item.creation}")

	print()

	# Also check Item Price records for these items
	if recent_items:
		item_codes = [i.item_code for i in recent_items]
		prices = frappe.db.sql("""
			SELECT item_code, price_list, price_list_rate, selling, buying
			FROM `tabItem Price`
			WHERE item_code IN %(codes)s
		""", {'codes': item_codes}, as_dict=True)
		print(f'Item Price records for these items: {len(prices)}')
		for p in prices:
			print(f"  {p.item_code} | {p.price_list} | Rate: {p.price_list_rate} | Selling: {p.selling} | Buying: {p.buying}")

	print()

	# Show total item count in system
	total = frappe.db.count('Item')
	print(f'Total items in system: {total}')

	# Check if any item code from Excel exists with a prefix/suffix
	sample_codes = ['TLS-FIEL01-L', 'TLS-NZE01-L', 'HLA-AE100-LH']
	print(f'\nSearching for sample codes from Excel:')
	for code in sample_codes:
		found = frappe.db.sql("""
			SELECT name, item_name FROM `tabItem`
			WHERE name LIKE %s OR item_code LIKE %s
			LIMIT 3
		""", (f'%{code}%', f'%{code}%'), as_dict=True)
		print(f"  '{code}': {found or 'NOT FOUND'}")

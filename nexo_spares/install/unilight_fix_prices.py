import frappe, openpyxl


def run():
	wb = openpyxl.load_workbook('/home/frappeuser/frappe-bench/UNILIGHT STOCK (1).xlsx')
	ws = wb.active
	rows = list(ws.iter_rows(values_only=True))
	# (item_code_in_excel, product_name, basic_rate, selling_price)
	items = [(r[0], r[1], r[3], r[4]) for r in rows[2:] if r[0]]

	price_list = frappe.db.get_single_value('Selling Settings', 'selling_price_list') or 'Standard Selling'
	print(f'Using price list: {price_list}')
	print(f'Processing {len(items)} items from Excel...\n')

	updated = created = skipped = warnings = 0

	for excel_code, product_name, basic_rate, selling_price in items:
		# Items were imported using Product Name as Item Code
		if not frappe.db.exists('Item', product_name):
			print(f'SKIP (not found in ERPNext): {excel_code} / "{product_name}"')
			skipped += 1
			continue

		if selling_price is None:
			print(f'WARNING (no selling price): {excel_code} / "{product_name}" — skipping price update')
			warnings += 1
			continue

		if selling_price < basic_rate:
			print(f'WARNING (selling < cost): {excel_code} / "{product_name}" | cost={basic_rate} sell={selling_price} — proceeding anyway')
			warnings += 1

		# Update valuation rate and standard rate on Item master
		frappe.db.set_value('Item', product_name, {
			'valuation_rate': basic_rate,
			'standard_rate': selling_price,
		})

		# Update or create Item Price for selling
		existing = frappe.db.get_value('Item Price',
			{'item_code': product_name, 'price_list': price_list, 'selling': 1}, 'name')
		if existing:
			frappe.db.set_value('Item Price', existing, 'price_list_rate', selling_price)
			print(f'UPDATED: "{product_name}" | cost={basic_rate} | selling={selling_price}')
			updated += 1
		else:
			doc = frappe.get_doc({
				'doctype': 'Item Price',
				'item_code': product_name,
				'price_list': price_list,
				'selling': 1,
				'price_list_rate': selling_price
			})
			doc.insert(ignore_permissions=True)
			print(f'CREATED: "{product_name}" | cost={basic_rate} | selling={selling_price}')
			created += 1

	frappe.db.commit()
	print(f'\n--- Done ---')
	print(f'Updated: {updated} | Created: {created} | Skipped (not found): {skipped} | Warnings: {warnings}')

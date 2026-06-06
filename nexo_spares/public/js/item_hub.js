// Nexo Auto Spares — Item form customization
// - Only two tabs: Details (simplified) and Stock & Sales
// - Stock & Sales shows only actual stock in hand, selling prices, and last 10 sales
// - Suppresses ERPNext's built-in projected/reserved indicators

frappe.ui.form.on("Item", {
	onload: function (frm) {
		// Suppress ERPNext's built-in item dashboard (projected, reserved, ordered qty widgets)
		// This must run before refresh so it never renders
		if (erpnext && erpnext.item) {
			erpnext.item.make_dashboard = function () {};
		}
	},

	refresh: function (frm) {
		nexo_item.hide_unused_tabs(frm);
		nexo_item.simplify_details_tab(frm);
		frm.set_df_property("valuation_rate", "label", "Landed Cost");
		frm.set_df_property("opening_stock", "label", "Opening Stock (Qty)");

		if (!frm.is_new()) {
			nexo_item.render_stock_sales(frm);
		} else {
			const $w = frm.fields_dict["nexo_item_snapshot"] &&
				frm.fields_dict["nexo_item_snapshot"].$wrapper;
			if ($w) $w.html(
				`<div class="text-muted text-center" style="padding:24px;">
					${__("Save the item first to see stock and sales data.")}
				</div>`
			);
		}
	},
});

frappe.provide("nexo_item");

// ── Tab Management ──────────────────────────────────────────────────────────

nexo_item.hide_unused_tabs = function (frm) {
	const keep = new Set(["details", "nexo_stock_sales_tab"]);

	if (!frm.layout || !frm.layout.tabs) return;

	frm.layout.tabs.forEach(function (tab) {
		const fn = tab.df && tab.df.fieldname;
		if (fn && !keep.has(fn)) {
			tab.df.hidden = true;   // persists across layout refreshes
			tab.toggle(false);
		}
	});
};

// ── Details Tab Simplification ──────────────────────────────────────────────

nexo_item.simplify_details_tab = function (frm) {
	const hide_fields = [
		// Series / status flags
		"naming_series",
		"disabled",
		"allow_alternative_item",
		"is_stock_item",        // all items are stock items here
		"has_variants",

		// Selling rate (shown in hub)
		"standard_rate",

		// Fixed asset (not relevant for a spares shop)
		"is_fixed_asset",
		"auto_create_assets",
		"is_grouped_asset",
		"asset_category",
		"asset_naming_series",

		// Tolerances
		"over_delivery_receipt_allowance",
		"over_billing_allowance",

		// Branding / physical properties
		"brand",
		"shelf_life_in_days",
		"end_of_life",
		"warranty_period",
		"weight_per_unit",
		"weight_uom",

		// Advanced inventory
		"default_material_request_type",
		"valuation_method",
		"allow_negative_stock",

		// UOM conversion table
		"unit_of_measure_conversion",   // section
		"uoms",
	];
	frm.toggle_display(hide_fields, false);
};

// ── Stock & Sales Tab Content ───────────────────────────────────────────────

nexo_item.render_stock_sales = function (frm) {
	const $wrapper = frm.fields_dict["nexo_item_snapshot"] &&
		frm.fields_dict["nexo_item_snapshot"].$wrapper;
	if (!$wrapper) return;

	$wrapper.html(
		`<div class="text-muted text-center" style="padding:24px;">${__("Loading...")}</div>`
	);

	frappe.call({
		method: "nexo_spares.api.item_info.get_item_hub",
		args: { item_code: frm.doc.name },
		callback: function (r) {
			if (!r.message) return;
			nexo_item._render_hub($wrapper, r.message);
		},
		error: function () {
			$wrapper.html(
				`<div class="text-muted text-center" style="padding:24px;">
					${__("Could not load stock and sales data.")}
				</div>`
			);
		},
	});
};

nexo_item._render_hub = function ($wrapper, d) {
	const currency = frappe.boot.sysdefaults.currency || "KES";
	const fmt = (v) => format_currency(parseFloat(v) || 0, currency);

	// ── Stock in Hand ──────────────────────────────────────────────────────
	const stock_rows = d.stock_levels.length
		? d.stock_levels
			.map(
				(s) => `
			<tr>
				<td>${s.warehouse}</td>
				<td class="text-right"><strong>${flt(s.actual_qty, 2)}</strong></td>
				<td class="text-right text-muted">${fmt(s.stock_value)}</td>
			</tr>`
			)
			.join("")
		: `<tr>
			<td colspan="3" class="text-muted text-center" style="padding:16px;">
				${__("No stock in any warehouse")}
			</td>
		</tr>`;

	// ── Selling Prices ─────────────────────────────────────────────────────
	const price_rows = d.selling_prices.length
		? d.selling_prices
			.map(
				(p) => `
			<tr>
				<td>${p.price_list}</td>
				<td class="text-right"><strong>${fmt(p.price_list_rate)}</strong></td>
			</tr>`
			)
			.join("")
		: `<tr>
			<td colspan="2" class="text-muted text-center" style="padding:16px;">
				${__("No selling price set")}
			</td>
		</tr>`;

	// ── Recent Sales ───────────────────────────────────────────────────────
	const sales_rows = d.recent_sales.length
		? d.recent_sales
			.map(
				(s) => `
			<tr>
				<td><a href="/app/sales-invoice/${s.invoice}">${s.invoice}</a></td>
				<td>${frappe.datetime.str_to_user(s.posting_date)}</td>
				<td class="text-right">${flt(s.qty, 2)}</td>
				<td class="text-right">${fmt(s.rate)}</td>
				<td class="text-right">${fmt(s.amount)}</td>
			</tr>`
			)
			.join("")
		: `<tr>
			<td colspan="5" class="text-muted text-center" style="padding:16px;">
				${__("No sales yet")}
			</td>
		</tr>`;

	const html = `
		<div style="padding:16px 4px;">

			<div style="margin-bottom:20px;">
				<span class="indicator blue" style="font-size:13px;">
					${__("Our Cost (Valuation Rate)")}:&nbsp;<strong>${fmt(d.valuation_rate)}</strong>
				</span>
			</div>

			<div class="row">
				<div class="col-md-5 col-sm-12" style="margin-bottom:20px;">
					<div style="font-weight:600;margin-bottom:8px;">${__("Stock in Hand")}</div>
					<table class="table table-condensed table-bordered" style="font-size:13px;margin:0;">
						<thead style="background:var(--subtle-fg);">
							<tr>
								<th>${__("Warehouse")}</th>
								<th class="text-right">${__("Qty")}</th>
								<th class="text-right">${__("Stock Value")}</th>
							</tr>
						</thead>
						<tbody>${stock_rows}</tbody>
					</table>
				</div>

				<div class="col-md-4 col-sm-12" style="margin-bottom:20px;">
					<div style="font-weight:600;margin-bottom:8px;">${__("Selling Prices")}</div>
					<table class="table table-condensed table-bordered" style="font-size:13px;margin:0;">
						<thead style="background:var(--subtle-fg);">
							<tr>
								<th>${__("Price List")}</th>
								<th class="text-right">${__("Rate")}</th>
							</tr>
						</thead>
						<tbody>${price_rows}</tbody>
					</table>
				</div>
			</div>

			<div>
				<div style="font-weight:600;margin-bottom:8px;">${__("Last 10 Sales")}</div>
				<table class="table table-condensed table-bordered" style="font-size:13px;margin:0;">
					<thead style="background:var(--subtle-fg);">
						<tr>
							<th>${__("Invoice")}</th>
							<th>${__("Date")}</th>
							<th class="text-right">${__("Qty")}</th>
							<th class="text-right">${__("Rate")}</th>
							<th class="text-right">${__("Amount")}</th>
						</tr>
					</thead>
					<tbody>${sales_rows}</tbody>
				</table>
			</div>

		</div>`;

	$wrapper.html(html);
};

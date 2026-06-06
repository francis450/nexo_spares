// Nexo Auto Spares — Customer form customization
// Two tabs: Details (name, type, group, territory, notes) + Address & Contact + Customer Hub

frappe.ui.form.on("Customer", {
	refresh: function (frm) {
		nexo_customer.hide_tabs(frm);
		nexo_customer.simplify_details(frm);

		if (!frm.is_new()) {
			nexo_customer.render_hub(frm);
		} else {
			const $w = frm.fields_dict["nexo_customer_snapshot"] &&
				frm.fields_dict["nexo_customer_snapshot"].$wrapper;
			if ($w) $w.html(
				`<div class="text-muted" style="padding:16px 0">
					${__("Save the customer to view debt and sales summary.")}
				</div>`
			);
		}
	},
});

frappe.provide("nexo_customer");

nexo_customer.hide_tabs = function (frm) {
	const keep = new Set(["contact_and_address_tab", "nexo_customer_tab"]);
	if (!frm.layout || !frm.layout.tabs) return;
	frm.layout.tabs.forEach(function (tab) {
		const fn = tab.df && tab.df.fieldname;
		if (fn && !keep.has(fn)) {
			tab.df.hidden = true;
			tab.toggle(false);
		}
	});
};

nexo_customer.simplify_details = function (frm) {
	const hide = [
		"naming_series",
		"salutation",
		"gender",
		"lead_name", "opportunity_name", "prospect_name",
		"account_manager",
		"image",
		// Defaults section
		"defaults_tab",
		"default_currency", "default_bank_account", "default_price_list",
		// Internal customer
		"internal_customer_section",
		"is_internal_customer", "represents_company", "companies",
		// More info
		"more_info",
		"market_segment", "industry", "customer_pos_id", "website", "language",
	];
	frm.toggle_display(hide, false);
};

nexo_customer.render_hub = function (frm) {
	const $w = frm.fields_dict["nexo_customer_snapshot"] &&
		frm.fields_dict["nexo_customer_snapshot"].$wrapper;
	if (!$w) return;

	$w.html(`<div class="text-muted" style="padding:14px 0">${__("Loading...")}</div>`);

	frappe.call({
		method: "nexo_spares.api.customer_info.get_customer_hub",
		args: { customer: frm.doc.name },
		callback: function (r) {
			if (r.message) nexo_customer._render($w, r.message);
		},
		error: function () {
			$w.html(
				`<div class="alert alert-danger" style="margin-top:8px">
					${__("Could not load customer summary.")}
				</div>`
			);
		},
	});
};

nexo_customer._render = function ($w, d) {
	const currency = frappe.boot.sysdefaults.currency || "KES";
	const fmt = (v) => format_currency(parseFloat(v) || 0, currency);
	const esc = frappe.utils.escape_html;

	// Outstanding invoices table
	const debt_rows = d.outstanding_invoices.length
		? d.outstanding_invoices.map((r) => {
			const badge = flt(r.outstanding_amount) >= flt(r.grand_total)
				? "red" : "orange";
			return `<tr>
				<td><a href="/app/sales-invoice/${esc(r.name)}">${esc(r.name)}</a></td>
				<td>${frappe.datetime.str_to_user(r.posting_date)}</td>
				<td class="text-right">${fmt(r.grand_total)}</td>
				<td class="text-right">
					<span class="indicator ${badge}">
						<strong>${fmt(r.outstanding_amount)}</strong>
					</span>
				</td>
			</tr>`;
		}).join("")
		: `<tr><td colspan="4" class="text-muted text-center" style="padding:16px;">
				${__("No outstanding invoices — all paid up!")}
			</td></tr>`;

	// Recent sales table
	const sales_rows = d.recent_sales.length
		? d.recent_sales.map((r) => `<tr>
			<td><a href="/app/sales-invoice/${esc(r.name)}">${esc(r.name)}</a></td>
			<td>${frappe.datetime.str_to_user(r.posting_date)}</td>
			<td class="text-right">${fmt(r.grand_total)}</td>
			<td><span class="indicator ${r.status === 'Paid' ? 'green' : r.outstanding_amount > 0 ? 'orange' : 'blue'}">${esc(r.status)}</span></td>
		</tr>`).join("")
		: `<tr><td colspan="4" class="text-muted text-center" style="padding:16px;">${__("No sales yet")}</td></tr>`;

	$w.html(`
		<div style="padding:8px 0 20px;">

			<div style="display:grid;grid-template-columns:repeat(3,minmax(140px,1fr));gap:12px;margin-bottom:20px;">
				<div style="border:1px solid var(--border-color);border-radius:8px;padding:14px;background:var(--fg-color);">
					<div style="color:var(--text-muted);font-size:12px;margin-bottom:6px;">${__("Total Sales")}</div>
					<div style="font-size:20px;font-weight:650;">${fmt(d.total_sales)}</div>
					<div style="color:var(--text-muted);font-size:12px;margin-top:4px;">${d.invoice_count} ${__("invoice(s)")}</div>
				</div>
				<div style="border:1px solid var(--border-color);border-radius:8px;padding:14px;background:var(--fg-color);">
					<div style="color:var(--text-muted);font-size:12px;margin-bottom:6px;">${__("Outstanding Debt")}</div>
					<div style="font-size:20px;font-weight:650;color:${d.total_outstanding > 0 ? 'var(--red)' : 'var(--green)'};">
						${fmt(d.total_outstanding)}
					</div>
					<div style="color:var(--text-muted);font-size:12px;margin-top:4px;">${d.outstanding_invoices.length} ${__("unpaid invoice(s)")}</div>
				</div>
				<div style="border:1px solid var(--border-color);border-radius:8px;padding:14px;background:var(--fg-color);">
					<div style="color:var(--text-muted);font-size:12px;margin-bottom:6px;">${__("Amount Paid")}</div>
					<div style="font-size:20px;font-weight:650;color:var(--green);">
						${fmt(d.total_sales - d.total_outstanding)}
					</div>
				</div>
			</div>

			${d.outstanding_invoices.length ? `
			<div style="margin-bottom:20px;">
				<div style="font-weight:600;margin-bottom:8px;">${__("Unpaid Invoices")}</div>
				<table class="table table-condensed table-bordered" style="font-size:13px;margin:0;">
					<thead style="background:var(--subtle-fg);">
						<tr>
							<th>${__("Invoice")}</th>
							<th>${__("Date")}</th>
							<th class="text-right">${__("Total")}</th>
							<th class="text-right">${__("Outstanding")}</th>
						</tr>
					</thead>
					<tbody>${debt_rows}</tbody>
				</table>
			</div>` : ""}

			<div>
				<div style="font-weight:600;margin-bottom:8px;">${__("Recent Sales")}</div>
				<table class="table table-condensed table-bordered" style="font-size:13px;margin:0;">
					<thead style="background:var(--subtle-fg);">
						<tr>
							<th>${__("Invoice")}</th>
							<th>${__("Date")}</th>
							<th class="text-right">${__("Amount")}</th>
							<th>${__("Status")}</th>
						</tr>
					</thead>
					<tbody>${sales_rows}</tbody>
				</table>
			</div>

		</div>`);
};

frappe.pages["nexo-daily-sales"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Daily Sales Summary"),
		single_column: true,
	});

	const page = wrapper.page;

	// Date picker in toolbar — defaults to today
	const date_field = page.add_field({
		fieldtype: "Date",
		fieldname: "sales_date",
		label: __("Date"),
		default: frappe.datetime.get_today(),
		change: function () {
			load_summary(this.get_value());
		},
	});

	page.set_primary_action(__("Refresh"), function () {
		load_summary(date_field.get_value());
	}, "fa fa-refresh");

	const $body = $(wrapper).find(".layout-main-section");

	function load_summary(date) {
		if (!date) date = frappe.datetime.get_today();

		$body.html(
			`<div style="padding:40px;text-align:center;" class="text-muted">${__("Loading...")}</div>`
		);

		frappe.call({
			method: "nexo_spares.api.daily_sales.get_daily_summary",
			args: { date: date },
			callback: function (r) {
				if (r.message) render_summary(r.message);
			},
			error: function () {
				$body.html(
					`<div class="alert alert-danger" style="margin:20px;">${__("Failed to load data.")}</div>`
				);
			},
		});
	}

	function render_summary(data) {
		const currency = frappe.boot.sysdefaults.currency || "KES";
		const fmt = (v) => format_currency(parseFloat(v) || 0, currency);
		const date_label = frappe.datetime.str_to_user(data.date);

		let payment_rows = "";
		if (data.payment_breakdown && data.payment_breakdown.length) {
			data.payment_breakdown.forEach(function (p) {
				const badge = get_payment_badge(p.mode_of_payment);
				payment_rows += `
					<tr>
						<td>
							<span class="indicator ${badge}">${p.mode_of_payment}</span>
						</td>
						<td class="text-right"><strong>${fmt(p.total_amount)}</strong></td>
						<td class="text-right text-muted">${p.tx_count} ${__("invoice(s)")}</td>
					</tr>`;
			});
		} else {
			payment_rows = `
				<tr>
					<td colspan="3" class="text-center text-muted" style="padding:20px;">
						${__("No POS sales recorded for this date.")}
					</td>
				</tr>`;
		}

		const html = `
			<div style="padding:20px;">
				<div class="row">
					<div class="col-md-5 col-sm-12">
						<div style="
							border-left: 4px solid var(--primary);
							padding: 20px 24px;
							margin-bottom: 20px;
							background: var(--card-bg);
							border-radius: 4px;
							box-shadow: var(--card-shadow);
						">
							<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);">
								${__("Total Sales")} &mdash; ${date_label}
							</div>
							<div style="font-size:36px;font-weight:700;color:var(--primary);margin-top:8px;">
								${fmt(data.total_sales)}
							</div>
							<div style="margin-top:6px;color:var(--text-muted);">
								${data.invoice_count} ${data.invoice_count === 1 ? __("transaction") : __("transactions")}
							</div>
						</div>
					</div>
				</div>

				<div class="row">
					<div class="col-md-7 col-sm-12">
						<div style="
							background: var(--card-bg);
							border-radius: 4px;
							box-shadow: var(--card-shadow);
							overflow: hidden;
						">
							<div style="
								padding: 12px 16px;
								border-bottom: 1px solid var(--border-color);
								font-weight: 600;
							">
								${__("Payment Breakdown")}
							</div>
							<table class="table" style="margin:0;">
								<thead style="background:var(--subtle-fg);">
									<tr>
										<th>${__("Mode of Payment")}</th>
										<th class="text-right">${__("Amount")}</th>
										<th class="text-right">${__("Count")}</th>
									</tr>
								</thead>
								<tbody>
									${payment_rows}
								</tbody>
							</table>
						</div>
					</div>
				</div>
			</div>`;

		$body.html(html);
	}

	function get_payment_badge(mode) {
		const m = (mode || "").toLowerCase();
		if (m.includes("cash")) return "green";
		if (m.includes("mpesa") || m.includes("m-pesa") || m.includes("mobile")) return "blue";
		if (m.includes("card") || m.includes("visa") || m.includes("mastercard")) return "orange";
		return "grey";
	}

	// Load today on page open
	load_summary(frappe.datetime.get_today());
};

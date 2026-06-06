import frappe
from frappe import _
from frappe.utils import fmt_money, flt


def execute(filters=None):
    filters = filters or {}
    if not filters.get("from_date"):
        filters["from_date"] = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not filters.get("to_date"):
        filters["to_date"] = frappe.utils.nowdate()
    period = filters.get("period") or "Weekly"

    if period == "Monthly":
        key_expr = "DATE_FORMAT(si.posting_date, '%%Y-%%m')"
        label_expr = "DATE_FORMAT(si.posting_date, '%%Y-%%m')"
    elif period == "Weekly":
        key_expr = "YEARWEEK(si.posting_date, 1)"
        label_expr = "MIN(DATE(si.posting_date))"
    else:
        key_expr = "DATE(si.posting_date)"
        label_expr = "DATE(si.posting_date)"

    # Raw data: period x mode amounts
    rows = frappe.db.sql(
        f"""
        SELECT
            {key_expr}                          AS period_key,
            {label_expr}                        AS period_label,
            sip.mode_of_payment,
            COALESCE(SUM(sip.amount), 0)        AS amount,
            COUNT(DISTINCT si.name)             AS tx_count
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
        WHERE si.docstatus = 1
          AND si.is_pos = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY {key_expr}, sip.mode_of_payment
        ORDER BY {key_expr}, sip.mode_of_payment
        """,
        filters,
        as_dict=True,
    )

    # Discover all modes
    all_modes = sorted({r.mode_of_payment for r in rows})

    # Pivot into period → {mode: amount}
    pivot = {}
    for row in rows:
        key = str(row.period_key)
        if key not in pivot:
            pivot[key] = {"period_label": str(row.period_label or row.period_key), "total": 0}
        pivot[key][row.mode_of_payment] = flt(row.amount)
        pivot[key]["total"] = pivot[key].get("total", 0) + flt(row.amount)

    columns = [{"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 120}]
    for mode in all_modes:
        columns.append({
            "label": _(mode),
            "fieldname": _safe_fieldname(mode),
            "fieldtype": "Currency",
            "width": 130,
        })
    columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 130})

    data = []
    for key in sorted(pivot.keys()):
        row_data = {"period": pivot[key]["period_label"], "total": flt(pivot[key].get("total"))}
        for mode in all_modes:
            row_data[_safe_fieldname(mode)] = flt(pivot[key].get(mode, 0))
        data.append(row_data)

    message = _build_summary(data, all_modes, filters)
    return columns, data, message


def _safe_fieldname(mode):
    return mode.lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def _build_summary(data, all_modes, filters):
    currency = (
        frappe.get_cached_value("Company", frappe.defaults.get_user_default("Company"), "default_currency")
        or "KES"
    )

    def money(v):
        return fmt_money(v or 0, currency=currency)

    grand_total = sum(flt(r["total"]) for r in data)
    mode_totals = {}
    for mode in all_modes:
        fn = _safe_fieldname(mode)
        mode_totals[mode] = sum(flt(r.get(fn, 0)) for r in data)

    def card(label, value, color="#2563eb", sub=None):
        sub_html = f'<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{sub}</div>' if sub else ""
        return f"""
        <div style="background:var(--card-bg);border-radius:6px;box-shadow:var(--card-shadow);
                    padding:14px 18px;flex:1;min-width:130px;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);">{label}</div>
          <div style="font-size:17px;font-weight:700;color:{color};margin-top:4px;">{value}</div>
          {sub_html}
        </div>"""

    mode_colors = ["#2563eb", "#27ae60", "#e67e22", "#8e44ad", "#e74c3c", "#16a085"]
    cards_html = card("Total Sales", money(grand_total))
    for i, mode in enumerate(all_modes):
        pct = (mode_totals[mode] / grand_total * 100) if grand_total else 0
        cards_html += card(mode, money(mode_totals[mode]), mode_colors[i % len(mode_colors)],
                           sub=f"{pct:.1f}% of total")

    return f'<div style="padding:16px 0;"><div style="display:flex;gap:12px;flex-wrap:wrap;">{cards_html}</div></div>'

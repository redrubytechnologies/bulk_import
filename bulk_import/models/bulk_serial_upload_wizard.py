from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import logging

_logger = logging.getLogger(__name__)

MANUAL_SERIAL_TRACKING = ('serial',)
AUTO_SERIAL_TRACKING = ('auto_serial',)
ALL_TRACKED = MANUAL_SERIAL_TRACKING + AUTO_SERIAL_TRACKING


class BulkSerialUploadWizard(models.TransientModel):
    _name = 'bulk.serial.upload.wizard'
    _description = 'Bulk Serial Number Upload Wizard for DC'

    picking_ids = fields.Many2many('stock.picking', string='Delivery Challans')
    picking_count = fields.Integer(string='DC Count', readonly=True)
    dc_identifier = fields.Selection([
        ('dc_number', 'DC Number'),
        ('reference', 'Reference Number'),
    ], string='Identify DCs by', required=True, default='dc_number')

    # Step 1 — quantity file (downloaded, user edits qty, re-uploads)
    qty_file = fields.Binary(string='Quantity File', attachment=False)
    qty_filename = fields.Char(string='Qty File Name')

    # Step 2 — serial file (generated from qty_file, user fills serials, uploads)
    import_file = fields.Binary(string='Serial File', attachment=False)
    import_filename = fields.Char(string='Serial File Name')

    has_serial_products = fields.Boolean(
        string='Has Serial Products',
        compute='_compute_has_serial_products',
    )

    @api.depends('picking_ids')
    def _compute_has_serial_products(self):
        for rec in self:
            rec.has_serial_products = any(
                move.product_id.tracking in MANUAL_SERIAL_TRACKING
                for picking in rec.picking_ids
                for move in picking.move_ids
                if move.state not in ('cancel', 'done')
            )

    # ── helpers ────────────────────────────────────────────────────────────────

    def _get_dc_key(self, picking):
        if self.dc_identifier == 'dc_number':
            return picking.dc_number or ''
        return picking.name or ''

    def _eligible_pickings(self):
        if self.dc_identifier == 'dc_number':
            return self.picking_ids.filtered(lambda p: p.dc_number)
        return self.picking_ids

    def _picking_sale_order(self, picking):
        return picking.sale_id or picking.sale_order_id or False

    def _mapped_lots_for(self, product, sale_order):
        if not sale_order:
            return self.env['stock.lot']
        return self.env['stock.lot'].search([
            ('product_id', '=', product.id),
            ('sale_order_id', '=', sale_order.id),
        ], order='id')

    def _sync_move_qty(self, move, new_qty):
        """Update product_uom_qty and sync move lines to new_qty.

        product_uom_qty drives both 'Demand Qty' and 'Quantity' columns on the DC
        (Quantity = min(WO quants, product_uom_qty)), so both must be updated together.

        For assigned/partially_available moves, Odoo auto-calls _do_unreserve() +
        _action_assign() when product_uom_qty is written, which re-creates all lines
        from stock. We explicitly unreserve first to prevent that cascade.
        """
        new_qty = int(new_qty)
        if new_qty <= 0 or move.product_id.tracking not in ALL_TRACKED:
            return

        # Update demand quantity without triggering _do_unreserve().
        # Odoo's write() for product_uom_qty calls _do_unreserve() unless
        # 'do_not_unreserve' is in context (see stock_move.py:860).
        # _do_unreserve() causes cascades in this install that invalidate the
        # move record. We manage move lines manually below instead.
        if abs(move.product_uom_qty - new_qty) > 0.001:
            move.with_context(do_not_unreserve=True).write({'product_uom_qty': new_qty})

        # Sync move lines to match new_qty
        open_lines = move.move_line_ids.filtered(
            lambda ml: ml.state not in ('done', 'cancel')
        )
        current_count = len(open_lines)

        if current_count < new_qty:
            for _ in range(new_qty - current_count):
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'picking_id': move.picking_id.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
        elif current_count > new_qty:
            unassigned = open_lines.filtered(lambda ml: not ml.lot_id)
            remove_count = current_count - new_qty
            unassigned[:remove_count].unlink()

    @staticmethod
    def _make_header(ws, headers, colors):
        from openpyxl.styles import Font, PatternFill, Alignment
        for col, (h, c) in enumerate(zip(headers, colors), 1):
            cell = ws.cell(row=1, column=col)
            cell.value = h
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color=c, end_color=c, fill_type='solid')
            cell.alignment = Alignment(horizontal='center')

    @staticmethod
    def _autowidth(ws, ncols, nrows):
        from openpyxl.utils import get_column_letter
        for col in range(1, ncols + 1):
            max_len = max(
                (len(str(ws.cell(r, col).value or '')) for r in range(1, nrows)),
                default=10,
            )
            ws.column_dimensions[get_column_letter(col)].width = min(max_len + 4, 45)

    def _make_attachment(self, filename, wb):
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        encoded = base64.b64encode(output.read()).decode('utf-8')
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': encoded,
            'res_model': self._name,
            'res_id': self.id,
            'public': True,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment.id),
            'target': 'new',
        }

    # ── Step 1: Download quantity template ────────────────────────────────────

    def action_download_template(self):
        """Download Sheet 1 — one row per product per DC with demand quantity.
        User edits quantities then uploads this file to generate the serial template.
        """
        self.ensure_one()
        try:
            from openpyxl import Workbook

            eligible = self._eligible_pickings()
            if not eligible:
                if self.dc_identifier == 'dc_number':
                    raise UserError(_(
                        "None of the selected DCs have a generated DC Number. "
                        "Switch to 'Reference Number' mode or select DCs with a DC number."
                    ))
                raise UserError(_("No eligible DCs found for the selected identifier mode."))

            wb = Workbook()
            ws = wb.active
            ws.title = "Quantities"
            self._make_header(
                ws,
                ['DC Number', 'Reference', 'Product Code', 'Product Name', 'Quantity'],
                ['4472C4',    '4472C4',    '4472C4',       '4472C4',       'ED7D31'],
            )

            row = 2
            for picking in eligible.sorted(key=lambda p: self._get_dc_key(p)):
                if picking.state in ('cancel', 'done'):
                    continue
                dc_key = self._get_dc_key(picking)
                if not dc_key:
                    continue

                product_qty = {}
                for move in picking.move_ids.filtered(lambda m: m.state not in ('cancel', 'done')):
                    if move.product_id.tracking not in ALL_TRACKED:
                        continue
                    pid = move.product_id.id
                    product_qty[pid] = product_qty.get(pid, 0) + move.product_uom_qty

                for pid, total_qty in sorted(
                    product_qty.items(),
                    key=lambda x: (self.env['product.product'].browse(x[0]).name or ''),
                ):
                    product = self.env['product.product'].browse(pid)
                    ws.cell(row=row, column=1).value = picking.dc_number or ''
                    ws.cell(row=row, column=2).value = picking.name or ''
                    ws.cell(row=row, column=3).value = product.default_code or ''
                    ws.cell(row=row, column=4).value = product.name or ''
                    ws.cell(row=row, column=5).value = int(total_qty)
                    row += 1

            if row == 2:
                raise UserError(_("No eligible products found in the selected DCs."))

            self._autowidth(ws, 5, row)
            ws.freeze_panes = 'A2'
            return self._make_attachment('quantity_template.xlsx', wb)

        except UserError:
            raise
        except Exception as e:
            _logger.error("Error generating quantity template: %s", e)
            raise UserError(_("Error generating template: %s") % str(e))

    # ── Step 2: Generate serial template from uploaded quantity file ───────────

    def action_generate_serial_template(self):
        """Read uploaded quantity file, create one serial row per unit for each
        'By Unique Serial Number' product.  Serial Number column is left blank
        for the user to fill in.
        """
        self.ensure_one()
        if not self.qty_file:
            raise UserError(_("Please upload the quantity file first (Step 1)."))

        try:
            from openpyxl import load_workbook, Workbook

            # ── Read quantities ───────────────────────────────────────────────
            wb_qty = load_workbook(io.BytesIO(base64.b64decode(self.qty_file)), data_only=True)
            ws_qty = wb_qty.active

            # Build picking lookups from ALL selected pickings so we can match
            # by reference even when DC numbers haven't been generated yet.
            by_dcnum = {}
            by_ref = {}
            for p in self.picking_ids:
                if p.dc_number:
                    by_dcnum[p.dc_number.strip()] = p
                if p.name:
                    by_ref[p.name.strip()] = p

            serial_rows = []   # list of (picking, product, qty)
            skip_reasons = []
            data_rows = 0

            for row in ws_qty.iter_rows(min_row=2, values_only=True):
                if not any(c for c in row if c not in (None, '')):
                    continue
                dc_num = str(row[0]).strip() if row[0] is not None else ''
                reference = str(row[1]).strip() if row[1] is not None else ''
                prod_code = str(row[2]).strip() if row[2] is not None else ''
                prod_name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ''
                try:
                    qty = int(float(row[4])) if row[4] is not None else 0
                except (ValueError, TypeError):
                    qty = 0

                data_rows += 1

                if not prod_code and not prod_name:
                    skip_reasons.append(_("Row skipped: no product code or name (DC='%s')") % (dc_num or reference))
                    continue
                if qty <= 0:
                    skip_reasons.append(_("Row skipped: qty <= 0 for product '%s' (DC='%s')") % (prod_code or prod_name, dc_num or reference))
                    continue

                # Match picking by identifier mode
                if self.dc_identifier == 'dc_number':
                    picking = by_dcnum.get(dc_num) or by_ref.get(reference)
                    if not picking:
                        skip_reasons.append(_(
                            "Row skipped: DC Number '%s' (Reference '%s') not found in selected DCs. "
                            "Available DC Numbers: %s"
                        ) % (dc_num, reference, ', '.join(sorted(by_dcnum.keys())[:5]) or '(none)'))
                        continue
                else:
                    picking = by_ref.get(reference) or by_dcnum.get(dc_num)
                    if not picking:
                        skip_reasons.append(_(
                            "Row skipped: Reference '%s' (DC Number '%s') not found in selected DCs. "
                            "Available References: %s"
                        ) % (reference, dc_num, ', '.join(sorted(by_ref.keys())[:5]) or '(none)'))
                        continue

                # Resolve product through the picking's moves (by code, then by name)
                if prod_code:
                    move = picking.move_ids.filtered(
                        lambda m: m.product_id.default_code == prod_code
                        and m.state not in ('cancel', 'done')
                    )[:1]
                else:
                    move = self.env['stock.move']

                if not move and prod_name:
                    move = picking.move_ids.filtered(
                        lambda m: (m.product_id.name or '').strip() == prod_name
                        and m.state not in ('cancel', 'done')
                    )[:1]

                if move:
                    product = move.product_id
                else:
                    # Final fallback: global search
                    if prod_code:
                        product = self.env['product.product'].search(
                            [('default_code', '=', prod_code)], limit=1
                        )
                    if not product and prod_name:
                        product = self.env['product.product'].search(
                            [('name', '=', prod_name)], limit=1
                        )

                if not product:
                    skip_reasons.append(_("Row skipped: product '%s' not found.") % (prod_code or prod_name))
                    continue

                if product.tracking not in MANUAL_SERIAL_TRACKING:
                    skip_reasons.append(_(
                        "Row skipped: product '%s' has tracking='%s' — "
                        "only 'By Unique Serial Number' (serial) products need a serial template."
                    ) % (product.display_name, product.tracking))
                    continue

                # Update demand quantity and sync move lines from the uploaded file
                if move:
                    self._sync_move_qty(move, qty)
                else:
                    move = picking.move_ids.filtered(
                        lambda m: m.product_id.id == product.id
                        and m.state not in ('cancel', 'done')
                    )[:1]
                    if move:
                        self._sync_move_qty(move, qty)

                serial_rows.append((picking, product, qty))

            if not serial_rows:
                diag = '\n'.join(skip_reasons[:10]) if skip_reasons else _("No data rows found in the file.")
                raise UserError(_(
                    "No 'By Unique Serial Number' products found in the quantity file "
                    "(%d data row(s) processed).\n\n"
                    "Diagnostic:\n%s\n\n"
                    "Note: 'No OEM Serial Number Tracking' products are auto-assigned "
                    "during import and do not need a serial template."
                ) % (data_rows, diag))

            # ── Build serial template ─────────────────────────────────────────
            wb_ser = Workbook()
            ws_ser = wb_ser.active
            ws_ser.title = "Serials"
            self._make_header(
                ws_ser,
                ['DC Number', 'Reference', 'Product Code', 'Product Name', 'Line No.', 'Serial Number'],
                ['4472C4',    '4472C4',    '4472C4',       '4472C4',       '4472C4',   'C00000'],
            )

            row = 2
            for picking, product, qty in serial_rows:
                for line_no in range(1, qty + 1):
                    ws_ser.cell(row=row, column=1).value = picking.dc_number or ''
                    ws_ser.cell(row=row, column=2).value = picking.name or ''
                    ws_ser.cell(row=row, column=3).value = product.default_code or ''
                    ws_ser.cell(row=row, column=4).value = product.name or ''
                    ws_ser.cell(row=row, column=5).value = line_no
                    # Column 6 (Serial Number) — blank, user fills
                    row += 1

            self._autowidth(ws_ser, 6, row)
            ws_ser.freeze_panes = 'A2'
            return self._make_attachment('serial_template.xlsx', wb_ser)

        except UserError:
            raise
        except Exception as e:
            _logger.error("Error generating serial template: %s", e)
            raise UserError(_("Error generating serial template: %s") % str(e))

    # ── Step 3: Import serials and validate DCs ────────────────────────────────

    def action_import_serials(self):
        """Read uploaded serial file, assign lot_ids to move lines, auto-assign
        auto_serial products, then validate each DC.
        """
        self.ensure_one()
        if not self.import_file and not self.qty_file:
            raise UserError(_("Please upload the quantity file (Step 1) or serial file (Step 2)."))

        try:
            from openpyxl import load_workbook

            # Build picking lookups from ALL selected pickings (dc_number + reference)
            pick_by_dcnum = {}
            pick_by_ref = {}
            for p in self.picking_ids:
                if p.dc_number:
                    pick_by_dcnum[p.dc_number.strip()] = p
                if p.name:
                    pick_by_ref[p.name.strip()] = p

            def _find_picking(dc_num, ref):
                if self.dc_identifier == 'dc_number':
                    return pick_by_dcnum.get(dc_num) or pick_by_ref.get(ref)
                return pick_by_ref.get(ref) or pick_by_dcnum.get(dc_num)

            errors = []
            serial_success = 0
            raw_rows = []
            serial_occurrences = {}

            # ── Qty-only mode: no serial file, auto_serial products only ──────
            if not self.import_file:
                wb_qty = load_workbook(io.BytesIO(base64.b64decode(self.qty_file)), data_only=True)
                ws_qty = wb_qty.active
                for row in ws_qty.iter_rows(min_row=2, values_only=True):
                    if not any(c for c in row if c not in (None, '')):
                        continue
                    dc_num = str(row[0]).strip() if row[0] is not None else ''
                    ref = str(row[1]).strip() if row[1] is not None else ''
                    prod_code = str(row[2]).strip() if row[2] is not None else ''
                    prod_name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ''
                    try:
                        qty = int(float(row[4])) if row[4] is not None else 0
                    except (ValueError, TypeError):
                        qty = 0
                    if (not prod_code and not prod_name) or qty <= 0:
                        continue
                    picking = _find_picking(dc_num, ref)
                    if not picking:
                        continue
                    if prod_code:
                        move = picking.move_ids.filtered(
                            lambda m: m.product_id.default_code == prod_code
                            and m.state not in ('cancel', 'done')
                        )[:1]
                    else:
                        move = self.env['stock.move']
                    if not move and prod_name:
                        move = picking.move_ids.filtered(
                            lambda m: (m.product_id.name or '').strip() == prod_name
                            and m.state not in ('cancel', 'done')
                        )[:1]
                    if move:
                        self._sync_move_qty(move, qty)
                # raw_rows stays empty → Pass 1 & 2 are skipped, go straight to Pass 3

            else:
                # ── Serial file mode: read serial file for Pass 1 & 2 ─────────
                wb = load_workbook(io.BytesIO(base64.b64decode(self.import_file)), data_only=True)
                ws = wb['Serials'] if 'Serials' in wb.sheetnames else wb.active

                header = [str(ws.cell(1, c).value or '').strip().lower() for c in range(1, 7)]
                new_fmt = 'reference' in header
                if new_fmt:
                    C_DC, C_REF, C_CODE, C_NAME, C_LINE, C_SERIAL = 0, 1, 2, 3, 4, 5
                else:
                    C_DC, C_REF, C_CODE, C_NAME, C_LINE, C_SERIAL = 0, None, 1, 2, 3, 4

                for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(c for c in row if c not in (None, '')):
                        continue

                    dc_num_cell = str(row[C_DC]).strip() if row[C_DC] is not None else ''
                    ref_cell = (
                        str(row[C_REF]).strip()
                        if C_REF is not None and row[C_REF] is not None else ''
                    )
                    prod_code = str(row[C_CODE]).strip() if row[C_CODE] is not None else ''
                    prod_name = str(row[C_NAME]).strip() if row[C_NAME] is not None else ''
                    try:
                        line_no = int(float(row[C_LINE])) if row[C_LINE] is not None else 0
                    except (ValueError, TypeError):
                        line_no = 0
                    serial_name = str(row[C_SERIAL]).strip() if row[C_SERIAL] is not None else ''

                    if (not prod_code and not prod_name) or not line_no or not serial_name:
                        continue

                    if not dc_num_cell and not ref_cell:
                        continue

                    prod_ident = prod_code or prod_name
                    raw_rows.append((row_num, dc_num_cell, ref_cell, prod_code, prod_name, line_no, serial_name))
                    serial_occurrences.setdefault((prod_ident, serial_name), []).append(row_num)

            # ── Pass 1 end ────────────────────────────────────────────────────
            duplicate_keys = {k for k, v in serial_occurrences.items() if len(v) > 1}

            # ── Pass 2: validate + assign serial-tracked products ─────────────
            for row_num, dc_num_cell, ref_cell, prod_code, prod_name, line_no, serial_name in raw_rows:

                prod_ident = prod_code or prod_name
                if (prod_ident, serial_name) in duplicate_keys:
                    dup_rows = serial_occurrences[(prod_ident, serial_name)]
                    errors.append(_(
                        "Row %d: Serial '%s' (product '%s') appears %d times "
                        "(rows %s). Remove duplicates."
                    ) % (row_num, serial_name, prod_ident, len(dup_rows),
                         ', '.join(str(r) for r in dup_rows)))
                    continue

                # Try dc_number first, then reference — works even when dc_number is blank
                if self.dc_identifier == 'dc_number':
                    picking = pick_by_dcnum.get(dc_num_cell) or pick_by_ref.get(ref_cell)
                    dc_key = dc_num_cell or ref_cell
                else:
                    picking = pick_by_ref.get(ref_cell) or pick_by_dcnum.get(dc_num_cell)
                    dc_key = ref_cell or dc_num_cell

                if not picking:
                    id_label = 'DC Number' if self.dc_identifier == 'dc_number' else 'Reference'
                    errors.append(_(
                        "Row %d: %s '%s' not found among the selected DCs."
                    ) % (row_num, id_label, dc_key))
                    continue

                if picking.state in ('done', 'cancel'):
                    errors.append(_(
                        "Row %d: DC '%s' is %s — skipping."
                    ) % (row_num, dc_key, picking.state))
                    continue

                # Resolve product through picking's moves (by code, then by name)
                product = self.env['product.product']
                if prod_code:
                    move = picking.move_ids.filtered(
                        lambda m: m.product_id.default_code == prod_code
                        and m.state not in ('cancel', 'done')
                    )[:1]
                    if move:
                        product = move.product_id
                if not product and prod_name:
                    move = picking.move_ids.filtered(
                        lambda m: (m.product_id.name or '').strip() == prod_name
                        and m.state not in ('cancel', 'done')
                    )[:1]
                    if move:
                        product = move.product_id
                if not product:
                    if prod_code:
                        product = self.env['product.product'].search(
                            [('default_code', '=', prod_code)], limit=1
                        )
                    if not product and prod_name:
                        product = self.env['product.product'].search(
                            [('name', '=', prod_name)], limit=1
                        )
                if not product:
                    errors.append(_("Row %d: Product '%s' not found.") % (row_num, prod_ident))
                    continue

                if product.tracking not in MANUAL_SERIAL_TRACKING:
                    continue

                sale_order = self._picking_sale_order(picking)

                lot = self.env['stock.lot'].search([
                    ('name', '=', serial_name),
                    ('product_id', '=', product.id),
                ], limit=1)

                if not lot:
                    any_lot = self.env['stock.lot'].search(
                        [('product_id', '=', product.id)], limit=1
                    )
                    if not any_lot:
                        errors.append(_(
                            "Row %d: Product '%s' has no serial numbers in the system. "
                            "Please create serials first."
                        ) % (row_num, product.display_name))
                    else:
                        errors.append(_(
                            "Row %d: Serial '%s' does not exist for product '%s'."
                        ) % (row_num, serial_name, prod_ident))
                    continue

                if sale_order:
                    if not lot.sale_order_id:
                        errors.append(_(
                            "Row %d: Serial '%s' (product '%s') has no work order mapping. "
                            "DC '%s' requires serials mapped to work order '%s'."
                        ) % (row_num, serial_name, prod_ident, dc_key, sale_order.name))
                        continue
                    if lot.sale_order_id.id != sale_order.id:
                        errors.append(_(
                            "Row %d: Serial '%s' belongs to work order '%s', "
                            "but DC '%s' is for work order '%s'."
                        ) % (row_num, serial_name, lot.sale_order_id.name,
                             dc_key, sale_order.name))
                        continue

                move_lines = picking.move_line_ids.filtered(
                    lambda ml: ml.product_id.id == product.id
                    and ml.state not in ('done', 'cancel')
                ).sorted('id')

                if not move_lines:
                    errors.append(_(
                        "Row %d: No move lines for product '%s' in DC '%s'. "
                        "Run 'Check Availability' first."
                    ) % (row_num, prod_ident, dc_key))
                    continue

                if line_no > len(move_lines):
                    errors.append(_(
                        "Row %d: Line No. %d exceeds available move lines (%d) "
                        "for product '%s' in DC '%s'."
                    ) % (row_num, line_no, len(move_lines), prod_ident, dc_key))
                    continue

                ml = move_lines[line_no - 1]
                ml.lot_id = lot.id
                ml.quantity = 1.0
                ml.picked = True
                serial_success += 1

            # ── Pass 3: auto-assign auto_serial products ──────────────────────
            auto_success = 0
            auto_errors = []

            for picking in self._eligible_pickings().filtered(
                lambda p: p.state not in ('done', 'cancel')
            ):
                sale_order = self._picking_sale_order(picking)
                dc_key = self._get_dc_key(picking)

                for move in picking.move_ids.filtered(
                    lambda m: m.state not in ('cancel', 'done')
                    and m.product_id.tracking in AUTO_SERIAL_TRACKING
                ):
                    product = move.product_id

                    open_lines = move.move_line_ids.filtered(
                        lambda ml: not ml.lot_id and ml.state not in ('done', 'cancel')
                    ).sorted('id')

                    if not open_lines:
                        continue

                    any_lot = self.env['stock.lot'].search(
                        [('product_id', '=', product.id)], limit=1
                    )
                    if not any_lot:
                        auto_errors.append(_(
                            "DC '%s' — Product '%s' has no serial numbers in the system."
                        ) % (dc_key, product.display_name))
                        continue

                    mapped_lots = self._mapped_lots_for(product, sale_order)
                    if not mapped_lots:
                        wo_name = sale_order.name if sale_order else _('(no work order)')
                        auto_errors.append(_(
                            "DC '%s' — Product '%s' has no serials mapped to work order '%s'."
                        ) % (dc_key, product.display_name, wo_name))
                        continue

                    lot_iter = iter(mapped_lots)
                    assigned = 0
                    for ml in open_lines:
                        lot = next(lot_iter, None)
                        if not lot:
                            break
                        ml.lot_id = lot.id
                        ml.quantity = 1.0
                        ml.picked = True
                        assigned += 1
                    auto_success += assigned

                    remaining = len(open_lines) - assigned
                    if remaining > 0:
                        auto_errors.append(_(
                            "DC '%s' — Product '%s': only %d of %d serials auto-assigned "
                            "(not enough mapped serials in work order '%s')."
                        ) % (dc_key, product.display_name, assigned, len(open_lines),
                             sale_order.name if sale_order else _('N/A')))

            # ── Auto-validate DCs ──────────────────────────────────────────────
            validated_dcs = []
            validate_errors = []

            if serial_success or auto_success:
                for picking in self._eligible_pickings().filtered(
                    lambda p: p.state not in ('done', 'cancel')
                ):
                    try:
                        result = picking.with_context(
                            skip_immediate=True,
                            skip_backorder=True,
                        ).button_validate()
                        if not isinstance(result, dict) or result.get('type') == 'ir.actions.act_url':
                            validated_dcs.append(self._get_dc_key(picking) or picking.name)
                        else:
                            validated_dcs.append(self._get_dc_key(picking) or picking.name)
                    except Exception as e:
                        validate_errors.append(
                            _("DC '%s' could not be validated: %s")
                            % (self._get_dc_key(picking) or picking.name, str(e))
                        )

            # ── Result ────────────────────────────────────────────────────────
            all_errors = errors + auto_errors + validate_errors
            parts = []
            if serial_success:
                parts.append(_("%d serial number(s) assigned from file.") % serial_success)
            if auto_success:
                parts.append(_("%d serial number(s) auto-assigned (No OEM products).") % auto_success)
            if validated_dcs:
                parts.append(_("%d DC(s) validated and marked Done: %s")
                             % (len(validated_dcs), ', '.join(validated_dcs)))
            if not serial_success and not auto_success:
                parts.append(_("No serial numbers were assigned."))
            if all_errors:
                parts.append(_("\nErrors (%d):") % len(all_errors))
                parts.extend(all_errors)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Bulk Serial Upload'),
                    'message': '\n'.join(parts),
                    'type': 'warning' if all_errors else 'success',
                    'sticky': bool(all_errors),
                },
            }

        except UserError:
            raise
        except Exception as e:
            _logger.error("Error importing serial numbers: %s", e)
            raise UserError(_("Error importing file: %s") % str(e))

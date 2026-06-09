from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime



class StockLotGenerateWizard(models.TransientModel):
    _name = 'stock.lot.generate.wizard'
    _description = 'Generate Serial Numbers Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    prefix = fields.Char(
        string='Serial Prefix',
        help='Fixed prefix e.g. "INST26" — serials will be INST26013, INST26014 ...',
    )
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    next_number = fields.Integer(
        string='Next Number',
        compute='_compute_next_number',
        store=False,
        readonly=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        domain=[('usage', '=', 'internal')],
        help='All generated serials will be set to qty=1 at this location',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        product_id = res.get('product_id')
        if product_id:
            product = self.env['product.product'].browse(product_id)
            prefix = (product.product_tmpl_id.serial_number_prefix or
                    product.serial_number_prefix or '')
            year_2 = datetime.now().strftime('%y')
            res['prefix'] = f"{prefix}{year_2}" if prefix else ''
        return res



    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     if not self.product_id:
    #         self.prefix = False
    #         return
    #     prefix = (self.product_id.product_tmpl_id.serial_number_prefix or
    #             self.product_id.serial_number_prefix or '')
    #     year_2 = datetime.now().strftime('%y')
    #     self.prefix = f"{prefix}{year_2}" if prefix else ''



    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            self.prefix = False
            return
        prefix = (self.product_id.product_tmpl_id.serial_number_prefix or
                self.product_id.serial_number_prefix or '')
        year_2 = datetime.now().strftime('%y')
        if prefix:
            self.prefix = f"{prefix}{year_2}"
        else:
            self.prefix = False  # Leave blank so user can type it
            return {
                'warning': {
                    'title': _('No Serial Prefix Configured'),
                    'message': _(
                        'Product "%s" has no Serial Number Prefix set. '
                        'Please enter a prefix manually, or configure one '
                        'on the product form.'
                    ) % self.product_id.display_name,
                }
            }

    @api.depends('prefix', 'product_id')
    def _compute_next_number(self):
        StockLot = self.env['stock.lot']
        for rec in self:
            if not rec.prefix:
                rec.next_number = 1
                continue
            # Find all lots whose name starts with the prefix and has only digits after
            all_lots = StockLot.search(
                [('name', 'like', rec.prefix)],
                order='name desc',
            )
            last_num = 0
            for lot in all_lots:
                remainder = lot.name[len(rec.prefix):]
                if remainder.isdigit():
                    last_num = int(remainder)
                    break
            rec.next_number = last_num + 1

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity < 1:
                raise ValidationError(_('Quantity must be at least 1.'))

    def action_generate(self):
        self.ensure_one()

        if not self.prefix or not isinstance(self.prefix, str) or not self.prefix.strip():
            raise UserError(_(
                'Serial Prefix is required. Either configure a "Serial Number Prefix" '
                'on the product form, or enter one manually in this wizard.'
            ))

        StockLot = self.env['stock.lot']
        StockQuant = self.env['stock.quant']
        prefix = self.prefix.strip()

        # --- 1. Determine starting number (single query) ---
        all_lots = StockLot.search([('name', 'like', prefix)], order='name desc')
        last_num = 0
        for lot in all_lots:
            remainder = lot.name[len(prefix):]
            if remainder.isdigit():
                last_num = int(remainder)
                break

        # --- 2. Build all serial names and check duplicates in one query ---
        serial_names = [
            '%s%03d' % (prefix, last_num + 1 + i)
            for i in range(self.quantity)
        ]
        existing = StockLot.search([
            ('name', 'in', serial_names),
            ('product_id', '=', self.product_id.id),
        ], limit=1)
        if existing:
            raise UserError(_('Serial "%s" already exists.') % existing.name)

        # --- 3. Batch-create all lots in one ORM call ---
        lot_vals = [
            {
                'name': name,
                'product_id': self.product_id.id,
                'company_id': self.company_id.id,
            }
            for name in serial_names
        ]
        lots = StockLot.create(lot_vals)

        # --- 4. Batch-create quants and apply inventory once ---
        if self.location_id:
            quant_vals = [
                {
                    'product_id': self.product_id.id,
                    'lot_id': lot.id,
                    'location_id': self.location_id.id,
                    'inventory_quantity': 1.0,
                }
                for lot in lots
            ]
            quants = StockQuant.sudo().create(quant_vals)
            quants._apply_inventory()
            quants.inventory_quantity_set = False

        return {
            'name': _('Generated Serial Numbers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', lots.ids)],
            'target': 'current',
        }

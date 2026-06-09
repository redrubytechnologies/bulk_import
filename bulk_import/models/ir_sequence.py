# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IrSequenceFiscalYear(models.Model):
    _inherit = 'ir.sequence'

    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(
                pytz.timezone(self._context.get('tz') or 'UTC')
            )
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(
                    date or self._context.get('ir_sequence_date')
                )
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(
                    date_range or self._context.get('ir_sequence_date_range')
                )

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y',
                'doy': '%j', 'woy': '%W', 'weekday': '%w',
                'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S',
            }
            res = {}
            for key, fmt in sequences.items():
                res[key] = effective_date.strftime(fmt)
                res['range_' + key] = range_date.strftime(fmt)
                res['current_' + key] = now.strftime(fmt)

            def fiscal_year_str(dt):
                # Financial year: April 1 – March 31, short format e.g. 26-27
                if dt.month >= 4:
                    return '%02d-%02d' % (dt.year % 100, (dt.year + 1) % 100)
                else:
                    return '%02d-%02d' % ((dt.year - 1) % 100, dt.year % 100)

            res['fiscal_year'] = fiscal_year_str(effective_date)
            res['range_fiscal_year'] = fiscal_year_str(range_date)
            res['current_fiscal_year'] = fiscal_year_str(now)

            return res

        self.ensure_one()
        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except (ValueError, TypeError, KeyError):
            raise UserError(_('Invalid prefix or suffix for sequence %r', self.name))
        return interpolated_prefix, interpolated_suffix

    def _create_date_range_seq(self, date):
        # Use fiscal year (April 1 – March 31) instead of calendar year
        date_obj = fields.Date.from_string(date)
        if date_obj.month >= 4:
            fy_start_year = date_obj.year
        else:
            fy_start_year = date_obj.year - 1

        date_from = '{}-04-01'.format(fy_start_year)
        date_to = '{}-03-31'.format(fy_start_year + 1)

        date_range = self.env['ir.sequence.date_range'].search([
            ('sequence_id', '=', self.id),
            ('date_from', '>=', date),
            ('date_from', '<=', date_to),
        ], order='date_from desc', limit=1)
        if date_range:
            date_to = date_range.date_from + timedelta(days=-1)

        date_range = self.env['ir.sequence.date_range'].search([
            ('sequence_id', '=', self.id),
            ('date_to', '>=', date_from),
            ('date_to', '<=', date),
        ], order='date_to desc', limit=1)
        if date_range:
            date_from = date_range.date_to + timedelta(days=1)

        seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'sequence_id': self.id,
        })
        return seq_date_range

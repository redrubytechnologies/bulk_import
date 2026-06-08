from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import csv
import io
# from werkzeug.utils import url_quote
from urllib.parse import quote as url_quote


class PartnerAddressBulkImport(models.TransientModel):
    _name = 'partner.address.bulk.import'
    _description = 'Bulk Import Partner Child Addresses'
    
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    import_file = fields.Binary(string='Import File')  # REMOVE required=True
    filename = fields.Char(string='Filename')
    
    # ADD THESE TWO FIELDS FOR TEMPLATE DOWNLOAD
    template_file = fields.Binary(string='Template File', readonly=True)
    template_filename = fields.Char(string='Template Filename', readonly=True)
    
    # def action_import_addresses(self):
    #     """Import multiple addresses including multiple delivery addresses"""
    #     if not self.import_file:
    #         raise UserError('Please upload a file to import.')
        
    #     file_data = base64.b64decode(self.import_file)
    #     file_input = io.StringIO(file_data.decode('utf-8'))
    #     reader = csv.DictReader(file_input)
        
    #     addresses_created = 0
    #     errors = []
        
    #     for idx, row in enumerate(reader, start=2):
    #         try:
    #             # Validate address type
    #             address_type = row.get('type', 'other').strip().lower()
    #             gstin = (row.get('gstin') or '').strip()

    #             if address_type not in ['contact', 'invoice', 'delivery', 'other', 'private']:
    #                 errors.append(f"Row {idx}: Invalid type '{address_type}'. Must be: contact, invoice, delivery, other, or private")
    #                 continue
                
    #             # Create child address
    #             # vals = {
    #             #     'parent_id': self.partner_id.id,
    #             #     'type': address_type,
    #             #     'name': row.get('name', '').strip(),
    #             #     'street': row.get('street', '').strip(),
    #             #     'street2': row.get('street2', '').strip(),
    #             #     'city': row.get('city', '').strip(),
    #             #     'zip': row.get('zip', '').strip(),
    #             #     'phone': row.get('phone', '').strip(),
    #             #     'mobile': row.get('mobile', '').strip(),
    #             #     'email': row.get('email', '').strip(),
    #             # }
    #             vals = {
    #                 'parent_id': self.partner_id.id,
    #                 'type': address_type,
    #                 'name': (row.get('name') or '').strip(),
    #                 'street': (row.get('street') or '').strip(),
    #                 'street2': (row.get('street2') or '').strip(),
    #                 'city': (row.get('city') or '').strip(),
    #                 'zip': (row.get('zip') or '').strip(),
    #                 'phone': (row.get('phone') or '').strip(),
    #                 'mobile': (row.get('mobile') or '').strip(),
    #                 'email': (row.get('email') or '').strip(),
    #             }

    #             # GST

    #             # Add GSTIN only for delivery address
    #             if gstin and address_type == 'delivery':
    #                 vals['vat'] = gstin
                
    #             # Add country
    #             country_name = row.get('country', '').strip()
    #             if country_name:
    #                 country = self.env['res.country'].search([
    #                     '|', ('name', '=ilike', country_name), 
    #                     ('code', '=ilike', country_name)
    #                 ], limit=1)
    #                 if country:
    #                     vals['country_id'] = country.id
                
    #             # Add state
    #             state_name = row.get('state', '').strip()
    #             if state_name and vals.get('country_id'):
    #                 state = self.env['res.country.state'].search([
    #                     ('country_id', '=', vals['country_id']),
    #                     '|', ('name', '=ilike', state_name), 
    #                     ('code', '=ilike', state_name)
    #                 ], limit=1)
    #                 if state:
    #                     vals['state_id'] = state.id
                
    #             self.env['res.partner'].create(vals)
    #             addresses_created += 1
                
    #         except Exception as e:
    #             errors.append(f"Row {idx}: {str(e)}")
        
    #     # Show result message
    #     if errors:
    #         error_msg = '\n'.join(errors)
    #         raise UserError(f"{addresses_created} address(es) imported successfully.\n\nErrors:\n{error_msg}")
        
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Success!',
    #             'message': f'{addresses_created} address(es) imported successfully!',
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }


    # def action_import_addresses(self):
    #     """Import multiple addresses including multiple delivery addresses"""
    #     if not self.import_file:
    #         raise UserError('Please upload a file to import.')
        
    #     file_data = base64.b64decode(self.import_file)
    #     # file_input = io.StringIO(file_data.decode('utf-8'))
    #     file_input = io.StringIO(file_data.decode('utf-8-sig'))
    #     reader = csv.DictReader(file_input)
        
    #     addresses_created = 0
    #     errors = []
        
    #     for idx, row in enumerate(reader, start=2):
    #         try:
    #             # Validate address type
    #             address_type = row.get('type', 'other').strip().lower()
    #             gstin = (row.get('gstin') or '').strip()
    #             consignee_name = (row.get('consignee_name') or '').strip()   #soundharya

    #             if address_type not in ['contact', 'invoice', 'delivery', 'other', 'private']:
    #                 errors.append(f"Row {idx}: Invalid type '{address_type}'. Must be: contact, invoice, delivery, other, or private")
    #                 continue
                
    #             vals = {
    #                 'parent_id': self.partner_id.id,
    #                 'type': address_type,
    #                 # 'name': (row.get('name') or '').strip(),
    #                 'name': (row.get('name') or row.get('\ufeffname') or '').strip(),
    #                 'street': (row.get('street') or '').strip(),
    #                 'street2': (row.get('street2') or '').strip(),
    #                 'city': (row.get('city') or '').strip(),
    #                 'zip': (row.get('zip') or '').strip(),
    #                 'phone': (row.get('phone') or '').strip(),
    #                 'mobile': (row.get('mobile') or '').strip(),
    #                 'email': (row.get('email') or '').strip(),
    #                 'comment': f"Consignee: {consignee_name}" if consignee_name else False,   #soundharya
    #             }
                
    #             # Add country
    #             country_name = (row.get('country') or '').strip()
    #             if country_name:
    #                 country = self.env['res.country'].search([
    #                     '|', ('name', '=ilike', country_name), 
    #                     ('code', '=ilike', country_name)
    #                 ], limit=1)
    #                 if country:
    #                     vals['country_id'] = country.id
                
    #             # Add state
    #             state_name = (row.get('state') or '').strip()
    #             if state_name and vals.get('country_id'):
    #                 state = self.env['res.country.state'].search([
    #                     ('country_id', '=', vals['country_id']),
    #                     '|', ('name', '=ilike', state_name), 
    #                     ('code', '=ilike', state_name)
    #                 ], limit=1)
    #                 if state:
    #                     vals['state_id'] = state.id
                
    #             # Create partner record
    #             partner = self.env['res.partner'].with_context(
    #                 no_vat_validation=True
    #             ).create(vals)
                
    #             # Force write GSTIN separately if delivery
    #             if gstin and address_type == 'delivery':
    #                 partner.write({'vat': gstin})
                
    #             addresses_created += 1
                
    #         except Exception as e:
    #             errors.append(f"Row {idx}: {str(e)}")
        
    #     # Show result message
    #     if errors:
    #         error_msg = '\n'.join(errors)
    #         raise UserError(f"{addresses_created} address(es) imported successfully.\n\nErrors:\n{error_msg}")
        
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Success!',
    #             'message': f'{addresses_created} address(es) imported successfully!',
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }

    def action_import_addresses(self):
        if not self.import_file:
            raise UserError('Please upload a file to import.')

        file_data = base64.b64decode(self.import_file)
        filename = (self.filename or '').lower()

        # Parse rows based on file type
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            rows = self._parse_xlsx(file_data)
        else:
            rows = self._parse_csv(file_data)

        addresses_created = 0
        errors = []

        for idx, row in enumerate(rows, start=2):
            try:
                address_type = (row.get('type') or 'other').strip().lower()
                gstin = (row.get('gstin') or '').strip()
                consignee_name = (row.get('consignee_name') or '').strip()

                if address_type not in ['contact', 'invoice', 'delivery', 'other', 'private']:
                    errors.append(f"Row {idx}: Invalid type '{address_type}'. Must be: contact, invoice, delivery, other, or private")
                    continue

                vals = {
                    'parent_id': self.partner_id.id,
                    'type': address_type,
                    'name': (row.get('name') or '').strip(),
                    'street': (row.get('street') or '').strip(),
                    'street2': (row.get('street2') or '').strip(),
                    'city': (row.get('city') or '').strip(),
                    'zip': str(row.get('zip') or '').strip(),
                    'phone': (row.get('phone') or '').strip(),
                    'mobile': (row.get('mobile') or '').strip(),
                    'email': (row.get('email') or '').strip(),
                    'comment': f"Consignee: {consignee_name}" if consignee_name else False,
                }

                country_name = (row.get('country') or '').strip()
                if country_name:
                    country = self.env['res.country'].search([
                        '|', ('name', '=ilike', country_name),
                        ('code', '=ilike', country_name)
                    ], limit=1)
                    if country:
                        vals['country_id'] = country.id

                state_name = (row.get('state') or '').strip()
                if state_name and vals.get('country_id'):
                    state = self.env['res.country.state'].search([
                        ('country_id', '=', vals['country_id']),
                        '|', ('name', '=ilike', state_name),
                        ('code', '=ilike', state_name)
                    ], limit=1)
                    if state:
                        vals['state_id'] = state.id

                partner = self.env['res.partner'].with_context(no_vat_validation=True).create(vals)

                if gstin and address_type == 'delivery':
                    partner.write({'vat': gstin})

                addresses_created += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        if errors:
            error_msg = '\n'.join(errors)
            raise UserError(f"{addresses_created} address(es) imported successfully.\n\nErrors:\n{error_msg}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': f'{addresses_created} address(es) imported successfully!',
                'type': 'success',
                'sticky': False,
            }
        }


    def _parse_xlsx(self, file_data):
        """Parse XLSX file and return list of dicts"""
        try:
            import openpyxl
        except ImportError:
            raise UserError('openpyxl library is required to import XLSX files. Please install it or use CSV format.')

        wb = openpyxl.load_workbook(filename=io.BytesIO(file_data), read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise UserError('The XLSX file is empty.')

        # First row = headers
        headers = [str(h).strip().lower() if h else '' for h in rows[0]]

        result = []
        for row in rows[1:]:
            # Skip completely empty rows
            if not any(cell for cell in row):
                continue
            row_dict = {}
            for col_idx, header in enumerate(headers):
                val = row[col_idx] if col_idx < len(row) else None
                row_dict[header] = str(val).strip() if val is not None else ''
            result.append(row_dict)

        return result


    def _parse_csv(self, file_data):
        """Parse CSV file and return list of dicts"""
        for encoding in ('utf-8-sig', 'latin-1', 'cp1252'):
            try:
                file_input = io.TextIOWrapper(io.BytesIO(file_data), encoding=encoding, newline='')
                reader = csv.DictReader(file_input)
                # Normalize headers to lowercase
                rows = []
                for row in reader:
                    rows.append({k.strip().lower(): v for k, v in row.items()})
                return rows
            except UnicodeDecodeError:
                file_input.detach()
                continue
        raise UserError('Could not decode the CSV file. Please save as UTF-8 and try again.')

    
    def action_download_template(self):
        """Download CSV template with examples - NEW METHOD"""
        # Create template content
        template_data = "name,type,street,street2,city,state,country,zip,phone,mobile,email,gstin,consignee_name\n"
        # template_data += "Main Contact Person,contact,123 Main Street,Suite 100,New Delhi,Delhi,India,110001,+91-11-12345678,+91-9876543210,contact@example.com\n"
        # template_data += "Invoice Department,invoice,456 MG Road,Floor 2,Mumbai,Maharashtra,India,400001,+91-22-98765432,,accounts@example.com\n"
        # template_data += "Warehouse 1,delivery,789 Industrial Area,Sector 18,Noida,Uttar Pradesh,India,201301,+91-120-1234567,,\n"
        # template_data += "Warehouse 2,delivery,321 Tech Park,Phase 3,Bangalore,Karnataka,India,560001,+91-80-7654321,,\n"
        # template_data += "Branch Office,other,654 Park Street,,Kolkata,West Bengal,India,700016,+91-33-2468135,,branch@example.com\n"
        
        template_data += "Main Contact Person,contact,123 Main Street,Suite 100,New Delhi,Delhi,India,110001,+91-11-12345678,+91-9876543210,contact@example.com,,\n"
        template_data += "Invoice Department,invoice,456 MG Road,Floor 2,Mumbai,Maharashtra,India,400001,+91-22-98765432,,accounts@example.com,,\n"
        template_data += "Warehouse 1,delivery,789 Industrial Area,Sector 18,Noida,Uttar Pradesh,India,201301,+91-120-1234567,,warehouse@example.com,33AAAAA0000A1Z5,The Director\n"
        template_data += "Warehouse 2,delivery,321 Tech Park,Phase 3,Bangalore,Karnataka,India,560001,+91-80-7654321,,warehouse2@example.com,29AAAAA0000A1Z5,The Manager\n"
        template_data += "Branch Office,other,654 Park Street,Phase 4,Kolkata,West Bengal,India,700016,+91-33-2468135,,branch@example.com,,\n"
        # Encode to base64
        encoded = base64.b64encode(template_data.encode('utf-8'))
        
        # Generate filename with partner name
        partner_name = self.partner_id.name.replace(' ', '_').replace('/', '_')
        filename = f'{partner_name}_address_import_template.csv'
        
        # Write to wizard record
        self.write({
            'template_file': encoded,
            'template_filename': filename,
        })
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=partner.address.bulk.import&id={self.id}&field=template_file&download=true&filename={url_quote(filename)}',
            'target': 'self',
        }

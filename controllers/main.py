from odoo import http
from odoo.http import request
import os
import tempfile

class ConsigneeController(http.Controller):
    
    @http.route('/zigma_erp/download_dynamic_template/<path:filename>', 
                type='http', auth='user')
    def download_dynamic_template(self, filename, **kwargs):
        """Download dynamically generated template"""
        try:
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'rb') as file:
                    file_content = file.read()
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass
                
                return request.make_response(
                    file_content,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition', f'attachment; filename="{filename}"')
                    ]
                )
            else:
                return request.not_found()
                
        except Exception as e:
            return request.not_found()

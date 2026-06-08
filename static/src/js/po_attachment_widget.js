/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import {
    many2ManyBinaryField,
    Many2ManyBinaryField,
} from "@web/views/fields/many2many_binary/many2many_binary_field";
import { FileInput } from "@web/core/file_input/file_input";

const MAX_PO_FILE_SIZE = 5 * 1024 * 1024; // 5 MB in bytes

/**
 * Custom FileInput that rejects files larger than 5 MB before uploading.
 * This prevents the server from returning an HTML error page (which would
 * cause a JSON parse error in the parent uploadFiles method).
 */
class FileInput5MB extends FileInput {
    async uploadFiles(params) {
        const files = (params.ufile && params.ufile.length && params.ufile) ||
                      (params.file ? [params.file] : []);

        for (const file of files) {
            if (file.size > MAX_PO_FILE_SIZE) {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                this.notification.add(
                    _t(
                        '"%(filename)s" (%(size)s MB) exceeds the maximum allowed size of 5 MB. Please upload a smaller file.',
                        { filename: file.name, size: sizeMB }
                    ),
                    { title: _t("File Too Large"), type: "danger" }
                );
                return null;
            }
        }

        return super.uploadFiles(params);
    }
}
FileInput5MB.template = FileInput.template;
FileInput5MB.defaultProps = FileInput.defaultProps;
FileInput5MB.props = FileInput.props;

/**
 * Custom Many2ManyBinaryField that uses FileInput5MB instead of FileInput.
 * Register this as widget="many2many_binary_5mb" on the field.
 */
class Many2ManyBinaryField5MB extends Many2ManyBinaryField {
    static components = {
        FileInput: FileInput5MB,
    };
}

registry.category("fields").add("many2many_binary_5mb", {
    ...many2ManyBinaryField,
    component: Many2ManyBinaryField5MB,
});

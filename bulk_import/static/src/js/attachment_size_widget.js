/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2ManyBinaryField, many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field";
import { FileInput } from "@web/core/file_input/file_input";
import { useService } from "@web/core/utils/hooks";

const MAX_SIZE_BYTES = 2 * 1024 * 1024; // 2 MB

class LimitedSizeFileInput extends FileInput {
    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    async uploadFiles(params) {
        const files = params.ufile || (params.file ? [params.file] : []);
        for (const file of files) {
            if (file.size > MAX_SIZE_BYTES) {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                this.notification.add(
                    `"${file.name}" (${sizeMB} MB) exceeds the maximum allowed size of 2 MB. Please upload a smaller file.`,
                    { type: "danger", title: "File Too Large", sticky: false }
                );
                return null;
            }
        }
        return super.uploadFiles(params);
    }
}

LimitedSizeFileInput.props = { ...FileInput.props };
LimitedSizeFileInput.defaultProps = { ...FileInput.defaultProps };
LimitedSizeFileInput.template = "web.FileInput";

export class AttachmentSizeLimitedField extends Many2ManyBinaryField {
    static components = {
        ...Many2ManyBinaryField.components,
        FileInput: LimitedSizeFileInput,
    };
}

export const attachmentSizeLimitedField = {
    ...many2ManyBinaryField,
    component: AttachmentSizeLimitedField,
};

registry.category("fields").add("attachment_size_limited", attachmentSizeLimitedField);

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { useEffect } from "@odoo/owl";

export class CustomMovesListRenderer extends ListRenderer {
    static recordRowTemplate = "zigma_erp.CustomMovesListRenderer.RecordRow";  // Reference to your record row template

    setup() {
        super.setup();
        useEffect(
            () => {
                this.keepColumnWidths = false;
            },
            () => [this.state.columns]
        );
    }

    processAllColumn(allColumns, list) {
        let cols = super.processAllColumn(...arguments);
        
        if (list.resModel === "internal.transfer.outward.line") {
            cols.push({
                type: 'opendetailsop',
                id: `column_detailOp_${cols.length}`,
            });
        } else if (list.resModel === "internal.transfer.inward.line") {
            cols.push({
                type: 'opendetailsin',
                id: `column_detailIn_${cols.length}`,
            });
        }
        
        return cols;
    }
}

CustomMovesListRenderer.props = [ ...ListRenderer.props, 'transMoveOpen?'];

export class CustomMovesX2ManyField extends X2ManyField {
    setup() {
        super.setup();
        this.canOpenRecord = true;
    }

    get isMany2Many() {
        return false;
    }

    async openRecord(record) {
                if (this.canOpenRecord && !record.isNew) {
            const dirty = await record.isDirty();
            const hasQtyChange = 'quantity' in record._changes || 'product_uom_qty' in record._changes;

            if (dirty && hasQtyChange) {
                await record._parentRecord.save({ reload: true });
                record = record._parentRecord.data[this.props.name].records.find(e => e.resId === record.resId);
                if (!record) return;
            }
        }

        return super.openRecord(record);
    }
}

CustomMovesX2ManyField.components = { ...X2ManyField.components, ListRenderer: CustomMovesListRenderer };

export const stockMoveX2ManyField = {
    ...x2ManyField,
    component: CustomMovesX2ManyField,
    additionalClasses: [...x2ManyField.additionalClasses || [], "o_field_one2many"],
};

// Register the custom widget with Odoo
registry.category("fields").add("trans_move_one2many", stockMoveX2ManyField);


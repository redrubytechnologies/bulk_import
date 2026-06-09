/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    openConsigneeBulkImport() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Bulk Import",
            res_model: "consignee.bulk.import.wizard",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    },
});

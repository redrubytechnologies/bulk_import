/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
    },

    async saveButtonClicked(params = {}) {
        const result = await super.saveButtonClicked(params);
        
        if (result) {
            this.notification.add("Your data has been saved successfully", {
                type: "success",
                title: "Success",
            });
        }
        
        return result;
    },
});
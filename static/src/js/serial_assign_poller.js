/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Subscribes to the "serial_assign_done" bus channel.
 * When the backend background thread finishes assigning serial numbers it
 * pushes a message on this channel.  We reload the page automatically so
 * the user never needs to click anything.
 */
const serialAssignPollerService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, { bus_service, notification, action }) {
        bus_service.subscribe("serial_assign_done", (payload) => {
            if (payload.state === "done") {
                notification.add(
                    "Serial numbers have been assigned successfully.",
                    { type: "success", title: "Done" }
                );
            } else {
                notification.add(
                    "Serial assignment failed. Check the server log for details.",
                    { type: "danger", title: "Error", sticky: true }
                );
            }
            // Reload the current form so the updated state is visible
            action.doAction({ type: "ir.actions.client", tag: "reload" });
        });

        bus_service.start();
    },
};

registry.category("services").add("serial_assign_poller", serialAssignPollerService);

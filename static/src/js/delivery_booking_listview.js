/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { DeliveryBookingDashBoard } from "./delivery_booking_dashboard";

export class DeliveryBookingDashBoardRenderer extends ListRenderer {}

DeliveryBookingDashBoardRenderer.template = "zigma_erp.DeliveryBookingListView";
DeliveryBookingDashBoardRenderer.components = Object.assign(
    {},
    ListRenderer.components,
    { DeliveryBookingDashBoard }
);

export const DeliveryBookingDashBoardListView = {
    ...listView,
    Renderer: DeliveryBookingDashBoardRenderer,
};

registry.category("views").add("delivery_booking_dashboard_list", DeliveryBookingDashBoardListView);

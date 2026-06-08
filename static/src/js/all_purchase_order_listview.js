/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { AllPurchaseOrderDashBoard } from "./all_purchase_order_dashboard";

export class AllPurchaseOrderDashBoardRenderer extends ListRenderer {}

AllPurchaseOrderDashBoardRenderer.template = "zigma_erp.AllPurchaseOrderListView";
AllPurchaseOrderDashBoardRenderer.components = Object.assign(
    {},
    ListRenderer.components,
    { AllPurchaseOrderDashBoard }
);

export const AllPurchaseOrderDashBoardListView = {
    ...listView,
    Renderer: AllPurchaseOrderDashBoardRenderer,
};

registry.category("views").add("all_purchase_order_dashboard_list", AllPurchaseOrderDashBoardListView);

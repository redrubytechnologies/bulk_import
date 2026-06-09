/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { PurchaseOrderDashBoard } from "./purchase_order_dashboard";

export class PurchaseOrderDashBoardRenderer extends ListRenderer {}

PurchaseOrderDashBoardRenderer.template = "zigma_erp.PurchaseOrderListView";
PurchaseOrderDashBoardRenderer.components = Object.assign(
    {},
    ListRenderer.components,
    { PurchaseOrderDashBoard }
);

export const PurchaseOrderDashBoardListView = {
    ...listView,
    Renderer: PurchaseOrderDashBoardRenderer,
};

registry.category("views").add("purchase_order_dashboard_list", PurchaseOrderDashBoardListView);

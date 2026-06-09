/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { PurchaseIndentDashBoard } from "./purchase_indent_dashboard";

export class PurchaseIndentDashBoardRenderer extends ListRenderer {}

PurchaseIndentDashBoardRenderer.template = "zigma_erp.PurchaseIndentListView";
PurchaseIndentDashBoardRenderer.components = Object.assign(
    {},
    ListRenderer.components,
    { PurchaseIndentDashBoard }
);

export const PurchaseIndentDashBoardListView = {
    ...listView,
    Renderer: PurchaseIndentDashBoardRenderer,
};

registry.category("views").add("purchase_indent_dashboard_list", PurchaseIndentDashBoardListView);

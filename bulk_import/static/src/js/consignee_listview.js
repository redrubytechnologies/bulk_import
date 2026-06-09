/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ConsigneeDashBoard } from "./consignee_dashboard";

export class ConsigneeDashBoardRenderer extends ListRenderer {}

ConsigneeDashBoardRenderer.template = "zigma_erp.ConsigneeListView";
ConsigneeDashBoardRenderer.components = Object.assign({}, ListRenderer.components, { ConsigneeDashBoard });

export const ConsigneeDashBoardListView = {
    ...listView,
    Renderer: ConsigneeDashBoardRenderer,
};

registry.category("views").add("consignee_dashboard_list", ConsigneeDashBoardListView);

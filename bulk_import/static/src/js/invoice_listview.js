/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { InvoiceDashBoard } from "./invoice_dashboard";

export class InvoiceDashBoardRenderer extends ListRenderer {}

InvoiceDashBoardRenderer.template = "zigma_erp.InvoiceListView";
InvoiceDashBoardRenderer.components = Object.assign(
    {},
    ListRenderer.components,
    { InvoiceDashBoard }
);

export const InvoiceDashBoardListView = {
    ...listView,
    Renderer: InvoiceDashBoardRenderer,
};

registry.category("views").add("invoice_dashboard_list", InvoiceDashBoardListView);

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ReceiptDashBoard } from "./receipt_dashboard";
import { DeliveryDashBoard } from "./delivery_dashboard";

export class ReceiptDashBoardRenderer extends ListRenderer {
    get isReceiptView() {
        return (
            this.props.list?.model?.config?.context?.restricted_picking_type_code === "incoming"
        );
    }

    get isDeliveryView() {
        return (
            this.props.list?.model?.config?.context?.restricted_picking_type_code === "outgoing"
        );
    }
}

ReceiptDashBoardRenderer.template = "zigma_erp.ReceiptListView";
ReceiptDashBoardRenderer.components = Object.assign({}, ListRenderer.components, {
    ReceiptDashBoard,
    DeliveryDashBoard,
});

export const ReceiptDashBoardListView = {
    ...listView,
    Renderer: ReceiptDashBoardRenderer,
};

registry.category("views").add("receipt_dashboard_list", ReceiptDashBoardListView);

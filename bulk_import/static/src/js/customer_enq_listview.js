/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { CustomerEnqDashBoard } from "./customer_enq_dashboard";

export class CustomerEnqDashBoardRenderer extends ListRenderer {
    get enquiryType() {
        return this.props.list.context.default_enquiry_type || 'direct';
    }
}
CustomerEnqDashBoardRenderer.template = "zigma_erp.CustomerEnqListView";
CustomerEnqDashBoardRenderer.components = Object.assign(
    {}, ListRenderer.components, { CustomerEnqDashBoard }
);

export const CustomerEnqDashBoardListView = { ...listView, Renderer: CustomerEnqDashBoardRenderer };
registry.category("views").add("customer_enq_dashboard_list", CustomerEnqDashBoardListView);

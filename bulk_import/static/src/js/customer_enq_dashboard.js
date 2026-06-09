/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

export class CustomerEnqDashBoard extends Component {
    static props = {
        enquiryType: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        onWillStart(async () => {
            const type = this.props.enquiryType || 'direct';
            this.enqData = await this.orm.call(
                "customer.enq", "retrieve_dashboard", [type]
            );
        });
    }

    setSearchContext(ev) {
        const filter_name = ev.currentTarget.getAttribute("filter_name");
        // clearQuery resets query to [] and calls _notify() to refresh the list
        this.env.searchModel.clearQuery();
        if (filter_name) {
            const filters = filter_name.split(",");
            const searchItems = this.env.searchModel.getSearchItems(
                (item) => filters.includes(item.name)
            );
            for (const item of searchItems) {
                this.env.searchModel.toggleSearchItem(item.id);
            }
        }
    }
}
CustomerEnqDashBoard.template = "zigma_erp.CustomerEnqDashboard";

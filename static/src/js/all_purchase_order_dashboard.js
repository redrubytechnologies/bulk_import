/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class AllPurchaseOrderDashBoard extends Component {
    static props = {
        domain: { type: Array, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        onWillStart(async () => {
            await this._fetchDashboard(this.props);
        });
        onWillUpdateProps(async (nextProps) => {
            await this._fetchDashboard(nextProps);
        });
    }

    async _fetchDashboard(props) {
        this.allPoData = await this.orm.call(
            "purchase.order",
            "retrieve_all_orders_dashboard",
            [],
            {}
        );
    }

    setAllPOFilter(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        const allFilters = ["draft_rfqs", "zigma_sent", "to_approve", "approved", "zigma_cancel"];

        const allItems = this.env.searchModel.getSearchItems((item) =>
            allFilters.includes(item.name)
        );
        for (const item of allItems) {
            const isActive = this.env.searchModel.query.some(
                (q) => q.searchItemId === item.id
            );
            if (isActive) {
                this.env.searchModel.toggleSearchItem(item.id);
            }
        }

        if (filterName !== "all") {
            const filters = filterName.split(",");
            const targetItems = this.env.searchModel.getSearchItems((item) =>
                filters.includes(item.name)
            );
            for (const item of targetItems) {
                this.env.searchModel.toggleSearchItem(item.id);
            }
        }
    }
}

AllPurchaseOrderDashBoard.template = "zigma_erp.AllPurchaseOrderDashboard";

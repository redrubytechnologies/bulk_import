/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class DeliveryBookingDashBoard extends Component {
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
        this.bookingData = await this.orm.call(
            "delivery.booking",
            "retrieve_dashboard",
            [],
            {}
        );
    }

    setBookingStateFilter(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        const stateFilterNames = ["draft", "confirmed", "dispatched", "delivered", "cancel"];

        const stateItems = this.env.searchModel.getSearchItems((item) =>
            stateFilterNames.includes(item.name)
        );
        for (const item of stateItems) {
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

DeliveryBookingDashBoard.template = "zigma_erp.DeliveryBookingDashboard";

/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class PurchaseIndentDashBoard extends Component {
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
        const domain = (props && props.domain) || [];
        this.indentData = await this.orm.call(
            "purchase.indent",
            "retrieve_dashboard",
            [],
            { domain }
        );
    }

    setIndentFilter(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        const allFilters = ["filter_indent_draft", "filter_indent_approved",
                            "filter_indent_vendor_mapping", "filter_indent_cancel"];

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

PurchaseIndentDashBoard.template = "zigma_erp.PurchaseIndentDashboard";

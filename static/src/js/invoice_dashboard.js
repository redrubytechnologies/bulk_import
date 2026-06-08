/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class InvoiceDashBoard extends Component {
    static props = {
        domain: { type: Array, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        onWillStart(async () => {
            await this._fetchDashboard();
        });
        onWillUpdateProps(async () => {
            await this._fetchDashboard();
        });
    }

    async _fetchDashboard() {
        this.invoiceData = await this.orm.call(
            "account.move",
            "retrieve_invoice_dashboard",
            [],
            {}
        );
    }

    setInvoiceFilter(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        // existing Odoo filter names: draft, posted, cancel, open (=Unpaid), closed (=Paid)
        const allFilters = ["draft", "posted", "cancel", "open", "closed"];

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

InvoiceDashBoard.template = "zigma_erp.InvoiceDashboard";

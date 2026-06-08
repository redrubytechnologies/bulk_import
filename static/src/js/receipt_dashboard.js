// /** @odoo-module */
// import { useService } from "@web/core/utils/hooks";
// import { Component, onWillStart } from "@odoo/owl";

// export class ReceiptDashBoard extends Component {
//     setup() {
//         this.orm = useService("orm");
//         onWillStart(async () => {
//             this.receiptData = await this.orm.call("stock.picking", "retrieve_receipt_dashboard");
//         });
//     }

//     setReceiptStateFilter(ev) {
//         const filterName = ev.currentTarget.getAttribute("filter_name");
//         const stateFilterNames = ["draft", "waiting", "available", "receipt_done", "receipt_cancel"];

//         // Remove all currently active state filters
//         const stateItems = this.env.searchModel.getSearchItems((item) =>
//             stateFilterNames.includes(item.name)
//         );
//         for (const item of stateItems) {
//             const isActive = this.env.searchModel.query.some(
//                 (q) => q.searchItemId === item.id
//             );
//             if (isActive) {
//                 this.env.searchModel.toggleSearchItem(item.id);
//             }
//         }

//         // Apply the selected state filter (skip for "all")
//         if (filterName !== "all") {
//             const targetItems = this.env.searchModel.getSearchItems((item) =>
//                 item.name === filterName
//             );
//             for (const item of targetItems) {
//                 this.env.searchModel.toggleSearchItem(item.id);
//             }
//         }
//     }
// }

// ReceiptDashBoard.template = "zigma_erp.ReceiptDashboard";




/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class ReceiptDashBoard extends Component {
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
        const domain = props.domain || [];
        this.receiptData = await this.orm.call(
            "stock.picking",
            "retrieve_receipt_dashboard",
            [],
            { domain }
        );
    }

    setReceiptStateFilter(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        const stateFilterNames = ["draft", "waiting", "available", "receipt_done", "receipt_cancel"];

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
            const targetItems = this.env.searchModel.getSearchItems((item) =>
                item.name === filterName
            );
            for (const item of targetItems) {
                this.env.searchModel.toggleSearchItem(item.id);
            }
        }
    }
}

ReceiptDashBoard.template = "zigma_erp.ReceiptDashboard";

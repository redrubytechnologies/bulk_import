// /** @odoo-module */
// import { patch } from "@web/core/utils/patch";
// import { PurchaseDashBoard } from '@purchase/views/purchase_dashboard';

// patch(PurchaseDashBoard.prototype, {
//     clearAllFilters(ev) {
//         ev.preventDefault();
//         // Collect active search item IDs from the current query, then toggle each off
//         const activeIds = this.env.searchModel.query.map(q => q.searchItemId);
//         for (const id of activeIds) {
//             this.env.searchModel.toggleSearchItem(id);
//         }
//     }
// });



/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { PurchaseDashBoard } from '@purchase/views/purchase_dashboard';
import { onWillStart, onWillUpdateProps, useState } from "@odoo/owl";

// Declare domain prop so OWL accepts it without a warning
PurchaseDashBoard.props = Object.assign({}, PurchaseDashBoard.props || {}, {
    domain: { type: Array, optional: true },
});

patch(PurchaseDashBoard.prototype, {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.purchaseData = useState({});

        onWillStart(() => this._fetchDashboard(this.props.domain || []));

        onWillUpdateProps((nextProps) => {
            const prev = JSON.stringify(this.props.domain || []);
            const next = JSON.stringify(nextProps.domain || []);
            if (prev !== next) {
                return this._fetchDashboard(nextProps.domain || []);
            }
        });
    },

    async _fetchDashboard(domain) {
        const data = await this.orm.call(
            "purchase.order", "retrieve_dashboard", [], { domain }
        );
        Object.assign(this.purchaseData, data);
    },

    clearAllFilters(ev) {
        ev.preventDefault();
        const activeIds = this.env.searchModel.query.map(q => q.searchItemId);
        for (const id of activeIds) {
            this.env.searchModel.toggleSearchItem(id);
        }
    },
});

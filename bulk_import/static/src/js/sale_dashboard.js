// /** @odoo-module */
// import { useService } from "@web/core/utils/hooks";
// import { Component, onWillStart } from "@odoo/owl";

// export class SaleDashBoard extends Component {
//     setup() {
//         this.orm = useService("orm");
//         onWillStart(async () => {
//             this.saleData = await this.orm.call("sale.order", "retrieve_dashboard");
//         });
//     }

//     setSearchContext(ev) {
//         const filter_name = ev.currentTarget.getAttribute("filter_name");
//         const filters = filter_name.split(",");
//         const searchItems = this.env.searchModel.getSearchItems((item) =>
//             filters.includes(item.name)
//         );
//         this.env.searchModel.query = [];
//         for (const item of searchItems) {
//             this.env.searchModel.toggleSearchItem(item.id);
//         }
//     }
// }

// SaleDashBoard.template = "zigma_erp.SaleDashboard";





/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";

export class SaleDashBoard extends Component {
    static props = {
        domain: { type: Array, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.saleData = useState({
            draft_count: 0,
            confirmed_count: 0,
            total_count: 0,
            cancel_count: 0,
        });

        onWillStart(() => this._fetchData(this.props.domain || []));

        onWillUpdateProps((nextProps) => {
            const prev = JSON.stringify(this.props.domain || []);
            const next = JSON.stringify(nextProps.domain || []);
            if (prev !== next) {
                return this._fetchData(nextProps.domain || []);
            }
        });
    }

    async _fetchData(domain) {
        const data = await this.orm.call("sale.order", "retrieve_dashboard", [], { domain });
        Object.assign(this.saleData, data);
    }

    setSearchContext(ev) {
        const filter_name = ev.currentTarget.getAttribute("filter_name");
        const filters = filter_name.split(",");
        const searchItems = this.env.searchModel.getSearchItems((item) =>
            filters.includes(item.name)
        );
        this.env.searchModel.query = [];
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}

SaleDashBoard.template = "zigma_erp.SaleDashboard";








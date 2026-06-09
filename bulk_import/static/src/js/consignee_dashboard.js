// /** @odoo-module */
// import { useService } from "@web/core/utils/hooks";
// import { Component, onWillStart } from "@odoo/owl";

// export class ConsigneeDashBoard extends Component {
//     static props = {
//         saleOrderId: { type: Number, optional: true },
//     };

//     setup() {
//         this.orm = useService("orm");
//         onWillStart(async () => {
//             const saleOrderId = this.props.saleOrderId || false;
//             this.consigneeData = await this.orm.call(
//                 "consignee.separation",
//                 "retrieve_dashboard",
//                 [saleOrderId]
//             );
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

// ConsigneeDashBoard.template = "zigma_erp.ConsigneeDashboard";



/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class ConsigneeDashBoard extends Component {
    static props = {
        saleOrderId: { type: Number, optional: true },
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
        const saleOrderId = props.saleOrderId || false;
        const domain = props.domain || [];
        this.consigneeData = await this.orm.call(
            "consignee.separation",
            "retrieve_dashboard",
            [saleOrderId],
            { domain }
        );
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

ConsigneeDashBoard.template = "zigma_erp.ConsigneeDashboard";

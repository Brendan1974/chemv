/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

patch(AccountReportFilters.prototype, {
    selectAccount(account) {
        account.selected = !account.selected;
        this.applyFilters("account");
    },
});

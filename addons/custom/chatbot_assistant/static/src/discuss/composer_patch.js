/** @odoo-module **/

import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Composer.prototype, {
    get placeholder() {
        const thread = this.thread ?? this.message?.thread;
        if (thread?.isChatbotAssistant) {
            return _t("Escribe tu consulta o /help para ver ejemplos…");
        }
        return super.placeholder;
    },
});

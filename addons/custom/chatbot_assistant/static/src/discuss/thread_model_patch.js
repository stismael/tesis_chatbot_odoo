/** @odoo-module **/

import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";

/** @type {import("models").Thread} */
const threadPatch = {
    /** Canal DM con el Asistente ERP (expuesto desde discuss.channel). */
    isChatbotAssistant: false,
};

patch(Thread.prototype, threadPatch);

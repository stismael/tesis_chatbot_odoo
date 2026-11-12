/** @odoo-module **/

import { SettingsFormController } from "@web/webclient/settings_form_view/settings_form_controller";
import { patch } from "@web/core/utils/patch";

/** Botones del chatbot que deben usar los valores del formulario sin aplicarlos ni recargar Ajustes. */
const CHATBOT_SETTINGS_BUTTONS = new Set([
    "action_chatbot_test_connection",
    "action_chatbot_sync_models",
    "action_chatbot_fallback_test_connection",
    "action_chatbot_fallback_sync_models",
]);

patch(SettingsFormController.prototype, {
    /**
     * Se guarda solo el registro temporal de Ajustes (no aplica la configuración) para que el
     * servidor reciba lo escrito. Después de la acción, Odoo recargaría Ajustes desde la
     * configuración guardada y se perdería lo escrito (por ejemplo, volvería a Gemini): en su
     * lugar se vuelve a leer únicamente este registro.
     */
    async beforeExecuteActionButton(clickParams) {
        if (CHATBOT_SETTINGS_BUTTONS.has(clickParams.name)) {
            const saved = await this.model.root.save({ reload: false });
            if (saved === false) {
                return false;
            }
            const model = this.model;
            model.load = async () => {
                delete model.load;
                await model.root.load();
            };
            return true;
        }
        return super.beforeExecuteActionButton(...arguments);
    },

    async afterExecuteActionButton(clickParams) {
        if (CHATBOT_SETTINGS_BUTTONS.has(clickParams.name)) {
            // Si no hubo recarga (una notificación no la pide), se quita el reemplazo de un solo uso
            // y se vuelve a leer este registro para mostrar lo que actualizó el servidor
            // (última verificación, catálogo).
            delete this.model.load;
            await this.model.root.load();
        }
        return super.afterExecuteActionButton(...arguments);
    },
});

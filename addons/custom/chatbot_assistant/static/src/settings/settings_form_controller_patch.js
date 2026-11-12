/** @odoo-module **/

import { SettingsFormController } from "@web/webclient/settings_form_view/settings_form_controller";
import { patch } from "@web/core/utils/patch";

/** Botones del chatbot que deben usar los valores del formulario sin recargar Ajustes. */
const CHATBOT_SETTINGS_BUTTONS = new Set([
    "action_chatbot_test_connection",
    "action_chatbot_sync_models",
]);

patch(SettingsFormController.prototype, {
    /**
     * Con noSaveDialog, Odoo igual hace model.root.save() y puede recargar la vista:
     * eso vuelve a get_values() (ICP) y restaura Gemini, vaciando lo que el usuario eligió.
     * Aquí guardamos el registro temporal sin reload y no abrimos el diálogo de Guardar.
     */
    async beforeExecuteActionButton(clickParams) {
        if (CHATBOT_SETTINGS_BUTTONS.has(clickParams.name)) {
            if (await this.model.root.isDirty()) {
                const saved = await this.model.root.save({ reload: false });
                if (saved === false) {
                    return false;
                }
            }
            return true;
        }
        return super.beforeExecuteActionButton(...arguments);
    },
});

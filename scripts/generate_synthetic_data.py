# Script ejecutado desde odoo shell para generar datos sintéticos
env['chatbot.test.data.generator'].generate_all()
env.cr.commit()
print('Datos sintéticos generados correctamente.')

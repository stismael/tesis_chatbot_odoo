bot = env["chatbot.discuss.service"]
chans = env["discuss.channel"].search([("channel_type", "=", "chat"), ("name", "ilike", "Asistente")])
print([c.name for c in chans])
msgs = env["mail.message"].search([("model", "=", "discuss.channel"), ("res_id", "in", chans.ids)])
print("borrando", len(msgs)); msgs.unlink()
env["chatbot.query.log"].search([]).unlink()
env["chatbot.session"].search([]).unlink()
env.cr.commit()

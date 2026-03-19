import uuid
from odoo import models, fields, api

class UcpBearerToken(models.Model):
    _name = 'ucp.bearer.token'
    _description = 'UCP Bearer Token for Identity Linking'

    name = fields.Char(string='Description', required=True)
    token = fields.Char(string='Access Token', required=True, readonly=True, copy=False, index=True, default=lambda self: str(uuid.uuid4()))
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade', default=lambda self: self.env.user)
    expiration = fields.Datetime(string='Expiration')

    _sql_constraints = [
        ('token_uniq', 'unique(token)', 'The Bearer Token must be unique!')
    ]

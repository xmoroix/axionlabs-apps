# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseApprovalBracket(models.Model):
    _name = 'purchase.approval.bracket'
    _description = 'Purchase Approval Bracket'
    _order = 'sequence, min_amount'

    name = fields.Char(
        string='Bracket Name',
        required=True,
        help='Name of this approval bracket (e.g., "Pharmacy - Manager Approval")'
    )

    sequence = fields.Integer(
        string='Priority',
        default=10,
        help='Lower sequence = higher priority. Used when multiple brackets match.'
    )

    min_amount = fields.Monetary(
        string='Minimum Amount',
        required=True,
        default=0.0,
        currency_field='currency_id',
        help='Minimum purchase order amount to trigger this bracket'
    )

    max_amount = fields.Monetary(
        string='Maximum Amount',
        currency_field='currency_id',
        help='Maximum purchase order amount for this bracket. Leave as 0 for unlimited.'
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        domain="[('usage', '=', 'internal')]",
        help='Optional: Apply this bracket only to purchases for a specific location. '
             'Leave empty to apply to all purchases.'
    )

    approver_ids = fields.Many2many(
        'res.users',
        'purchase_approval_bracket_approver_rel',
        'bracket_id',
        'user_id',
        string='Approvers',
        required=True,
        help='Users who can approve purchase orders in this bracket'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to disable this bracket without deleting it'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Company for which this bracket applies'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    # Display field showing approver names
    approver_names = fields.Char(
        string='Approvers',
        compute='_compute_approver_names',
        store=False
    )

    @api.depends('approver_ids')
    def _compute_approver_names(self):
        """Compute a comma-separated list of approver names for display"""
        for record in self:
            record.approver_names = ', '.join(record.approver_ids.mapped('name'))

    @api.constrains('min_amount', 'max_amount')
    def _check_amounts(self):
        """Validate that min_amount <= max_amount (when max_amount is set)"""
        for record in self:
            if record.max_amount > 0 and record.min_amount > record.max_amount:
                raise ValidationError(
                    'Minimum amount cannot be greater than maximum amount. '
                    f'Bracket "{record.name}": min={record.min_amount}, max={record.max_amount}'
                )

            if record.min_amount < 0:
                raise ValidationError(
                    f'Minimum amount cannot be negative for bracket "{record.name}"'
                )

    @api.constrains('approver_ids')
    def _check_approvers(self):
        """Ensure at least one approver is assigned"""
        for record in self:
            if not record.approver_ids:
                raise ValidationError(
                    f'Bracket "{record.name}" must have at least one approver assigned.'
                )

    def name_get(self):
        """Custom display name showing amount range and location"""
        result = []
        for record in self:
            name = record.name
            if record.location_id:
                name = f"{name} ({record.location_id.name})"

            # Add amount range
            if record.max_amount > 0:
                amount_range = f"{record.min_amount:,.0f} - {record.max_amount:,.0f}"
            else:
                amount_range = f"{record.min_amount:,.0f}+"

            name = f"{name} [{amount_range} {record.currency_id.symbol}]"
            result.append((record.id, name))

        return result

    @api.model
    def find_applicable_bracket(self, amount, location_id=None, company_id=None):
        """
        Find the applicable approval bracket for a given amount and location.

        Logic:
        - Each bracket is tied to a specific location (Magasin, Pharmacy, Maintenance)
        - Brackets are matched based on: location + amount range
        - Returns the bracket with highest priority (lowest sequence, then highest min_amount)

        :param amount: Purchase order total amount
        :param location_id: Destination location ID (required - always set in PO workflow)
        :param company_id: Company ID (defaults to current company)
        :return: purchase.approval.bracket record or empty recordset
        """
        if not company_id:
            company_id = self.env.company.id

        # Build domain for bracket search
        domain = [
            ('location_id', '=', location_id),  # Location is ALWAYS specified
            ('min_amount', '<=', amount),
            ('company_id', '=', company_id),
            ('active', '=', True),
        ]

        # Add max_amount condition (0 means unlimited)
        domain.append('|')
        domain.append(('max_amount', '>=', amount))
        domain.append(('max_amount', '=', 0))

        # Search and return the highest priority bracket
        # Order by: sequence ASC (lower = higher priority), then min_amount DESC (highest matching threshold)
        bracket = self.search(domain, order='sequence asc, min_amount desc', limit=1)

        return bracket

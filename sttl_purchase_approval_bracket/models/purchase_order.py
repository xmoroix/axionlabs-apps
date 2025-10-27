# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Computed field to get destination location from picking type
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        related='picking_type_id.default_location_dest_id',
        store=True,
        readonly=True,
        help='Destination location from the picking type. '
             'This affects which approval bracket is applied.'
    )

    # Track which approval bracket was applied
    approval_bracket_id = fields.Many2one(
        'purchase.approval.bracket',
        string='Approval Bracket',
        readonly=True,
        help='The approval bracket that applies to this purchase order'
    )

    # Track the specific approvers for this PO
    bracket_approver_ids = fields.Many2many(
        'res.users',
        'purchase_order_bracket_approver_rel',
        'order_id',
        'user_id',
        string='Bracket Approvers',
        readonly=True,
        help='Approvers from the matched bracket (for reference only)'
    )

    def _find_applicable_bracket(self):
        """
        Find the applicable approval bracket for this purchase order.

        :return: purchase.approval.bracket record or empty recordset
        """
        self.ensure_one()

        return self.env['purchase.approval.bracket'].find_applicable_bracket(
            amount=self.amount_total,
            location_id=self.destination_location_id.id if self.destination_location_id else None,
            company_id=self.company_id.id
        )

    def _create_approval_notifications(self):
        """
        Send notifications to approvers when PO requires approval.
        """
        self.ensure_one()

        if not self.bracket_approver_ids:
            return

        # Get or create the approval activity type
        activity_type = self.env.ref(
            'sttl_purchase_approval_bracket.mail_activity_type_purchase_approval',
            raise_if_not_found=False
        )

        if not activity_type:
            # Fallback to default 'To Do' activity type
            activity_type = self.env.ref('mail.mail_activity_data_todo')

        # Create activity for each approver
        for approver in self.bracket_approver_ids:
            self.activity_schedule(
                activity_type_id=activity_type.id,
                summary=f'Purchase Order Approval Required: {self.name}',
                note=f'Purchase Order <a href="#" data-oe-model="purchase.order" data-oe-id="{self.id}">{self.name}</a> '
                     f'from {self.create_uid.name} requires your approval.<br/><br/>'
                     f'<b>Supplier:</b> {self.partner_id.name}<br/>'
                     f'<b>Total Amount:</b> {self.amount_total:,.2f} {self.currency_id.symbol}<br/>'
                     f'<b>Destination Location:</b> {self.destination_location_id.name if self.destination_location_id else "N/A"}<br/>'
                     f'<b>Bracket:</b> {self.approval_bracket_id.name}<br/><br/>'
                     f'Please review and approve this purchase order.',
                user_id=approver.id
            )

        # Post a message to chatter to notify approvers
        approver_names = ', '.join(self.bracket_approver_ids.mapped('name'))
        self.message_post(
            body=f'<p>Purchase Order requires approval.</p>'
                 f'<ul>'
                 f'<li><b>Amount:</b> {self.amount_total:,.2f} {self.currency_id.symbol}</li>'
                 f'<li><b>Bracket:</b> {self.approval_bracket_id.name}</li>'
                 f'<li><b>Approvers:</b> {approver_names}</li>'
                 f'</ul>',
            subject=f'Approval Required: {self.name}',
            message_type='notification',
            partner_ids=self.bracket_approver_ids.mapped('partner_id').ids,
            subtype_xmlid='mail.mt_comment'
        )

    def _needs_approval(self):
        """
        Override Odoo's approval check to use our bracket system.
        This replaces Odoo's simple amount check with our bracket-based logic.

        :return: True if approval is required, False otherwise
        """
        self.ensure_one()

        # Find applicable bracket
        bracket = self._find_applicable_bracket()

        if bracket:
            # Store bracket info
            self.write({
                'approval_bracket_id': bracket.id,
                'bracket_approver_ids': [(6, 0, bracket.approver_ids.ids)]
            })

            # Check if current user is an approver
            if self.env.user in bracket.approver_ids:
                # User is an approver - they can approve directly
                return False

            # Approval is needed
            return True

        # No bracket applies - no approval needed
        return False

    def button_confirm(self):
        """
        Override button_confirm to use our bracket approval logic.
        This replaces Odoo's default approval condition.
        """
        for order in self:
            # Check if approval is needed using our bracket system
            if order.state in ('draft', 'sent') and order._needs_approval():
                # Set to 'to approve' state (Odoo's standard state)
                order.write({'state': 'to approve'})

                # Send notifications to approvers
                order._create_approval_notifications()

                # Return without confirming (stay in 'to approve' state)
                return True

        # Proceed with standard confirmation
        return super(PurchaseOrder, self).button_confirm()

    def button_approve(self, force=False):
        """
        Override button_approve to validate approvers and send notifications.
        """
        for order in self:
            # If bracket approvers are set, validate the user
            if not force and order.bracket_approver_ids:
                if self.env.user not in order.bracket_approver_ids:
                    from odoo.exceptions import UserError
                    raise UserError(
                        f'You are not authorized to approve this purchase order.\n\n'
                        f'Authorized approvers: {", ".join(order.bracket_approver_ids.mapped("name"))}'
                    )

            # Mark approval activities as done
            order.activity_feedback(['sttl_purchase_approval_bracket.mail_activity_type_purchase_approval'])

            # Notify the original creator
            if order.create_uid != self.env.user and order.bracket_approver_ids:
                order.message_post(
                    body=f'<p>Your Purchase Order has been <b>approved</b> by {self.env.user.name}.</p>'
                         f'<ul>'
                         f'<li><b>Supplier:</b> {order.partner_id.name}</li>'
                         f'<li><b>Total Amount:</b> {order.amount_total:,.2f} {order.currency_id.symbol}</li>'
                         f'</ul>',
                    subject=f'Purchase Order Approved: {order.name}',
                    message_type='notification',
                    partner_ids=[order.create_uid.partner_id.id],
                    subtype_xmlid='mail.mt_comment'
                )

        # Call Odoo's standard approval method
        return super(PurchaseOrder, self).button_approve(force=force)

    def button_cancel(self):
        """
        Override button_cancel to send notification when PO is cancelled during approval.
        """
        for order in self:
            # If PO was in to approve state, notify the creator
            if order.state == 'to approve' and order.create_uid != self.env.user and order.bracket_approver_ids:
                order.message_post(
                    body=f'<p>Your Purchase Order has been <b>cancelled</b> by {self.env.user.name}.</p>'
                         f'<ul>'
                         f'<li><b>Supplier:</b> {order.partner_id.name}</li>'
                         f'<li><b>Total Amount:</b> {order.amount_total:,.2f} {order.currency_id.symbol}</li>'
                         f'</ul>',
                    subject=f'Purchase Order Cancelled: {order.name}',
                    message_type='notification',
                    partner_ids=[order.create_uid.partner_id.id],
                    subtype_xmlid='mail.mt_comment'
                )

            # Mark approval activities as done
            order.activity_feedback(['sttl_purchase_approval_bracket.mail_activity_type_purchase_approval'])

        # Proceed with standard cancellation
        return super(PurchaseOrder, self).button_cancel()

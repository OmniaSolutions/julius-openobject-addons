# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _

    
class sale_order(orm.Model):
    _inherit = 'sale.order'
    
    def _calc_amount_untaxed_financial_discounted(self, cr, uid, ids,name, args, context=None):
        if context is None:
            context = {}
        res = {}
        for sale_order in self.browse(cr, uid, ids, context=context):
            amount_untaxed = sale_order.amount_untaxed
            discount = (100 - sale_order.financial_discount_percentage) / 100
            amount_untaxed_financial_discounted = amount_untaxed * discount
            res[sale_order.id] = amount_untaxed_financial_discounted
        return res
    
    def _calc_amount_tax_financial_discounted(self, cr, uid, ids,name, args, context=None):
        if context is None:
            context = {}
        res = {}
        for sale_order in self.browse(cr, uid, ids, context=context):
            amount_tax = sale_order.amount_tax
            discount = (100 - sale_order.financial_discount_percentage) / 100
            amount_tax_financial_discounted = amount_tax * discount
            res[sale_order.id] = amount_tax_financial_discounted
        return res
    
    def _calc_amount_total_financial_discounted(self, cr, uid, ids,name, args, context=None):
        if context is None:
            context = {}
        res = {}
        for sale_order in self.browse(cr, uid, ids, context=context):
            amount_total_financial_discounted = sale_order.amount_untaxed_financial_discounted + sale_order.amount_tax_financial_discounted
            res[sale_order.id] = amount_total_financial_discounted
        return res
    
    def _check_if_financial_discount(self, cr, uid, ids,name, args, context=None):
        if context is None:
            context = {}
        res = {}
        for sale_order in self.browse(cr, uid, ids, context=context):
            res[sale_order.id] = False
            for line in sale_order.order_line:
                if line.financial_discount == True:
                    res[sale_order.id] = True
                    break
        return res
    
    _columns = {
            'financial_discount_percentage' : fields.float('Financial Discount Percentage'),
            'amount_untaxed_financial_discounted' : fields.function(_calc_amount_untaxed_financial_discounted,string='Untaxed Amount With Financial Discount', readonly=True),
            'amount_tax_financial_discounted' : fields.function(_calc_amount_tax_financial_discounted, string='Taxes With Financial Discount', readonly=True),
            'amount_total_financial_discounted' : fields.function(_calc_amount_total_financial_discounted, string='Total With Financial Discount', readonly=True),
            'financial_discount_is_present' : fields.function(_check_if_financial_discount, string='Financial Discount Present', readonly=True, type="boolean"),
    }
    
#     def action_button_confirm(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         self.generate_global_discount(cr, uid, ids, context=context)
#         return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)

    def generate_financial_discount(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_obj = self.pool.get('sale.order.line')
        for sale_order in self.browse(cr, uid, ids, context=context):
            if sale_order.financial_discount_percentage != 0.00:
                discount =  sale_order.financial_discount_percentage / 100
                res = 0
                for line in sale_order.order_line:
                    if line.financial_discount == True:
                        line_obj.unlink(cr, uid, [line.id], context=context)
                    else:
                        qty = line.product_uom_qty
                        pu = line.price_unit
                        sub = qty * pu
                        res += sub
                discount_value = res * discount
                data_obj = self.pool.get('ir.model.data')
                model, product_id = data_obj.get_object_reference(cr, uid, 'financial_discount', 'product_financial_discount')
                res = line_obj.product_id_change(cr, uid, [],
                    pricelist=sale_order.pricelist_id.id,
                    product=product_id, qty=1,
                    partner_id=sale_order.partner_id.id,
                    lang=sale_order.partner_id.lang, update_tax=True,
                    date_order=sale_order.date_order,
                    fiscal_position=sale_order.fiscal_position,
                    context=context)
                value = res.get('value')
                if value:
                    tax_ids = value.get('tax_id') and \
                        [(6, 0, value.get('tax_id'))] or [(6, 0, [])]
                    value.update({
                        'financial_discount': True,
                        'price_unit': -discount_value,
                        'order_id': sale_order.id,
                        'product_id': product_id,
                        'product_uom_qty': 1,
                        'product_uos_qty': 1,
                        'tax_id': tax_ids, 
                    })
                    line_obj.create(cr, uid, value, context=context)
                    self.write(cr, uid, sale_order.id, {
                        'financial_discount_percentage': 0.00,
                        }, context=context)
        return True

class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'
    
    _columns = {
        'financial_discount' : fields.boolean('Global Discount')
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
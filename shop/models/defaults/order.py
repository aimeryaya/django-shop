# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from shop.models import order


class Order(order.BaseOrder):
    """Default materialized model for Order"""
    number = models.PositiveIntegerField(_("Order Number"), null=True, default=None, unique=True)
    shipping_address_text = models.TextField(_("Shipping Address"), blank=True, null=True,
        help_text=_("Shipping address at the moment of purchase."))
    billing_address_text = models.TextField(_("Billing Address"), blank=True, null=True,
        help_text=_("Billing address at the moment of purchase."))

    class Meta:
        verbose_name = pgettext_lazy('order_models', "Order")
        verbose_name_plural = pgettext_lazy('order_models', "Orders")

    def get_or_assign_number(self):
        """
        Set a unique number to identify this Order object. The first 4 digits represent the
        current year. The last five digits represent a zero-padded incremental counter.
        """
        if self.number is None:
            epoch = timezone.now().date()
            epoch = epoch.replace(epoch.year, 1, 1)
            aggr = Order.objects.filter(number__isnull=False, created_at__gt=epoch).aggregate(models.Max('number'))
            try:
                epoc_number = int(str(aggr['number__max'])[4:]) + 1
                self.number = int('{0}{1:05d}'.format(epoch.year, epoc_number))
            except (KeyError, ValueError):
                # the first order this year
                self.number = int('{0}00001'.format(epoch.year))
        return self.get_number()

    def get_number(self):
        number = str(self.number)
        return '{}-{}'.format(number[:4], number[4:])

    @classmethod
    def resolve_number(cls, number):
        bits = number.split('-')
        return dict(number=''.join(bits))

    def populate_from_cart(self, cart, request):
        self.shipping_address_text = cart.shipping_address.as_text() if cart.shipping_address else ''
        self.billing_address_text = cart.billing_address.as_text() if cart.billing_address else ''

        # in case one of the addresses was None, the customer presumably intended the other one.
        if not self.shipping_address_text:
            self.shipping_address_text = self.billing_address_text
        if not self.billing_address_text:
            self.billing_address_text = self.shipping_address_text
        super(Order, self).populate_from_cart(cart, request)

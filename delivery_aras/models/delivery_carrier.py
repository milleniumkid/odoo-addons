# Copyright 2024 Ahmet Yiğit Budak (https://github.com/yibudak)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Copyright 2024 Ismail Cagan Yilmaz (https://github.com/milleniumkid)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import phonenumbers
from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
from .aras_request import ArasRequest
from lxml import etree
from datetime import datetime

ARAS_OPERATION_CODES = {
    1: ("Çıkış Şubesinde", "in_transit"),
    2: ("Yolda", "in_transit"),
    3: ("Teslimat Şubesinde", "in_transit"),
    4: ("Teslimatta", "in_transit"),
    5: ("Parçalı Teslimat", "customer_delivered"),
    6: ("Teslim Edildi", "customer_delivered"),
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("aras", "Aras Kargo")],
        ondelete={"aras": "cascade"},
        )

    aras_username = fields.Char(string="Username", help="Aras Username")
    aras_password = fields.Char(string="Password", help="Aras Password")
    aras_query_username = fields.Char(
        string="Query Username", help="Aras Query Username"
    )
    aras_query_password = fields.Char(
        string="Query Password", help="Aras Query Password"
    )
    aras_customer_code = fields.Char(string="Customer Code", help="Aras Customer Code")

    def _get_aras_credentials(self):
        """Access key is mandatory for every request while group and user are
        optional"""
        credentials = {
            "prod": self.prod_environment,
            "username": self.aras_username,
            "password": self.aras_password,
            "query_username": self.aras_query_username,
            "query_password": self.aras_query_password,
            "customer_code": self.aras_customer_code,
        }
        return credentials

    def _aras_address(self, partner):
        """Sender address is the address of the company, required field."""
        return partner._display_address()

    def _aras_phone_number(self, partner, priority="mobile"):
        """
        Aras requires phone number without spaces and country code.
        We use priority selector to handle two different phone numbers.
        :param partner: recordset res.partner
        :param priority: string
        :return: phone number without spaces and country code
        """
        priority_field = getattr(partner, priority)
        if priority_field:
            return phonenumbers.format_number(
                phonenumbers.parse(priority_field, partner.country_id.code or "TR"),
                phonenumbers.PhoneNumberFormat.E164,
            ).lstrip("+9")
        elif partner.phone or partner.mobile:
            return phonenumbers.format_number(
                phonenumbers.parse(
                    partner.phone or partner.mobile, partner.country_id.code or "TR"
                ),
                phonenumbers.PhoneNumberFormat.E164,
            ).lstrip("+9")
        else:
            raise ValidationError(
                _(
                    "%s\nPartner's phone number is missing."
                    " It's a required field for dispatch." % partner.name
                )
            )

    def _prepare_aras_piece_details(self, picking):
        """It's required to write down product barcodes for Piece Detail"""
        self.ensure_one()
        piece_details = []
        for _ in range(max(picking.carrier_package_count, 1)):
            piece_details.append(
                {
                    # This is a bit tricky, we need a unique barcode for
                    # each package, so we can use the same method as we use
                    # for the integration code.
                    "BarcodeNumber": self._get_ref_number(),
                }
            )
        return {"PieceDetail": piece_details}

    def _prepare_aras_shipping(self, picking):
        """Convert picking values for Aras Kargo api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        # We'll compose the request via some diferenced parts, like label settings,
        # address options, incoterms and so. There are lots of thing to take into
        # account to acomplish a properly formed request.
        vals = {}
        vals.update(
            {
                "InvoiceNumber": picking.name,
                "IntegrationCode": self._get_ref_number(),
                "ReceiverName": picking.partner_id.display_name[
                    :100
                ],  # Aras Kargo has a 100 characters limit for receiver name
                "ReceiverAddress": self._aras_address(picking.partner_id),
                "ReceiverPhone1": self._aras_phone_number(
                    picking.partner_id, priority="mobile"
                ),
                "ReceiverPhone2": self._aras_phone_number(
                    picking.partner_id, priority="phone"
                ),
                "ReceiverCityName": picking.partner_id.state_id.name,
                "ReceiverTownName": picking.partner_id.district_id.name,
                "TradingWaybillNumber": picking.name,
                "PayorTypeCode": (
                    1 if self.payment_type == "sender_pays" else 2
                ),  # 1 = Sender, 2 = Receiver pays
                "IsWorldWide": 0,
                "VolumetricWeight": max(picking.picking_total_weight, 1),
                # "PieceCount": max(picking.carrier_package_count, 1),
            }
        )
        # piece_details = self._prepare_aras_piece_details(picking)
        # vals.update({"PieceDetails": piece_details})
        return vals

    def aras_send_shipping(self, pickings):
        """Send booking request to Aras
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        aras_request = ArasRequest(**self._get_aras_credentials())
        result = []
        for picking in pickings:
            vals = self._prepare_aras_shipping(picking)
            try:
                response = aras_request._send_shipping(vals)

            except Exception as e:
                raise e

            finally:
                self._aras_log_request(aras_request)

            if not response:
                result.append(vals)
                continue
            vals["tracking_number"] = response.OrgReceiverCustId
            vals["exact_price"] = 0.0
            result.append(vals)
        return result

    # @api.model
    def _aras_log_request(self, aras_request):
        """Helper to write raw request/response to the current picking. If debug
        is active in the carrier, those will be logged in the ir.logging as well"""
        aras_last_request = aras_last_response = False
        try:
            aras_last_request = etree.tostring(
                aras_request.history.last_sent["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
            aras_last_response = etree.tostring(
                aras_request.history.last_received["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
        # Don't fail hard on this. Sometimes zeep could not be able to keep history
        except Exception:
            return
        # Debug must be active in the carrier
        self.log_xml(aras_last_request, "aras_request")
        self.log_xml(aras_last_response, "aras_response")

    def aras_cancel_shipment(self, pickings):
        """Cancel the expedition
        :param pickings - stock.picking recordset
        :returns bool
        """
        aras_request = ArasRequest(**self._get_aras_credentials())
        for picking in pickings.filtered("carrier_tracking_ref"):
            if hasattr(
                self, "%s_tracking_state_update" % self.delivery_type
            ):  # check state before cancel
                getattr(self, "%s_tracking_state_update" % self.delivery_type)(picking)

            if picking.delivery_state not in [
                "shipping_recorded_in_carrier",
                "canceled_shipment",
            ]:
                raise ValidationError(
                    _(
                        "You can't cancel a shipment that already has been sent to Aras Kargo"
                    )
                )

            try:
                aras_request._cancel_shipment(picking.carrier_tracking_ref)
            except Exception as e:
                raise e
            finally:
                self._aras_log_request(aras_request)
        return True

    def aras_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        return (
            "https://kargotakip.araskargo.com.tr/mainpage.aspx?code=%s"
            % picking.shipping_number
        )

    def aras_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        aras_request = ArasRequest(**self._get_aras_credentials())

        try:
            response = aras_request._query_shipment(picking)
        except Exception as e:
            raise e
        finally:
            self._aras_log_request(aras_request)

        if not response:
            return False

        if isinstance(response, list):
            response = response[-1]

        vals = {
            "tracking_state": "%s - %s - %s"
            % (
                response["DURUMU"],
                response["DURUM_EN"],
                response.get("IADE_SEBEBI", ""),
            ),
            "delivery_state": ARAS_OPERATION_CODES[int(response["DURUM_KODU"])][1],
            "shipping_number": response["KARGO_TAKIP_NO"],
            "carrier_shipping_cost": float(response["TUTAR"]),
            "carrier_total_deci": float(response["HACIMSEL_AGIRLIK"]),
        }

        if picking.tracking_state != vals["tracking_state"]:
            vals.update(self._aras_update_tracking_history(picking, response, vals))

        if vals["delivery_state"] == "customer_delivered":
            vals.update(self._aras_delivered(response))

        picking.write(vals)
        return True

    def _aras_update_tracking_history(self, picking, response, vals):
        """Update tracking history"""
        self.ensure_one()
        new_state = "%s - %s" % (response["ISLEM_TARIHI"], vals["tracking_state"])
        if not picking.tracking_state_history:
            vals["tracking_state_history"] = new_state
        else:
            vals["tracking_state_history"] = (
                picking.tracking_state_history + "\n" + new_state
            )
        return vals

    def _aras_delivered(self, response):
        """Update delivered fields"""
        self.ensure_one()
        return {
            "date_delivered": datetime.fromisoformat(response["ISLEM_TARIHI"]),
            "carrier_received_by": response.get("TESLIM_ALAN", ""),
        }

    def aras_carrier_get_label(self, picking):
        """
        Aras Kargo doesn't provide label for shipments.
        They are not implemented common label on their systems.
        """
        raise NotImplementedError(
            _("Aras Kargo API doesn't provide methods to print label.")
        )

    def aras_rate_shipment(self, order):
        """There's no public API so use rules for calculation."""
        return self.base_on_rule_rate_shipment(order)

    def aras_get_rate(self, order):
        """Get delivery price for Aras"""
        return self.base_on_rule_get_rate(order)

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID
import logging
import time

import requests




# from odoo.addons.hw_proxy.controllers import main as hw_proxy


_logger = logging.getLogger(__name__)

class zwave_homeassistant(models.Model):
    _name = 'zwave.homeassistant'

    url = 'http://localhost:8123/api'
    headers = {
        "Authorization":"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiNGRmZDIwNjExYTQ0ODllYWQwODAzYjc0MGQwZWQzNiIsImlhdCI6MTU3OTA3Mjc3OCwiZXhwIjoxODk0NDMyNzc4fQ.fQr2uoSJ2o9kYyOhdU7CvI5ulPprBapaGHaz12epR78",
        "content-type":"application/json"
    }
    data = '{"entity_id":"lock.danalock"}'

    # @api.model
    # def lockedstart_test(self):
    #     for driver in hw_proxy.drivers:
    #         hw_proxy.drivers[driver].lockedstart()

    @api.model
    def get_state(self):
        state_url = self.url + '/states/lock.danalock'
        response = requests.get(state_url, headers=self.headers)
        state = response.json()['state']
        _logger.info('State = %s'%state)
        return state
    
    @api.model
    def lock_operation(self, barcode):
        barcode_check = self.env['hr.employee'].search([('barcode', '=', barcode)])
        if barcode_check:    
            state = self.get_state()
            if state == 'locked':
                unlock_url = self.url + '/services/lock/unlock'
                requests.post(unlock_url, data=self.data, headers=self.headers)
                time.sleep(10)
                lock_url = self.url + '/services/lock/lock'
                requests.post(lock_url, data=self.data, headers=self.headers)
            elif state == 'unlocked':
                lock_url = self.url + '/services/lock/lock'
                requests.post(lock_url, data=self.data, headers=self.headers)
            else:
                _logger.error("state = %s"%state)
        else:
            _logger.info("Barcode does not match")

class zwave_device(models.Model):
    _name = 'zwave.devices'

    entity_id = fields.Char()

    url = 'http://localhost:8123/api'

    def get_state(self):
        state_url = self.url + 'states/' + self.entity_id
        response = requests.get(state_url)
        return state


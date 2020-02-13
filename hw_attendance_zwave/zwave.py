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
from odoo.tools.config import config
from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID
import logging
import time

import requests



#logging.getLogger('openzwave').addHandler(logging.NullHandler())
#logging.basicConfig(level=logging.DEBUG)

# logger = logging.getLogger('openzwave')

_logger = logging.getLogger(__name__)

# CHECK IF OPENZWAVE IS INSTALLED. ELSE THROW EXCEPTION
import sys, os
import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
import six
if six.PY3:
    from pydispatch import dispatcher
else:
    from louie import dispatcher



# for arg in sys.argv:
#     if arg.startswith("--device"):
#         temp,device = arg.split("=")
#     elif arg.startswith("--log"):
#         temp,log = arg.split("=")
#     elif arg.startswith("--sniff"):
#         temp,sniff = arg.split("=")
#         sniff = float(sniff)
#     elif arg.startswith("--help"):
#         _logger.info("help : ")
#         _logger.info("  --device=/dev/yourdevice ")
#         _logger.info("  --log=Info|Debug")






config_path = config.get('zwave_config_path', '/usr/local/lib/python3.6/dist-packages/python_openzwave/ozw_config')
user_path = config.get('zwave_user_path', '/usr/share/odoo-hw/hw_attendance_zwave/ozw_log')


# configure these in config?
device="/dev/ttyACM0"
log="Always"
sniff=300.0


options = ZWaveOption(device, \
  config_path=config_path, \
  user_path=user_path, cmd_line="")
options.set_log_file("OZW_Log.log")
options.set_append_log_file(True)
options.set_console_output(False)
options.set_save_log_level(log)
options.set_logging(True)
options.lock()

#Create a network object
_logger.info("Carl user_path: %s"%config_path)
network = ZWaveNetwork(options, autostart=False)


def notification_catcher(*args, **kw):
    # _logger.info(args)
    _logger.info("Carl Z-Wave Notification: %s"%str(kw))

#We connect to the louie dispatcher
dispatcher.connect(notification_catcher)

# def all nodes_queried(**kw):
#     return break

network.start()




class zwave_network(models.Model):
    _name = 'zwave.network'

    device = fields.Char(string="Controller path", default="/dev/ttyACM0")
    # change to selection
    log = fields.Char(string="Logging enabled", default="Always")
    sniff = fields.Float(string="sniff", default=300.0)
    home_id = fields.Char(string="Home network ID", compute="get_home_id")
    node_ids = fields.One2many('zwave.node', 'network_id', string="Nodes on the network")


    # def notification_catcher(*args, **kw):
    #     # _logger.info(args)
    #     _logger.info("Carl Z-Wave Notification: %s"%str(kw))

    # #We connect to the louie dispatcher
    # dispatcher.connect(notification_catcher)

    # displays the dispatcher notifications

    # While doing this the node to connect must be in inclusion mode and the network key must be set in options.xml
    @api.multi
    def get_home_id(self):
        return network.home_id

    @api.multi
    def add_secure_node(self):
        _logger.info("Trying to connect a secure node to network...")
        try:
            node_state = network.controller.add_node(doSecurity=True)
            # if ZWaveNetwork.SIGNAL_NODE.name
        except:
            _logger.info("something went wrong")

    @api.multi
    def remove_node(self):
        _logger.info("Trying to remove a node from network...")
        try:
            danalock_state = network.controller.remove_node()
        except:
            _logger.info("something went wrong")
        _logger.info("{} nodes were found.".format(network.nodes_count))

    @api.model
    def get_network(self):
        return network

    @api.model
    def create_network(self):
        #Create a network object
        network = ZWaveNetwork(options, autostart=False)    

    @api.model
    def state(self):
        return network.state
    
    @api.multi
    def alert_state(self):
        message = 'No response'
        if network.state == 0:
            message = 'Stopped'
        elif network.state == 1:
            message = 'Failed'
        elif network.state == 3:
            message = 'Resetted'
        elif network.state == 5:
            message = 'Started'
        elif network.state == 7:
            message = 'Awakened'
        elif network.state == 10:
            message = 'Ready'

        raise Warning("Network state: %s"%message)

    @api.multi
    def start(self):
        if self.state() != 10 or self.state() != 7:
            network.start()
            _logger.info("***** Waiting for z-wave network to become ready : ")
            for i in range(0,90):
                if network.state>=network.STATE_READY:
                    _logger.info("***** Network is ready")
                    break
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                    time.sleep(1.0)
        else:
            raise Warning("Network is already running")

        #verify that it starts?


    @api.multi
    def stop(self):
        network.stop()
        # Verify that it stops?

    def list_nodes(self):
        _logger.info("Carl Nodes on network: %s"%str(network.nodes))

    @api.multi
    def map_nodes(self):
        for node in network.nodes:
            _node = network.nodes[node]
            node_type = ''
            if 'lock' in _node.type.lower():
                node_type = 'lock'
            elif 'controller' in _node.type.lower():
                node_type = 'controller'
            else:
                node_type = 'undeclared'


            if not self.env['zwave.node'].search([('node_id', '=', node)]):

                self.env['zwave.node'].create({
                    'node_id':node,
                    'name':_node.product_name,
                    'node_type':node_type,
                    'network_id': self.id
                    })



class zwave_node(models.Model):
    _name = 'zwave.node'

    node_id = fields.Integer(string="Node ID", required=True)
    name = fields.Char(string="Node name", required=True)
    node_type = fields.Selection([('controller', 'A network controller'),('lock', 'A secure node'), ('undeclared', 'An undeclared node')])
    network_id = fields.Many2one('zwave.network', string="Network associated to node")


    lock_value = fields.Integer(string='The ZWaveValue ID', compute='get_doorlock_value')
    # time is an integer where 0 == no autolock and 1 - 2147483647
    lock_delay = fields.Integer(string='Delay before locking', default='10')


    @api.depends('node_id')
    def get_doorlock_value(self):
        lock_values = network.nodes[self.node_id].get_doorlocks()
        for val, value_object in lock_values.items():
            _logger.info("Returning value: %s"%val)
            self.lock_value = val

    @api.model
    def get_locked_status(self):
        locks = network.nodes[self.node_id].get_doorlocks()
        for val, value_object in locks.items():
            return value_object.data

    @api.multi
    def alert_autolock(self):
        lock = self.get_node()
        autolock_value = lock.get_values(label='Autolock')
        for val, value_object in autolock_value.items():
            raise Warning(value_object.data)

    @api.multi
    def get_autolock(self):
        lock = self.get_node()
        autolock_value = lock.get_values(label='Autolock')
        for val, value_object in autolock_value.items():
            return value_object

    # time is an integer where 0 == no autolock and 1 - 2147483647
    @api.multi
    def set_autolock(self):
        lock_delay = time or self.lock_delay
        autolock = self.get_autolock()
        autolock.data = self.lock_delay
        autolock.refresh()

    @api.multi
    def alert_state(self):
        locks = network.nodes[self.node_id].get_doorlocks()
        for val, value_object in locks.items():
            raise Warning(value_object.data)

    @api.model
    def get_node(self):
        _logger.info("Returning Node: %s"%network.nodes[self.node_id])
        return network.nodes[self.node_id]

    @api.multi
    def lock(self):

        lock = self.get_node()
        # Setting lock to True = locked
        lock.set_doorlock(self.lock_value, True)

    @api.multi
    def unlock(self):
        # value = self.get_doorlock_value()
        lock = self.get_node()
        # Setting lock to False = unlocked
        lock.set_doorlock(self.lock_value, False)



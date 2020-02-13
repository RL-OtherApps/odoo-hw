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
import odoo

import traceback

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty
import time
from select import select
from threading import Thread, Lock

from odoo.addons.hw_proxy.controllers import main as hw_proxy
from odoo.modules.registry import Registry

from os import listdir
from os.path import join, isdir

import evdev


_logger = logging.getLogger(__name__)

scanner_thread = None

class RFID_Devices(models.Model):
    _name = "rfid.devices"
    
    # ~ listDevices = fields.Char(string="Available devices")
    device_path = fields.Char(string="Path to device")
    device_name = fields.Char(string="Device name")
    thread_state = fields.Boolean(string="State")

    
    
    
    # ~ def devices(self):
        

class RFID_ScannerDevice():
    def __init__(self, path):
        self.evdev = evdev.InputDevice(path)
        self.evdev.grab()

        self.barcode = []
        self.shift = False

class RFID_Scanner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.lock = Lock()
        self.status = {'status':'connecting', 'messages':[]}
        self.input_dir = '/dev/input/by-id/'
        self.open_devices = []
        self.barcodes = Queue()
        self.env = None
        self.keymap = {
            2: ("1","!"),
            3: ("2","@"),
            4: ("3","#"),
            5: ("4","$"),
            6: ("5","%"),
            7: ("6","^"),
            8: ("7","&"),
            9: ("8","*"),
            10:("9","("),
            11:("0",")"),
            12:("-","_"),
            13:("=","+"),
            # 14 BACKSPACE
            # 15 TAB
            16:("q","Q"),
            17:("w","W"),
            18:("e","E"),
            19:("r","R"),
            20:("t","T"),
            21:("y","Y"),
            22:("u","U"),
            23:("i","I"),
            24:("o","O"),
            25:("p","P"),
            26:("[","{"),
            27:("]","}"),
            # 28 ENTER
            # 29 LEFT_CTRL
            30:("a","A"),
            31:("s","S"),
            32:("d","D"),
            33:("f","F"),
            34:("g","G"),
            35:("h","H"),
            36:("j","J"),
            37:("k","K"),
            38:("l","L"),
            39:(";",":"),
            40:("'","\""),
            41:("`","~"),
            # 42 LEFT SHIFT
            43:("\\","|"),
            44:("z","Z"),
            45:("x","X"),
            46:("c","C"),
            47:("v","V"),
            48:("b","B"),
            49:("n","N"),
            50:("m","M"),
            51:(",","<"),
            52:(".",">"),
            53:("/","?"),
            # 54 RIGHT SHIFT
            57:(" "," "),
        }

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def set_status(self, status, message = None):
        if status == self.status['status']:
            if message != None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Barcode Scanner Error: '+message)
        elif status == 'disconnected' and message:
            _logger.info('Disconnected Barcode Scanner: %s', message)

    def get_devices(self):
        try:
            if not evdev:
                return []

            if not isdir(self.input_dir):
                return []

            new_devices = [device for device in listdir(self.input_dir)
                           if join(self.input_dir, device) not in [dev.evdev.fn for dev in self.open_devices]]
            scanners = [device for device in new_devices
                        if (('kbd' in device) and ('keyboard' not in device.lower()))
                        or ('barcode' in device.lower()) or ('scanner' in device.lower())]

            for device in scanners:
                # Leo was here
                # ~ _logger.warn("leowashere %s"%device)
                if not device == 'usb-Sycreader_RFID_Technology_Co.__Ltd_SYC_ID_IC_USB_Reader_08FF20140315-event-kbd':
                    _logger.debug('opening device %s', join(self.input_dir,device))
                    self.open_devices.append(RFID_ScannerDevice(join(self.input_dir,device)))

            if self.open_devices:
                self.set_status('connected','Connected to '+ str([dev.evdev.name for dev in self.open_devices]))
            else:
                self.set_status('disconnected','Barcode Scanner Not Found')

            return self.open_devices
        except Exception as e:
            self.set_status('error',str(e))
            return []

    def release_device(self, dev):
        self.open_devices.remove(dev)

    # def get_barcode(self):
        """ Returns a scanned barcode. Will wait at most 5 seconds to get a barcode, and will
            return barcode scanned in the past if they are not older than 5 seconds and have not
            been returned before. This is necessary to catch barcodes scanned while the POS is
            busy reading another barcode
        """

        self.lockedstart()

        while True:
            try:
                timestamp, barcode = self.barcodes.get(True, 5)
                if timestamp > time.time() - 5:
                    return barcode
            except Empty:
                return ''

    def get_status(self):
        self.lockedstart()
        return self.status

    def _get_open_device_by_fd(self, fd):
        for dev in self.open_devices:
            if dev.evdev.fd == fd:
                return dev

    def run(self):
        """ This will start a loop that catches all keyboard events, parse barcode
            sequences and put them on a timestamped queue that can be consumed by
            the point of sale's requests for barcode events
        """
        self.barcodes = Queue()

        barcode  = []
        shift    = False
        devices  = None

        while True: # barcodes loop
            devices = self.get_devices()

            try:
                while True: # keycode loop
                    r,w,x = select({dev.fd: dev for dev in [d.evdev for d in devices]},[],[],5)
                    if len(r) == 0: # timeout
                        break

                    for fd in r:
                        device = self._get_open_device_by_fd(fd)

                        # ~ _logger.warn("leotest %s"%device.evdev.name)
                        if not evdev.util.is_device(device.evdev.fn):
                            _logger.info('%s disconnected', str(device.evdev))
                            self.release_device(device)
                            break

                        events = device.evdev.read()

                        for event in events:
                            if event.type == evdev.ecodes.EV_KEY:
                                # _logger.debug('Evdev Keyboard event %s',evdev.categorize(event))
                                if event.value == 1: # keydown events
                                    if event.code in self.keymap:
                                        if device.shift:
                                            device.barcode.append(self.keymap[event.code][1])
                                        else:
                                            device.barcode.append(self.keymap[event.code][0])
                                    elif event.code == 42 or event.code == 54: # SHIFT
                                        device.shift = True
                                    elif event.code == 28: # ENTER, end of barcode
                                        _logger.info("Carl barcode 1: %s"%device.barcode)
                                        _logger.debug('pushing barcode %s from %s', ''.join(device.barcode), str(device.evdev))
                                        self.barcodes.put( (time.time(),''.join(device.barcode)) )
                                        timestump, test_barcode = self.barcodes.get(True)

                                        # Leo was here
                                        if device.evdev.name == 'ACS ACR1281 Dual Reader':
                                            hexa_string = test_barcode
                                            # ~ _logger.warn("leo barcode %s"%hexa_string)
                                            result = int(hexa_string, 16)

                                            test_barcode = result
                                            # ~ _logger.warn("leo barcode %s"%test_barcode)
                                        with api.Environment.manage():
                                            # Unclosed cursor might generate exception
                                            try:
                                                new_cr = Registry('Inpassering-ex-jobb').cursor()
                                                new_cr.autocommit(True)
                                                context = {}
                                                env = api.Environment(new_cr, SUPERUSER_ID, context)

                                                match = env['hr.employee'].search([('barcode', '=', test_barcode)])

                                                if match:
                                                    network = ''
                                                    # choose what method to run here. Possible?
                                                    if not env['zwave.network'].search([]):
                                                        network = env['zwave.network'].create({})
                                                    else:
                                                        network = env['zwave.network'].search([], limit=1)

                                                    if network.state() != 10:
                                                        network.start()

                                                    if not env['zwave.node'].search([]):
                                                        _logger.info("Mapping nodes")
                                                        network.map_nodes()
                                                    lock = env['zwave.node'].search([('node_id', '=', 2)], limit=1)

                                                    if lock:
                                                        state = lock.get_locked_status()
                                                        _logger.info("Lock state: %s"%state)
                                                        # if state == True:
                                                        lock.unlock()
                                                else:
                                                    _logger.info("BARCODE DOES NOT MATCH")
                                                # # elif state == False:
                                                # #     lock.lock()
                                                
                                            except Exception as e:
                                                _logger.warn(traceback.format_exc())
                                                self.set_status('Enviroment error',str(e))
                                            finally:
                                                new_cr.close()



                                        device.barcode = []
                                elif event.value == 0: #keyup events
                                    if event.code == 42 or event.code == 54: # LEFT SHIFT
                                        device.shift = False


            except Exception as e:
                _logger.warn(traceback.format_exc())
                self.set_status('error',str(e))

if evdev:
    scanner_thread = RFID_Scanner()
    hw_proxy.drivers['rfid'] = scanner_thread
    scanner_thread.lockedstart()



# class ScannerDriver(hw_proxy.Proxy):
#     @http.route('/hw_proxy/scanner', type='json', auth='none', cors='*')
#     def scanner(self):
#         return scanner_thread.get_barcode() if scanner_thread else None

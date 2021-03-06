# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019- Vertel AB (<http://vertel.se>).
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

{
    'name': 'Rfid Threading Handler',
    'version': '12.0.1',
    'category': 'hr',
    'description': """
        Handles threading and input of RFID-Devices. Overrides hw_scanner.
        Lets you input which devices to thread and not to thread as a system parameter. 
        Uses decimal input as a standard check value. Therefore:
        Lets you input which devices to convert from hexadecimal input to decimal input as a system parameter. 

""",
    'images': [],
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'website': 'http://www.vertel.se',
    'depends': ['hr_attendance', 'hw_zwave'],
    'data': ['security/ir.model.access.csv', 'views/devices_view.xml'],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:

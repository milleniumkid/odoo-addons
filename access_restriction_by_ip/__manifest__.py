##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Access Restriction By IP",
    "summary": """User Can Access His Account Only From Specified IP Address""",
    "version": "16.0.1.0.0",
    "author": "Cybrosys Techno Solutions, Altinkaya Enclosures",
    "company": "Cybrosys Techno Solutions",
    "website": "https://github.com/altinkaya-opensource/odoo-addons",
    "category": "Tools",
    "depends": ["base", "mail"],
    "external_dependencies": {
        "python": ["ipaddress"],
    },
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/allowed_ips_view.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
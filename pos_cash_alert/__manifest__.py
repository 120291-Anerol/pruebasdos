# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#################################################################################
{
  "name"                 :  "Alertas por exceso de efectivo",
  "summary"              :  """Este modulo envia alertas por exceso de efectivo""",
  "category"             :  "Point Of Sale",
  "version"              :  "1.0.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "http://www.sinergia-e.com",
  "description"          :  """Alertas en POS""",
  "live_test_url"        :  "",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                             'views/pos_config.xml',
                             'views/templates.xml',
                            ],
  "demo"                 :  ['data/pos_cash_alert_demo.xml'],
  "qweb"                 :  ['static/src/xml/pos_cash_alert.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  27,
  "currency"             :  "MXN",
  "pre_init_hook"        :  "pre_init_check",
}
from PyQt5 import QtWidgets
import window, ventu_parser, sys
import json as js


with open('locations.json', 'r', encoding='utf-8') as f:
    configs = js.load(f)

hours = {'06': '0300', '12': '0900', '18': '1500', '24': '2100'}
dir = window.Window.dir_name
fTypes = window.Window.forecast_types

parser = ventu_parser.VentuskyParser(configs, hours, fTypes, dir, fInterval=1)

app = QtWidgets.QApplication(sys.argv)
window = window.Window(ventu_parser=parser)
window.show()
sys.exit(app.exec_())
import ventu_parser, os, urllib3
from datetime import datetime, timedelta


class WindyParser(ventu_parser.VentuskyParser):
    def __init__(self, configs, hours, fTypes, screenshotsDir, fInterval=3):
        self.driver = self.create_driver()
        self.configs = configs
        self.hours = hours
        self.fTypes = fTypes
        self.fInterval = fInterval
        self.dir = screenshotsDir
        self.disabledParticlesAnimation = True

        self.urls = {}

        # списки id и xpath элементов интерфейса ventusky, которые мы удаляем,
        # чтобы сделать скриншоты
        self.invis_id_elements = ["search", "bottom", "rh-icons", "logo", "rh-bottom", "rhpane"]
        self.invis_xpath_elements = ["/html/body/div[1]/div[1]/div[1]/canvas"]

    def get_tomorrow(self, delta):
        today = datetime.today() + timedelta(days=delta)
        return today.strftime('%Y-%m-%d')

    # проверяет, загрузилась ли анимация погоды
    def is_loaded(self):
        body = self.driver.find_element_by_xpath("/html/body")
        return "load" not in body.get_attribute("class")

    def create_url(self):
        for locationName, params in self.configs.items():
            coords, scale, width, height = params.values()

            for fType in self.fTypes:
                num_gen = WindyParser.gen()  # создаем генератор чисел
                for delta in range(1, self.fInterval + 1):
                    for hour in self.hours:
                        date = self.get_tomorrow(delta)
                        url = f"https://www.windy.com/{fType},{date}-{hour},{coord},{scale}"
                        screenshot_name = f"{locationName}_{self.fTypes[fType]}_{next(num_gen)}.png"
                        self.urls[url] = (screenshot_name, width, height)

# ----------------------------------------

fTypes = {"-Precip-type-ptype?ptype": "Тип осадков"}
hours = ["15"]
coord = "60.744,49.421"
scale = "4"
class_name = "loading-path"

configs = {"Test": {
    "coords": "55.744,45.421",
    "scale": 5,
    "width": 1000,
    "height": 600
}}
# ---------------------------------------------------

parser = WindyParser(configs, hours, fTypes, f"{os.curdir}/Скрины", 4)
parser.create_url()
for url in parser.urls.keys():
    try:
        parser.launch_driver()
    except urllib3.exceptions.MaxRetryError:
        pass
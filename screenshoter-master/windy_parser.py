import io
from time import sleep

from PIL import Image
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from urllib3.exceptions import MaxRetryError
from Screenshot import Screenshot_Clipping
ss = Screenshot_Clipping.Screenshot()

import ventu_parser, os
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

class WindyParser(ventu_parser.VentuskyParser):
    def __init__(self, configs, hours, fTypes, screenshotsDir, fInterval=3):
        self.driver = self.create_driver()
        self.configs = configs
        self.hours = hours
        self.fTypes = fTypes
        self.fInterval = fInterval
        self.dir = screenshotsDir

        self.urls = {}

        # списки id и xpath элементов интерфейса ventusky, которые мы удаляем,
        # чтобы сделать скриншоты
        self.invis_id_elements = ["search", "bottom", "rh-icons", "logo", "rh-bottom", "rhpane"]
        self.invis_xpath_elements = []

    def get_tomorrow(self, delta):
        today = datetime.today() + timedelta(days=delta)
        return today.strftime('%Y%m%d')

    # проверяет, загрузилась ли анимация погоды
    def is_loaded(self):
        try:
            body = self.driver.find_element(By.CSS_SELECTOR, "body")
            sleep(1)
            return "selectedpois-favs" in body.get_attribute("class")
        except NoSuchElementException:
            return False

    def create_url(self):
        for locationName, params in self.configs.items():
            coords, scale, width, height = params.values()

            for fType in self.fTypes:
                num_gen = WindyParser.gen()  # создаем генератор чисел
                for delta in range(1, self.fInterval + 1):
                    for hour in self.hours:
                        date = self.get_tomorrow(delta)
                        print(date)
                        url = f"https://www.windy.com/ru/{fType},{date}{hour},{coords},{scale}"
                        screenshot_name = os.path.join(self.dir, locationName, f"{self.fTypes[fType]}{next(num_gen)}.png")
                        self.urls[url] = (screenshot_name, width, height)

    def launch_driver(self):
        self.create_url()
        for url, item in self.urls.items():
            screenshotName, width, height = item
            self.driver.set_window_size(width, height)
            try:
                self.drive_url(url, screenshotName)
            except Exception:
                pass

        try:
            self.driver.close()
            self.driver.quit()
        except Exception:
            pass


    def drive_url(self, url, screenshotName):
        self.driver.get(url)
        # ждем, пока загрузится
        while True:
            if self.is_loaded():
                break
        # если появится промо, то удаляем его
        try:
            promo = self.driver.find_element(By.ID, "news")
            self.driver.execute_script("""var element = arguments[0];
                                                 element.parentNode.removeChild(element);""", promo)
        except NoSuchElementException:
            pass

        # делаем элементы меню сделать невидимыми
        self.set_invisible_by_xpath()
        self.set_invisible_by_id()
        head, tail = os.path.split(screenshotName)
        if not os.path.exists(head):
            os.mkdir(head)
        ss.full_Screenshot(self.driver, save_path=head, image_name=tail)

        # body = self.driver.find_element(By.CSS_SELECTOR, "body")
        # image = body.screenshot_as_png()
        # print(image)
        # imageStream = io.BytesIO(image)
        # im = Image.open(imageStream)
        # im.save(screenshotName)

        # self.driver.get_screenshot_as_file(screenshotName)
        # sleep(1)

# ----------------------------------------


# ---------------------------------------------------
from windy_config import configs, hours, fTypes

parser = WindyParser(configs, hours, fTypes, os.curdir, 1)
parser.create_url()
for url in parser.urls.keys():
    parser.launch_driver()



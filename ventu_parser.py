
import window
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json as js

class VentuskyParser:
    def __init__(self, locations, hours, forecast_types, screenshotsDir, forecast_interval=3, delta=1):
        self.driver = VentuskyParser.create_driver()
        self.locations = locations
        self.hours = hours
        self.forecast_types = forecast_types
        self.forecast_interval = forecast_interval
        self.delta = delta
        self.dir = screenshotsDir

        # списки id и xpath элементов интерфейса ventusky, которые мы удаляем,
        # чтобы сделать скриншоты
        self.invis_id_elements = ["header", "p", "m", "l"]
        self.invis_xpath_elements = ["/html/body/menu", "/html/body/div[3]", "/html/body/div[4]", "/html/body/a[1]",
                                "/html/body/a[2]"]

    def create_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-automation")
        chrome_options.add_argument("window-size=2000,1400")
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        return driver

    # генератор чисел +1
    def gen(n=1):
        while True:
            yield str(n)
            n += 1

    # проверяет, загрузилась ли анимация погоды
    def is_loaded(self):
        xx_span = self.driver.find_elements_by_class_name("xx")
        a = xx_span[0].get_attribute("style")
        return a == ""

    # функция возвращает дату сегодня + delta дней в формате ГГГГ.мм.дд
    def get_tomorrow(self):
        today = datetime.today() + timedelta(days=self.delta)
        return today.strftime('%Y%m%d')

    # делаем невидимыми переданные элементы страницы
    def set_invisible_by_id(self):
        for html_id in self.invis_id_elements:
            e = self.driver.find_element_by_id(html_id)
            self.driver.execute_script("arguments[0].setAttribute('style','display: none')", e)

    def set_invisible_by_xpath(self):
        for xpath in self.invis_xpath_elements:
            e = self.driver.find_element_by_xpath(xpath)
            self.driver.execute_script("arguments[0].setAttribute('style','display: none')", e)

    # для каждого location генерим url
    def create_url(self, name, coords):
        for fType in self.forecast_types:
            num_gen = VentuskyParser.gen()  # создаем генератор чисел
            for delta in range(1, self.forecast_interval + 1):
                for hour in self.hours.values():
                    date = self.get_tomorrow()
                    url = f"https://www.ventusky.com/?p={coords};4&l={fType}&t={date}/{hour}"
                    print(url)
                    self.drive_url(url, name, fType, num_gen)

    def drive_url(self, url, locationName, fType, num_gen):
        self.driver.get(url)
        # ждем, пока загрузится
        while True:
            if self.is_loaded():
                break

        # если появится промо, то удаляем его
        try:
            promo = self.driver.find_element_by_id("news")
            self.driver.execute_script("""var element = arguments[0];
                                                 element.parentNode.removeChild(element);""", promo)
        except NoSuchElementException:
            pass

        # делаем элементы меню сделать невидимыми
        self.set_invisible_by_xpath()
        self.set_invisible_by_id()

        screenshot_name = f"{locationName}_{self.forecast_types[fType]}_{next(num_gen)}.png"
        self.driver.get_screenshot_as_file(f"{self.dir}/{screenshot_name}")

with open('locations.json', 'r', encoding='utf-8') as f:
    locations = js.load(f)

hours = {'06': '0300', '12': '0900', '18': '1500', '24': '2100'}
dir = window.Window.dir_name
fTypes = window.Window.forecast_types


parser = VentuskyParser(locations, hours, fTypes, dir, 1)
for name, coords in locations.items():
    parser.create_url(name, coords)


# тестируем небольшие идейки
# def test_func():
#     date = get_tomorrow(1)
#     url = "https://www.ventusky.com/?p={};4&l={}&t={}/{}".format(locations["ДФО"], list(forecast_types.keys())[0], date, "0300")
#     driver.get(url)
#     # делаем элементы меню сделать невидимыми
#     [set_invisible_by_xpath(driver, xpath) for xpath in invis_xpath_elements]
#     [set_invisible_by_id(driver, id) for id in invis_id_elements]
#     while True:
#         if is_loaded(driver):
#             break
#     driver.get_screenshot_as_file("{}_{}.png".format('test', 1))

#test_func()
#driver.quit()

# locations = {}


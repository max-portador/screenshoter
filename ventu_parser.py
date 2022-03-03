import os.path
import sys
from datetime import datetime, timedelta
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from gismeteo_urls import gismeteo_urls
from PIL import Image

path_to_driver = "./chromedriver" if sys.platform == 'linux' else "./chromedriver.exe"

css_selector_settings = "#menu-settings > a"
css_selector_checkbox = "#settings-colors > div.resp_table > div > label > div.resp_table_cell.cell2 > input[type=checkbox]"
css_selector_closebtn = "#aside_close_btn"
css_selector_basemap = "#x > canvas:nth-child(1)"
css_selector_boarders = "#x > canvas:nth-child(5)"

SNOW_ACC = 'new-snow-ac'
RAIN_ACC = 'rain-ac'


class VentuskyParser:
    def __init__(self, configs, hours, fTypes, screenshotsDir, fInterval=3):
        self.driver = self.create_driver()
        self.configs = configs
        self.hours = hours
        self.fTypes = fTypes
        self.fInterval = fInterval
        self.dir = screenshotsDir
        self.switched_to_mm = False

        self.urls = {}


        # списки id и xpath элементов интерфейса ventusky, которые мы удаляем,
        # чтобы сделать скриншоты
        self.invis_id_elements = ["header", "p", "m", "i", "h", "k"]
        self.invis_xpath_elements = ["/html/body/menu", "/html/body/div[3]", "/html/body/div[4]", "/html/body/a[1]",
                                "/html/body/a[2]"]

    def set_dir(self, new_dir):
        self.dir = new_dir

    def create_driver(self):
        chrome_options = Options()
        # РАСКОМЕНТИРОВАТЬ СТРОКУ ДЛЯ РАБОТЫ В ФОНОВОМ РЕЖИМЕ
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-automation")
        chrome_options.add_argument("window-size=2000,1400")
        driver = webdriver.Chrome(path_to_driver, options=chrome_options)
        driver.maximize_window()
        return driver

    # генератор чисел +1
    @staticmethod
    def gen(n=1):
        while True:
            yield str(n)
            n += 1

    # проверяет, загрузилась ли анимация погоды
    def is_loaded(self):
        xx_span = self.driver.find_elements_by_class_name("xx")
        a = xx_span[0].get_attribute("style")
        try:
            self.driver.find_element(By.CSS_SELECTOR, css_selector_boarders)
        except NoSuchElementException:
            return False
        return a == ""

    # функция возвращает дату сегодня + delta дней в формате ГГГГ.мм.дд
    def get_tomorrow(self, delta):
        today = datetime.today() + timedelta(days=delta)
        return today.strftime('%Y%m%d')

    def turn_on_grid(self):
        self.driver.get("https://www.ventusky.com")
        while True:
            if self.is_loaded():
                break

        # входим в настройки
        settings_btn = self.driver.find_element(By.CSS_SELECTOR, css_selector_settings)
        settings_btn.click()
        # ставим галочку отображать значение в сетке, если не установлено
        check_box = self.driver.find_element(By.CSS_SELECTOR, css_selector_checkbox)
        if not check_box.is_selected():
            check_box.click()
        # закрываем настройки
        close_btn = self.driver.find_element(By.CSS_SELECTOR, css_selector_closebtn)
        close_btn.click()

    # добавить в список url накопление осадков или снега
    def create_url_by_type_and_time(self, f_type, days, name, coords, scale, sub_dir, width, height):
        delta = self.get_tomorrow(days)
        hour = '0600'

        url = f"https://www.ventusky.com/?p={coords};{scale}&l={f_type}&t={delta}/{hour}"
        screenshot_name = os.path.join(sub_dir, f"{name}.png")
        self.urls[url] = (screenshot_name, width, height)

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
    def create_url(self):
        for locationName, params in self.configs.items():
            coords, scale, width, height = params.values()

            sub_dir = os.path.join(self.dir, locationName)
            if not os.path.exists(sub_dir):
                os.mkdir(sub_dir)

            for fType in self.fTypes:
                num_gen = VentuskyParser.gen()  # создаем генератор чисел
                for delta in range(1, self.fInterval + 1):
                    for hour in self.hours.values():
                        date = self.get_tomorrow(delta)
                        url = f"https://www.ventusky.com/?p={coords};{scale}&l={fType}&t={date}/{hour}"
                        screenshot_name = os.path.join(sub_dir, f"{self.fTypes[fType]}{next(num_gen)}.png")

                        self.urls[url] = (screenshot_name, width, height)

            # накопление осадков за 24 часа
            self.create_url_by_type_and_time(RAIN_ACC, 1, "сумм24", coords, scale, sub_dir, width, height)
            # накопление  накопления осадков за 72 часа
            self.create_url_by_type_and_time(RAIN_ACC, 3, "сумм72", coords, scale, sub_dir, width, height)
            # накопление  накопления снега за 24 часа
            self.create_url_by_type_and_time(SNOW_ACC, 1, "снег24", coords, scale, sub_dir, width, height)
            # накопление  накопления снега за 72 часа
            self.create_url_by_type_and_time(SNOW_ACC, 3, "снег72", coords, scale, sub_dir, width, height)

    # делает скрин по указанному url и сохраняет под именем screenshotName
    def drive_url(self, url, screenshotName):
        print(screenshotName)
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

        # переключает на м/с, если порывы ветра
        if not self.switched_to_mm and "gust" in url:
            scale = self.driver.find_element(By.CSS_SELECTOR, "#h")
            scale.click()
            self.switched_to_mm = True
            sleep(5)

        # делаем элементы меню сделать невидимыми
        self.set_invisible_by_xpath()
        self.set_invisible_by_id()
        self.driver.get_screenshot_as_file(screenshotName)

    def launch_driver(self):
        self.create_url()
        self.turn_on_grid()
        for url, item in self.urls.items():
            screenshotName, width, height = item
            self.driver.set_window_size(width, height)
            self.drive_url(url, screenshotName)

        # try:
        #     self.driver.close()
        #     self.driver.quit()
        # except ConnectionRefusedError:
        #     pass

    def get_gismeteo(self):
        urls = self.create_dirs_and_urls()
        self.driver.set_window_size(2000, 1400)

        for pair in urls:
            saving_name = pair["saving_name"]
            self.driver.get(pair["url"])
            # promo = self.driver.find_element(By.CSS_SELECTOR, "body > section.section-overlay")
            # self.driver.execute_script("""var element = arguments[0];
            #                                                  element.parentNode.removeChild(element);""", promo)
            widget = self.driver.find_element(By.CSS_SELECTOR, "body > section > div.content-column.column1 > section:nth-child(2) > div > div > div")

            location = widget.location
            size = widget.size

            x1 = int(location['x'])
            y1 = int(location['y'])
            width = int(size['width'])
            height = int(size['height'])
            x2 = x1 + width
            y2 = y1 + height

            print(saving_name)
            self.driver.get_screenshot_as_file(saving_name)
            with Image.open(saving_name) as img:
                try:
                    box = (x1, y1, x2, y2)
                    part = img.crop(box)
                    # os.remove(saving_name)
                    part.save(saving_name)
                except Exception as e:
                    print(e)


    def create_dirs_and_urls(self):
        urls = []
        for FO, pairs in gismeteo_urls.items():
            _sub_dir = os.path.join(self.dir, FO)

            if not os.path.exists(_sub_dir):
                os.mkdir(_sub_dir)

            sub_dir = os.path.join(_sub_dir, 'Гисметео')
            if not os.path.exists(sub_dir):
                os.mkdir(sub_dir)

            for city, url in pairs.items():
                saving_name = os.path.join(sub_dir, f'{city}.png')
                urls.append({"url": url, "saving_name": saving_name})

        return urls
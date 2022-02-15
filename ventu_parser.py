import os.path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

css_selector_settings = "#menu-settings > a"
css_selector_checkbox = "#settings-colors > div.resp_table > div > label > div.resp_table_cell.cell2 > input[type=checkbox]"
css_selector_closebtn = "#aside_close_btn"



class VentuskyParser:
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
        self.invis_id_elements = ["header", "p", "m", "i", "h", "k"]
        self.invis_xpath_elements = ["/html/body/menu", "/html/body/div[3]", "/html/body/div[4]", "/html/body/a[1]",
                                "/html/body/a[2]"]

    def set_screenshot_dir(self, new_dir):
        self.dir = new_dir

    def create_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-automation")
        chrome_options.add_argument("window-size=2000,1400")
        driver = webdriver.Chrome("./chromedriver.exe", options=chrome_options)
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

            for fType in self.fTypes:
                num_gen = VentuskyParser.gen()  # создаем генератор чисел
                for delta in range(1, self.fInterval + 1):
                    for hour in self.hours.values():
                        date = self.get_tomorrow(delta)
                        url = f"https://www.ventusky.com/?p={coords};{scale}&l={fType}&t={date}/{hour}"
                        screenshot_name = f"{locationName}_{self.fTypes[fType]}_{next(num_gen)}.png"
                        self.urls[url] = (screenshot_name, width, height)

            delta_day_3 = self.get_tomorrow(3)
            fType = 'rain-ac'
            hour = '0600'

            url = f"https://www.ventusky.com/?p={coords};{scale}&l={fType}&t={delta_day_3}/{hour}"
            screenshot_name = f"{locationName}_накопление_осадков_72ч.png"
            self.urls[url] = (screenshot_name, width, height)

            fType ="new-snow-ac"

            url = f"https://www.ventusky.com/?p={coords};{scale}&l={fType}&t={delta_day_3}/{hour}"
            screenshot_name = f"{locationName}_накопление_снега_72ч.png"
            self.urls[url] = (screenshot_name, width, height)

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

        # делаем элементы меню сделать невидимыми
        self.set_invisible_by_xpath()
        self.set_invisible_by_id()

        saving_dir = os.path.join(self.dir, screenshotName)
        self.driver.get_screenshot_as_file(saving_dir)

    def launch_driver(self):

        self.create_url()
        self.turn_on_grid()
        for url, item in self.urls.items():
            screenshotName, width, height = item
            self.driver.set_window_size(width, height)
            self.drive_url(url, screenshotName)

        try:
            self.driver.close()
            self.driver.quit()
        except ConnectionRefusedError:
            pass


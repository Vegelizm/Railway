import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Настройки headless-браузера
chrome_options = Options()
chrome_options.add_argument("--headless")  # Без графики
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Запуск браузера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Открываем Авито
driver.get("https://www.avito.ru/")

print("✅ Бот запущен!")

# Бесконечно обновляем страницу
def stay_online(interval=300):
    try:
        while True:
            time.sleep(interval)  # Ждём X секунд
            driver.refresh()  # Обновляем страницу
            print("🔄 Страница обновлена")
    except KeyboardInterrupt:
        driver.quit()

stay_online()

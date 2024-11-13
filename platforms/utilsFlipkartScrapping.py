# utilsAmazonScrapping.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
import datetime
from django.contrib.contenttypes.models import ContentType
from platforms.models import flipkartProduct, review

def fetch_flipkart_reviews(sessionId, username):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except WebDriverException as e:
        return f'Error initializing WebDriver: {e}'

    try:
        fsn_list = flipkartProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Fsn', flat=True).distinct()
        for fsn in fsn_list:
            try:
                url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page=1"
                browser.get(url)
                time.sleep(2)
                soup = BeautifulSoup(browser.page_source, 'html.parser')
                total_reviews = soup.find_all('div', {'class': 'row j-aW8Z'})[1].text
                nu = total_reviews.replace(',', '')
                nu = [int(word) for word in nu.split() if word.isdigit()]
                nu = int(nu[0])
                pages = min((nu // 10) + 1, 10)
            except Exception as e:
                continue

            for page in range(0, pages + 1):
                try:
                    page_url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page={page}"
                    browser.get(page_url)
                    time.sleep(2)
                    soup = BeautifulSoup(browser.page_source, 'html.parser')
                    reviews_containers = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG'})

                    for container in reviews_containers:
                        review_content = container.find('div', {'class': 'ZmyHeo'}).text.strip() if container.find('div', {'class': 'ZmyHeo'}) else 'No content provided'
                        rating = 0
                        if container.find('div', {'class': 'XQDdHH Ga3i8K'}):
                            rating = int(container.find('div', {'class': 'XQDdHH Ga3i8K'}).text.strip())
                        elif container.find('div', {'class': '_3LWZlK _32lA32 _1BLPMq'}):
                            rating = int(container.find('div', {'class': '_3LWZlK _32lA32 _1BLPMq'}).text.strip())
                        elif container.find('div', {'class': '_3LWZlK _1rdVr6 _1BLPMq'}):
                            rating = int(container.find('div', {'class': '_3LWZlK _1rdVr6 _1BLPMq'}).text.strip())

                        try:
                            review_date_str = container.find('p', {'class': '_2NsDsF'}).text.strip()
                            review_date = datetime.datetime.strptime(review_date_str, "%d %b, %Y").date()
                        except:
                            review_date = datetime.date.min

                        flipkart_product_instance = flipkartProduct.objects.filter(Fsn=fsn, Status='pending', user=username, sessionId=sessionId).first()
                        if flipkart_product_instance:
                            content_type = ContentType.objects.get_for_model(flipkartProduct)
                            review_instance = review.objects.create(
                                content_type=content_type,
                                object_id=flipkart_product_instance.id,
                                reviewContent=review_content,
                                rating=rating,
                                created_at=review_date or datetime.date.min,
                                user=username,
                                sessionId=sessionId,
                            )

                except Exception as e:
                    break

            flipkartProduct.objects.filter(Fsn=fsn, user=username, sessionId=sessionId).update(Status='completed')

    except Exception as e:
        return f'An error occurred during processing: {e}'
    finally:
        browser.quit()

    return 'Successfully fetched and saved Flipkart reviews'

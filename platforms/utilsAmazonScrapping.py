
from django.http import JsonResponse, HttpResponse,response
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import time
import datetime
from django.contrib.contenttypes.models import ContentType
from platforms.models import amazonProduct, review

def fetch_amazon_reviews(sessionId, username):
    # Set up Chrome options
    chrome_options = Options()
    try:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except WebDriverException as e:
        return f'Error initializing WebDriver: {e}'

    try:
        asin_list = amazonProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Asin', flat=True).distinct()
        cnt=0
        size=0
        for Asin in asin_list:
            size=size+1
            url = f"https://www.amazon.com/product-reviews/{Asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
            browser.get(url)

            try:
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="filter-info-section"]/div'))
                )
                total_reviews_text = browser.find_element(By.XPATH, '//*[@id="filter-info-section"]/div').text
                match = re.search(r'(\d{1,3}(?:,\d{3})*) with reviews', total_reviews_text)
                if match:
                    total_reviews_text = match.group(1)
                    total_reviews_number_str = re.sub(r'[^\d]', '', total_reviews_text)
                    total_reviews = int(total_reviews_number_str)
                    num_pages = min((total_reviews // 10) + 1, 10)
            except TimeoutException:
                cnt=cnt+1
                continue
            except NoSuchElementException:
                cnt=cnt+1
                continue
            except Exception as e:
                cnt=cnt+1
                continue
            
            for page in range(1, num_pages + 1):
                try:
                    page_url = f"https://www.amazon.com/product-reviews/{Asin}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber={page}"
                    browser.get(page_url)
                    time.sleep(2)

                    soup = BeautifulSoup(browser.page_source, "html.parser")
                    reviews_containers = soup.find_all("div", {"class": "a-section celwidget"})

                    for container in reviews_containers:
                        review_content = container.find("span", {"data-hook": "review-body"}).get_text().strip() if container.find("span", {"data-hook": "review-body"}) else 'No content provided'
                        review_date_str = container.find("span", {"data-hook": "review-date"}).get_text().strip()
                        date_match = re.search(r'\d{1,2} \w+ \d{4}', review_date_str)
                        review_date = datetime.datetime.strptime(date_match.group(0), "%d %B %Y").date() if date_match else None
                        rating_text = container.find("i", {"data-hook": "review-star-rating"}).get_text() if container.find("i", {"data-hook": "review-star-rating"}) else '0'
                        rating = int(rating_text.split('.')[0])

                        amazon_product_instance = amazonProduct.objects.filter(Asin=Asin, Status='pending', user=username, sessionId=sessionId).first()
                        if amazon_product_instance:
                            content_type = ContentType.objects.get_for_model(amazonProduct)
                            review_instance = review.objects.create(
                                content_type=content_type,
                                object_id=amazon_product_instance.id,
                                reviewContent=review_content,
                                rating=rating,
                                user=username,
                                sessionId=sessionId,
                                created_at=review_date or datetime.date.min,
                            )

                except Exception as e:
                    break
            if size!=cnt:
              amazonProduct.objects.filter(Asin=Asin, user=username, sessionId=sessionId).update(Status='completed')

    except Exception as e:
        return f'An error occurred during processing: {e}'
    finally:
        browser.quit()
    if size!=cnt:
      return 'Successfully fetched and saved Amazon reviews'
    else :
        return 'no asin is being proccesed'
      

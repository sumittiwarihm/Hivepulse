from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import re
import time
import datetime
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from platforms.models import amazonProduct, review

class Command(BaseCommand):
    help = 'Fetch Amazon reviews and save them to the database'
    def add_arguments(self, parser):
        parser.add_argument('--sessionId', type=str, help='The session ID')
        parser.add_argument('--username', type=str, help='The username')

    def handle(self, *args, **options):
    # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use the new headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument("--no-sandbox")  # Required for running as root on some systems
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--window-size=1920,1080")  # Set a fixed window size
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")  # User agent spoofing
        
        sessionId = options['sessionId']
        username = options['username']

        try:
            # Set up the WebDriver with the specified options
            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        except WebDriverException as e:
            self.stdout.write(self.style.ERROR(f'Error initializing WebDriver: {e}'))
            return

        try:
            # Fetch ASINs with 'pending' status
            asin_list = amazonProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Asin', flat=True).distinct()

            for Asin in asin_list:
                self.stdout.write(self.style.SUCCESS(f'Processing ASIN: {Asin}'))
                url = f"https://www.amazon.in/product-reviews/{Asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
                browser.get(url)

                try:
                    # Explicit wait for the element to be present
                    WebDriverWait(browser, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="filter-info-section"]/div'))
                    )

                    total_reviews_text = browser.find_element(By.XPATH, '//*[@id="filter-info-section"]/div').text
                    match = re.search(r'(\d{1,3}(?:,\d{3})*) with reviews', total_reviews_text)
                    if match:
                        total_reviews_text = match.group(1)
                        total_reviews_number_str = re.sub(r'[^\d]', '', total_reviews_text)
                        total_reviews = int(total_reviews_number_str)
                        num_pages = min((total_reviews // 10) + 1, 10)  # Adjust the number of pages to scrape
                except TimeoutException:
                    self.stdout.write(self.style.ERROR(f'Timed out waiting for reviews section for ASIN {Asin}'))
                    continue
                except NoSuchElementException:
                    self.stdout.write(self.style.ERROR(f'No reviews section found for ASIN {Asin}'))
                    continue
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error fetching reviews for ASIN {Asin}: {e}'))
                    continue

                for page in range(1, num_pages + 1):
                    try:
                        page_url = f"https://www.amazon.in/product-reviews/{Asin}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber={page}"
                        browser.get(page_url)
                        time.sleep(2)  # Additional wait to ensure the page has fully loaded

                        soup = BeautifulSoup(browser.page_source, "html.parser")
                        reviews_containers = soup.find_all("div", {"class": "a-section celwidget"})

                        for container in reviews_containers:
                            try:
                                review_content = container.find("span", {"data-hook": "review-body"}).get_text().strip()
                            except:
                                review_content = 'No content provided'  # Default if not found

                            try:
                                review_date_str = container.find("span", {"data-hook": "review-date"}).get_text().strip()
                                date_match = re.search(r'\d{1,2} \w+ \d{4}', review_date_str)
                                if date_match:
                                    date_str = date_match.group(0)
                                    date_obj = datetime.datetime.strptime(date_str, "%d %B %Y").date()
                                    review_date = date_obj
                                else:
                                    review_date = None
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Date parsing error for review: {e}"))
                                review_date = None  # Default to None if not found

                            try:
                                rating_text = container.find("i", {"data-hook": "review-star-rating"}).get_text()
                                rating = int(rating_text.split('.')[0])  # Extract integer rating from string
                            except:
                                rating = 0  # Default if not found

                            # Save each review as a separate entry in the database
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
                                    created_at=review_date or datetime.date.min,  # Use the earliest representable date as a fallback
                                )

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing page {page} for ASIN {Asin}: {e}'))
                        break  # Exit the loop if an error occurs

                # Update product status
                amazonProduct.objects.filter(Asin=Asin, user=username, sessionId=sessionId).update(Status='completed')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during processing: {e}'))

        finally:
            # Ensure the browser is closed even if an error occurs
            browser.quit()

        self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Amazon reviews'))



# from django.db.models import Q
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
# import re
# import time
# import datetime
# from bs4 import BeautifulSoup
# from django.core.management.base import BaseCommand
# from django.contrib.contenttypes.models import ContentType
# from platforms.models import amazonProduct, review
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from django.db import transaction

# class Command(BaseCommand):
#     help = 'Fetch Amazon reviews and save them to the database'

#     def add_arguments(self, parser):
#         parser.add_argument('--sessionId', type=str, help='The session ID')
#         parser.add_argument('--username', type=str, help='The username')

#     def setup_browser(self):
#         chrome_options = Options()
#         # chrome_options.add_argument("--headless=new")  # Use the new headless mode
#         chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
#         chrome_options.add_argument("--no-sandbox")  # Required for running as root on some systems
#         chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
#         chrome_options.add_argument("--window-size=1920,1080")  # Set a fixed window size
#         chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")  # User agent spoofing
#         chrome_options.add_argument("accept-language=en-US,en;q=0.9")
#         chrome_options.add_argument("accept-encoding=gzip, deflate, br")
#         chrome_options.add_argument("referer=https://www.amazon.in/")

#         try:
#             return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
#         except WebDriverException as e:
#             self.stdout.write(self.style.ERROR(f'Error initializing WebDriver: {e}'))
#             return None

#     def fetch_reviews(self, Asin):
#         with transaction.atomic():
#             amazon_product_instance = amazonProduct.objects.select_for_update(nowait=True).filter(Asin=Asin,Status__in=['pending', 'in-progress']).first()
#             if not amazon_product_instance:
#                 return  # Exit if the ASIN is already being processed or completed
#             amazon_product_instance.Status = 'in-progress'
#             amazon_product_instance.save()

#         browser = self.setup_browser()
#         if not browser:
#             return

#         self.stdout.write(self.style.SUCCESS(f'Processing ASIN: {Asin}'))
#         url = f"https://www.amazon.in/product-reviews/{Asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
#         browser.get(url)

#         try:
#             WebDriverWait(browser, 20).until(
#                 EC.presence_of_element_located((By.XPATH, '//*[@id="filter-info-section"]/div'))
#             )

#             total_reviews_text = browser.find_element(By.XPATH, '//*[@id="filter-info-section"]/div').text
#             match = re.search(r'(\d{1,3}(?:,\d{3})*) with reviews', total_reviews_text)
#             if match:
#                 total_reviews_text = match.group(1)
#                 total_reviews_number_str = re.sub(r'[^\d]', '', total_reviews_text)
#                 total_reviews = int(total_reviews_number_str)
#                 num_pages = min((total_reviews // 10) + 1, 10)  # Adjust the number of pages to scrape
#             else:
#                 num_pages = 1  # Default to one page if no review count found
#         except TimeoutException:
#             self.stdout.write(self.style.ERROR(f'Timed out waiting for reviews section for ASIN {Asin}'))
#             browser.quit()
#             return
#         except NoSuchElementException:
#             self.stdout.write(self.style.ERROR(f'No reviews section found for ASIN {Asin}'))
#             browser.quit()
#             return
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'Error fetching reviews for ASIN {Asin}: {e}'))
#             browser.quit()
#             return

#         for page in range(1, num_pages + 1):
#             page_url = f"https://www.amazon.in/product-reviews/{Asin}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber={page}"
#             browser.get(page_url)
#             time.sleep(6)  # Additional wait to ensure the page has fully loaded

#             soup = BeautifulSoup(browser.page_source, "html.parser")
#             reviews_containers = soup.find_all("div", {"class": "a-section celwidget"})

#             for container in reviews_containers:
#                 try:
#                     review_content = container.find("span", {"data-hook": "review-body"}).get_text().strip()
#                 except:
#                     review_content = 'No content provided'

#                 try:
#                     review_date_str = container.find("span", {"data-hook": "review-date"}).get_text().strip()
#                     date_match = re.search(r'\d{1,2} \w+ \d{4}', review_date_str)
#                     if date_match:
#                         date_str = date_match.group(0)
#                         date_obj = datetime.datetime.strptime(date_str, "%d %B %Y").date()
#                         review_date = date_obj
#                     else:
#                         review_date = None
#                 except Exception as e:
#                     self.stdout.write(self.style.ERROR(f"Date parsing error for review: {e}"))
#                     review_date = None

#                 try:
#                     rating_text = container.find("i", {"data-hook": "review-star-rating"}).get_text()
#                     rating = int(rating_text.split('.')[0])
#                 except:
#                     rating = 0

#                 review.objects.create(
#                     content_type=ContentType.objects.get_for_model(amazonProduct),
#                     object_id=amazon_product_instance.id,
#                     reviewContent=review_content,
#                     rating=rating,
#                     created_at=review_date or datetime.date.min,
#                 )

#         amazon_product_instance.Status = 'completed'
#         amazon_product_instance.save()

#         browser.quit()

#     def handle(self, *args, **options):
#         sessionId = options['sessionId']
#         username = options['username']
#         asin_list = amazonProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Asin', flat=True).distinct()

#         max_threads = 2 # Adjust based on your system capabilities
#         with ThreadPoolExecutor(max_threads) as executor:
#             futures = {executor.submit(self.fetch_reviews, Asin): Asin for Asin in asin_list}
#             for future in as_completed(futures):
#                 Asin = futures[future]
#                 try:
#                     future.result()  # This will re-raise any exceptions caught during execution
#                 except Exception as e:
#                     self.stdout.write(self.style.ERROR(f'Error processing ASIN {Asin}: {e}'))

#         self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Amazon reviews'))

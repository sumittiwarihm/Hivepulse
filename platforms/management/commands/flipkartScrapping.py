from webdriver_manager.chrome import ChromeDriverManager
import re
import time
import datetime
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from django.contrib.contenttypes.models import ContentType
from platforms.models import flipkartProduct, review

class Command(BaseCommand):
    help = 'Fetch Flipkart reviews and save them to the database'

    def add_arguments(self, parser):
        parser.add_argument('--sessionId', type=str, help='The session ID')
        parser.add_argument('--username', type=str, help='The username')

    def handle(self, *args, **options):
        # Set up Chrome options
        chrome_options = Options()
        #chrome_options.add_argument("--headless=new")  # Use headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument("--no-sandbox")  # Required for running as root on some systems
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--window-size=1920,1080")  # Set a fixed window size
        
        sessionId = options['sessionId']
        username = options['username']

        try:
            # Set up the WebDriver with the specified options
            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        except WebDriverException as e:
            self.stdout.write(self.style.ERROR(f'Error initializing WebDriver: {e}'))
            return

        try:
            # Fetch FSNs with 'pending' status
            fsn_list = flipkartProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Fsn', flat=True).distinct()

            for fsn in fsn_list:
                self.stdout.write(self.style.SUCCESS(f'Processing FSN: {fsn}'))
                
                try:
                    # Fetch total number of reviews
                    url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page=1"
                    browser.get(url)
                    time.sleep(2)
                    
                    soup = BeautifulSoup(browser.page_source, 'html.parser')
                    reviews_divs = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG MDcJkH'}) #row P48fSg gZLG+o
                    if len(reviews_divs) > 1:
                        total_reviews_text = reviews_divs[1].text
                        nu = [int(word) for word in re.sub(r'[^\d]', '', total_reviews_text).split() if word.isdigit()]
                        total_reviews = int(nu[0]) if nu else 0
                        num_pages = min((total_reviews // 10) + 1, 10)  # Set a limit to scrape up to 10 pages
                    else:
                        self.stdout.write(self.style.ERROR(f'No reviews section found for FSN {fsn}'))
                        continue

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error fetching reviews for FSN {fsn}: {e}'))
                    continue

                # Loop through review pages
                for page in range(1, num_pages + 1):
                    try:
                        page_url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page={page}"
                        browser.get(page_url)
                        time.sleep(2)

                        soup = BeautifulSoup(browser.page_source, 'html.parser')
                        reviews_containers = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG MDcJkH'})

                        for container in reviews_containers:
                            try:
                                review_content = container.find('div', {'class': '_11pzQk'}).text.strip()
                            except:
                                review_content = 'No content provided'  # Default if not found

                            try:
                                rating_text = container.find('div', {'class': 'XQDdHH Ga3i8K _9lBNRY'}).text.strip()
                                rating = int(rating_text.split('.')[0])  # Extract integer rating from string
                            except:
                                rating = 0  # Default if not found

                            try:
                                review_date_str = container.find('p', {'class': '_2NsDsF'}).text.strip()
                                review_date = datetime.datetime.strptime(review_date_str, "%d %b, %Y").date()
                            except:
                                review_date = datetime.date.min  # Default to the earliest representable date

                            # Save each review as a separate entry in the database
                            flipkart_product_instance = flipkartProduct.objects.filter(Fsn=fsn, Status='pending', user=username, sessionId=sessionId).first()
                            if flipkart_product_instance:
                                content_type = ContentType.objects.get_for_model(flipkartProduct)
                                review_instance = review.objects.create(
                                    content_type=content_type,
                                    object_id=flipkart_product_instance.id,
                                    reviewContent=review_content,
                                    rating=rating,
                                    created_at=review_date,
                                    user=username,
                                    sessionId=sessionId,
                                )

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing page {page} for FSN {fsn}: {e}'))
                        break  # Exit the loop if an error occurs

                # Update product status
                flipkartProduct.objects.filter(Fsn=fsn, user=username, sessionId=sessionId).update(Status='completed')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during processing: {e}'))

        finally:
            # Ensure the browser is closed even if an error occurs
            browser.quit()

        self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Flipkart reviews'))


















# import re
# import time
# import datetime
# import numpy as np
# from django.core.management.base import BaseCommand
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# from django.contrib.contenttypes.models import ContentType
# from platforms.models import flipkartProduct, review


# flag=True
# class Command(BaseCommand):
#     help = 'Fetch Flipkart reviews and save them to the database'
#     def add_arguments(self, parser):
#         parser.add_argument('--sessionId', type=str, help='The session ID')
#         parser.add_argument('--username', type=str, help='The username')
    
    
#     def handle(self, *args, **options):
#         # Set up Chrome options
#         chrome_options = Options()
#         #chrome_options.add_argument("--headless")  # Run in headless mode
#         chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
#         chrome_options.add_argument("--no-sandbox")  # Required for running as root on some systems
#         chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
#         chrome_options.add_argument("--window-size=1920,1080")  # Set a fixed window size
#         # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36") 
#         # chrome_options.set_capability('goog:loggingPrefs', {'browser': 'OFF'})
#         sessionId = options['sessionId']
#         username = options['username']
#         # Set up the WebDriver with the specified options
#         browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#         # Fetch FSNs with 'pending' status
#         fsn_list = flipkartProduct.objects.filter(Status='pending', sessionId=sessionId, user=username).values_list('Fsn', flat=True).distinct()

#         for fsn in fsn_list:
#             self.stdout.write(self.style.SUCCESS(f'Processing FSN: {fsn}'))
#             soup = None  # Initialize soup to ensure it exists
#             try:
#                 reviews_divs = soup.find_all('div', {'class': 'row j-aW8Z'})
#                 if len(reviews_divs) > 1:
#                     total_reviews_text = reviews_divs[1].text
#                     nu = total_reviews_text.replace(',', '')
#                     nu = [int(word) for word in nu.split() if word.isdigit()]
#                     total_reviews_number = int(nu[0])
#                     num_pages = 1  # int(np.ceil(total_reviews_number / 10))
#                 else:
#                     self.stdout.write(self.style.ERROR(f'Could not find the expected total reviews div for FSN {fsn}'))
#                     continue
#             except Exception as e:
                
#                 self.stdout.write(self.style.ERROR(f'Error fetching reviews for FSN {fsn}: {e}'))
#                 continue
#             if soup:  # Proceed only if soup is successfully created
#                 for page in range(1, num_pages + 1):
#                     page_url = f"https://www.flipkart.com/realme-c55-rainforest-128-gb/product-reviews/itm054283d14c56e?pid={fsn}&lid=LSTMOBGNBYJPF2DEADSUWHGW7&marketplace=FLIPKART&page={page}"
#                     browser.get(page_url)
#                     time.sleep(2)

#                     soup = BeautifulSoup(browser.page_source, 'html.parser')
#                     reviews_containers = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG'})

#                     for container in reviews_containers:
#                         try:
#                             review_content = container.find('div', {'class': 'ZmyHeo'}).text.strip()
#                         except:
#                             review_content = 'No content provided'  # Default if not found

#                         try:
#                             rating_text = container.find('div', {'class': 'XQDdHH Ga3i8K'}).text.strip()
#                             rating = int(rating_text.split('.')[0])  # Extract integer rating from string
#                         except:
#                             rating = 0  # Default if not found

#                         try:
#                             review_date_str = container.find('p', {'class': '_2NsDsF'}).text.strip()
#                             review_date = datetime.datetime.strptime(review_date_str, "%d %b, %Y").date()
#                         except:
#                             review_date = datetime.date.min  # Default to the earliest representable date

#                         # Save each review as a separate entry in the database
#                         flipkart_product_instance = flipkartProduct.objects.filter(Fsn=fsn, Status='pending',user=username, sessionId=sessionId).first()
#                         if flipkart_product_instance:
#                             content_type = ContentType.objects.get_for_model(flipkartProduct)
#                             review_instance = review.objects.create(
#                                 content_type=content_type,
#                                 object_id=flipkart_product_instance.id,
#                                 reviewContent=review_content,
#                                 rating=rating,
#                                 created_at=review_date,
#                                 user=username,
#                                 sessionId=sessionId,
#                             )

#             # Update product status
#             flipkartProduct.objects.filter(Fsn=fsn,user=username, sessionId=sessionId).update(Status='completed')

#         browser.quit()
#         self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Flipkart reviews'))

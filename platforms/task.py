from Hivepulse.celery import app
import time
@app.task
def factorial_task(n):
    time.sleep(20)
    return "hello"

@app.task
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
# flipkart script complete .
from selenium import webdriver
import logging
logger = logging.getLogger(__name__)
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
@app.task
def fetch_flipkart_reviews(sessionId,username):
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
        logger.info(f"Processing fsn list: {fsn_list}")
        # logger.error(f"Error initializing WebDriver: {e}")
        for fsn in fsn_list:
            try:
                # print("helooo")
                url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page=1"
                browser.get(url)
                time.sleep(2)
                soup = BeautifulSoup(browser.page_source, 'html.parser')
                total_reviews = soup.find_all('div', {'class': 'row j-aW8Z'})[1].text
                nu = total_reviews.replace(',', '')
                nu = [int(word) for word in nu.split() if word.isdigit()]
                nu = int(nu[0])
                pages = 10
            except Exception as e:
                continue
            for page in range(0, pages+1):
                print(page)
                try:
                    print("hello")
                    page_url = f"https://www.flipkart.com/poco-m6-pro-5g-power-black-128-gb/product-reviews/itm5b122ff13027f?pid={fsn}&lid=LSTMOBGRNZ3FX5XNR2TILGJYM&marketplace=FLIPKART&page={page}"
                    browser.get(page_url)
                    time.sleep(3)
                    soup = BeautifulSoup(browser.page_source, 'html.parser')
                    reviews_containers = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG'})
                    for container in reviews_containers:
                        review_content = container.find('div', {'class': 'ZmyHeo'}).text.strip() if container.find('div', {'class': 'ZmyHeo'}) else 'No content provided'
                        review_content = re.sub(r'READ MORE$', '', review_content).strip()
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
            # flipkartProduct.objects.filter(Fsn=fsn, user=username, sessionId=sessionId).update(Status='completed')
            try:
                perform_flipkart_sentiment_analysis(sessionId, username)
                print("Script Ran For Seniment Analysis")
                flipkartProduct.objects.filter(Fsn=fsn, user=username, sessionId=sessionId).update(Status='completed')
            except Exception as e:
                return f'An error occurred during processing of snetiment analysis: {e}'
    except Exception as e:
        return f'An error occurred during processing of scrapping  script: {e}'
    finally:
        browser.quit()
    return 'Successfully fetched the review and got the sentiment and saved for Flipkart reviews'

# utilsAmazonScrapping.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from django.contrib.contenttypes.models import ContentType
from platforms.models import review, sentimentResult, flipkartProduct

def perform_flipkart_sentiment_analysis(sessionId, username):
    # Load the RoBERTa model and tokenizer
    MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    def polarity_scores_roberta(text):
        encoded_text = tokenizer(
            text, 
            return_tensors='pt', 
            truncation=True,  
            max_length=512    
        )
        output = model(**encoded_text)
        scores = output.logits[0].detach().cpu().numpy()
        scores = softmax(scores)
        scores_dict = {
            'negativeScore': scores[0],
            'neutralScore': scores[1],
            'positiveScore': scores[2]
        }
        return scores_dict

    def classify_sentiment(pos_score, neg_score, neu_score, threshold=0.5):
        if pos_score > neg_score and pos_score > neu_score and pos_score >= threshold:
            return 'Positive'
        elif neg_score > pos_score and neg_score > neu_score and neg_score >= threshold:
            return 'Negative'
        else:
            return 'Neutral'

    def analyze_and_store_sentiment():
        flipkart_product_content_type = ContentType.objects.get_for_model(flipkartProduct)
        flipkart_product_reviews = review.objects.filter(content_type=flipkart_product_content_type)
        review_toprocess = flipkart_product_reviews.filter(user=username, sessionId=sessionId)

        for rev in review_toprocess:
            if sentimentResult.objects.filter(review_id=rev.id).exists():
                print(f'Sentiment already exists for review ID {rev.id}, skipping...')
                continue

            text = rev.reviewContent
            roberta_result = polarity_scores_roberta(text)
            
            estimated_result = classify_sentiment(
                roberta_result['positiveScore'], 
                roberta_result['negativeScore'], 
                roberta_result['neutralScore']
            )
            
            sentiment = sentimentResult(
                review_id=rev.id,
                positiveScore=roberta_result['positiveScore'],
                neutralScore=roberta_result['neutralScore'],
                negativeScore=roberta_result['negativeScore'],
                estimatedResult=estimated_result,
                user=username,
                sessionId=sessionId,
            )
            sentiment.save()
            print(f'Sentiment saved for review ID {rev.id}')

    analyze_and_store_sentiment()
    return "Flipkart sentiment analysis completed successfully."



# plystore script complete
import time
import datetime
from google_play_scraper import reviews, Sort
from django.contrib.contenttypes.models import ContentType
from platforms.models import playstoreProduct, review
@app.task
def fetch_playstore_reviews(sessionId, username):
    appid_list = playstoreProduct.objects.filter(Status='pending', sessionId=sessionId).values_list('AppId', flat=True).distinct()
    
    for AppId in appid_list:
        print(f'Processing AppId: {AppId}')
        
        try:
            continuation_token = None
            all_reviews = []
            fetched_reviews = 0

            while fetched_reviews < 1500:
                reviews_data, continuation_token = reviews(
                    AppId,
                    lang='en',
                    country='in',
                    sort=Sort.NEWEST,
                    count=min(1500, 1500 - fetched_reviews),
                    continuation_token=continuation_token
                )
                
                if len(reviews_data) == 0:
                    print(f'No reviews fetched for {AppId}, breaking the loop.')
                    break

                all_reviews.extend(reviews_data)
                fetched_reviews += len(reviews_data)

                print(f'Fetched {len(reviews_data)} reviews for {AppId}...')

                if not continuation_token or fetched_reviews >= 1500:
                    break

            print(f'Total reviews fetched for {AppId}: {len(all_reviews)}')

            for review_data in all_reviews:
                review_content = review_data.get('content', 'No content provided')
                review_date = review_data.get('at', datetime.date.min)
                rating = review_data.get('score', 0)
                
                playstore_product_instance = playstoreProduct.objects.filter(AppId=AppId, Status='pending', sessionId=sessionId, user=username).first()
                if playstore_product_instance:
                    content_type = ContentType.objects.get_for_model(playstoreProduct)
                    try:
                        review_instance = review.objects.create(
                            content_type=content_type,
                            object_id=playstore_product_instance.id,
                            reviewContent=review_content,
                            rating=rating,
                            created_at=review_date,
                            user=username,
                            sessionId=sessionId,
                        )
                    except Exception as save_error:
                        print(f"Error saving review for AppId {AppId}: {save_error}")

            # playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
            # print(f'Status updated for {AppId}')
            try:
               perform_playstore_sentiment_analysis(sessionId,username)
               playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
               print(f'Status updated for {AppId}')
            except:
               return 'error came during sneitment analysis of playstore'
        except Exception as e:
            print(f'Error fetching reviews for AppId {AppId}: {e}')

    return 'Successfully fetched and saved Google Play Store reviews'



from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from django.contrib.contenttypes.models import ContentType
from platforms.models import review, sentimentResult, playstoreProduct

def perform_playstore_sentiment_analysis(sessionId, username):
    # Load the RoBERTa model and tokenizer
    MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    def polarity_scores_roberta(text):
        encoded_text = tokenizer(
            text, 
            return_tensors='pt', 
            truncation=True,  
            max_length=512    
        )
        output = model(**encoded_text)
        scores = output.logits[0].detach().cpu().numpy()
        scores = softmax(scores)
        scores_dict = {
            'negativeScore': scores[0],
            'neutralScore': scores[1],
            'positiveScore': scores[2]
        }
        return scores_dict

    def classify_sentiment(pos_score, neg_score, neu_score, threshold=0.5):
        if pos_score > neg_score and pos_score > neu_score and pos_score >= threshold:
            return 'Positive'
        elif neg_score > pos_score and neg_score > neu_score and neg_score >= threshold:
            return 'Negative'
        else:
            return 'Neutral'

    def analyze_and_store_sentiment():
        playstore_product_content_type = ContentType.objects.get_for_model(playstoreProduct)
        playstore_product_reviews = review.objects.filter(content_type=playstore_product_content_type)
        review_toprocess = playstore_product_reviews.filter(user=username, sessionId=sessionId)

        for rev in review_toprocess:
            if sentimentResult.objects.filter(review_id=rev.id).exists():
                print(f'Sentiment already exists for review ID {rev.id}, skipping...')
                continue

            text = rev.reviewContent
            roberta_result = polarity_scores_roberta(text)
            
            estimated_result = classify_sentiment(
                roberta_result['positiveScore'], 
                roberta_result['negativeScore'], 
                roberta_result['neutralScore']
            )
            
            sentiment = sentimentResult(
                review_id=rev.id,
                positiveScore=roberta_result['positiveScore'],
                neutralScore=roberta_result['neutralScore'],
                negativeScore=roberta_result['negativeScore'],
                estimatedResult=estimated_result,
                user=username,
                sessionId=sessionId,
            )
            sentiment.save()
            print(f'Sentiment saved for review ID {rev.id}')

    analyze_and_store_sentiment()
    return "Playstore sentiment analysis completed successfully."



# amazon script 

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

@app.task
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
              perform_amazon_sentiment_analysis(sessionId, username)
              amazonProduct.objects.filter(Asin=Asin, user=username, sessionId=sessionId).update(Status='completed')
    except Exception as e:
        return f'An error occurred during processing: {e}'
    finally:
        browser.quit()
    if size!=cnt:
      return 'Successfully fetched and saved Amazon reviews'
    else :
        return 'no asin is being proccesed'
    

    # utilsAmazonScrapping.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from django.contrib.contenttypes.models import ContentType
from platforms.models import review, sentimentResult, amazonProduct
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction, IntegrityError, reset_queries

def perform_amazon_sentiment_analysis(sessionId, username):
    # Load the RoBERTa model and tokenizer
    MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    def polarity_scores_roberta(text):
        encoded_text = tokenizer(
            text, 
            return_tensors='pt', 
            truncation=True,  
            max_length=512    
        )
        output = model(**encoded_text)
        scores = output.logits[0].detach().cpu().numpy()
        scores = softmax(scores)
        scores_dict = {
            'negativeScore': scores[0],
            'neutralScore': scores[1],
            'positiveScore': scores[2]
        }
        return scores_dict

    def classify_sentiment(pos_score, neg_score, neu_score, threshold=0.5):
        if pos_score > neg_score and pos_score > neu_score and pos_score >= threshold:
            return 'Positive'
        elif neg_score > pos_score and neg_score > neu_score and neg_score >= threshold:
            return 'Negative'
        else:
            return 'Neutral'

    def process_review(rev):
        try:
            with transaction.atomic():
                review_locked = review.objects.select_for_update().get(id=rev.id)
                if sentimentResult.objects.filter(review_id=review_locked.id).exists():
                    print(f'Sentiment already exists for review ID {review_locked.id}, skipping...')
                    return

                text = review_locked.reviewContent
                roberta_result = polarity_scores_roberta(text)
                
                estimated_result = classify_sentiment(
                    roberta_result['positiveScore'], 
                    roberta_result['negativeScore'], 
                    roberta_result['neutralScore']
                )
                
                sentiment = sentimentResult(
                    review_id=review_locked.id,
                    positiveScore=roberta_result['positiveScore'],
                    neutralScore=roberta_result['neutralScore'],
                    negativeScore=roberta_result['negativeScore'],
                    estimatedResult=estimated_result,
                    user=username,
                    sessionId=sessionId,
                )
                sentiment.save()
                print(f'Sentiment saved for review ID {review_locked.id}')

        except IntegrityError:
            print(f"Sentiment result for review ID {rev.id} already exists. Skipping...")
        except Exception as e:
            print(f"Exception occurred while processing review ID {rev.id}: {e}")
        finally:
            reset_queries()

    def analyze_and_store_sentiment():
        amazon_product_content_type = ContentType.objects.get_for_model(amazonProduct)
        amazon_product_reviews = review.objects.filter(content_type=amazon_product_content_type)
        review_toprocess = amazon_product_reviews.filter(user=username, sessionId=sessionId)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_review = {executor.submit(process_review, rev): rev for rev in review_toprocess}
            
            for future in as_completed(future_to_review):
                try:
                    future.result()
                except Exception as e:
                    print(f"Exception occurred while processing a review: {e}")

    analyze_and_store_sentiment()

      









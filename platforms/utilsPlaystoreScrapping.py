# utilsAmazonScrapping.py

import time
import datetime
from google_play_scraper import reviews, Sort
from django.contrib.contenttypes.models import ContentType
from platforms.models import playstoreProduct, review

def fetch_playstore_reviews(sessionId, username):
    appid_list = playstoreProduct.objects.filter(Status='pending', sessionId=sessionId).values_list('AppId', flat=True).distinct()
    
    for AppId in appid_list:
        print(f'Processing AppId: {AppId}')
        
        try:
            continuation_token = None
            all_reviews = []
            fetched_reviews = 0

            while fetched_reviews < 100:
                reviews_data, continuation_token = reviews(
                    AppId,
                    lang='en',
                    country='in',
                    sort=Sort.NEWEST,
                    count=min(100, 100 - fetched_reviews),
                    continuation_token=continuation_token
                )
                
                if len(reviews_data) == 0:
                    print(f'No reviews fetched for {AppId}, breaking the loop.')
                    break

                all_reviews.extend(reviews_data)
                fetched_reviews += len(reviews_data)

                print(f'Fetched {len(reviews_data)} reviews for {AppId}...')

                if not continuation_token or fetched_reviews >= 100:
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

            playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
            print(f'Status updated for {AppId}')

        except Exception as e:
            print(f'Error fetching reviews for AppId {AppId}: {e}')

    return 'Successfully fetched and saved Google Play Store reviews'

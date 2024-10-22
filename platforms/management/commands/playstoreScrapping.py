import time
import datetime
from django.core.management.base import BaseCommand
from google_play_scraper import reviews, Sort
from django.contrib.contenttypes.models import ContentType
from platforms.models import playstoreProduct, review

class Command(BaseCommand):
    help = 'Fetch Google Play Store reviews and save them to the database'
    
    def add_arguments(self, parser):
        parser.add_argument('--sessionId', type=str, help='The session ID')
        parser.add_argument('--username', type=str, help='The username')

    def handle(self, *args, **options):
        # Get the sessionId and username from command line arguments
        sessionId = options['sessionId']
        username = options['username']

        # Fetch AppIds with 'pending' status for the given sessionId
        appid_list = playstoreProduct.objects.filter(Status='pending', sessionId=sessionId).values_list('AppId', flat=True).distinct()

        for AppId in appid_list:
            self.stdout.write(self.style.SUCCESS(f'Processing AppId: {AppId}'))
            
            try:
                # Paginated fetching of reviews
                self.stdout.write(self.style.SUCCESS(f'Fetching reviews for {AppId}...'))
                
                continuation_token = None  # To handle pagination
                all_reviews = []
                fetched_reviews = 0  # Track the total number of fetched reviews

                while fetched_reviews < 100:  # Limit to 100 reviews per app
                    # Fetch paginated reviews
                    reviews_data, continuation_token = reviews(
                        AppId,
                        lang='en',        # Language of the reviews
                        country='in',     # Restrict reviews to India
                        sort=Sort.NEWEST, # Sort by newest reviews
                        count=min(100, 100 - fetched_reviews),  # Fetch up to 100 reviews per app
                        continuation_token=continuation_token  # Handle pagination
                    )

                    # If no reviews are fetched, break the loop to avoid infinite loop
                    if len(reviews_data) == 0:
                        self.stdout.write(self.style.WARNING(f'No reviews fetched for {AppId}, breaking the loop.'))
                        break

                    # Append fetched reviews
                    all_reviews.extend(reviews_data)
                    fetched_reviews += len(reviews_data)  # Update the fetched review count

                    self.stdout.write(self.style.SUCCESS(f'Fetched {len(reviews_data)} reviews for {AppId}...'))

                    # Break loop if no more reviews are available or we have reached the limit of 100
                    if not continuation_token or fetched_reviews >= 100:
                        break

                self.stdout.write(self.style.SUCCESS(f'Total reviews fetched for {AppId}: {len(all_reviews)}'))

                # Process and save the reviews
                for review_data in all_reviews:
                    review_content = review_data.get('content', 'No content provided')
                    review_date = review_data.get('at', datetime.date.min)  # Use the earliest representable date as a fallback
                    rating = review_data.get('score', 0)
                    
                    # Save each review as a separate entry in the database
                    playstore_product_instance = playstoreProduct.objects.filter(AppId=AppId, Status='pending', sessionId=sessionId, user=username).first()
                    if playstore_product_instance:
                        content_type = ContentType.objects.get_for_model(playstoreProduct)
                        
                        # Check for existing review to avoid duplicates
                        existing_review = review.objects.filter(
                            content_type=content_type,
                            object_id=playstore_product_instance.id,
                            reviewContent=review_content,
                            user=username
                        ).exists()

                        if not existing_review:
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
                                self.stdout.write(self.style.ERROR(f"Error saving review for AppId {AppId}: {save_error}"))
                        else:
                            self.stdout.write(self.style.WARNING(f'Skipping duplicate review for AppId {AppId} by {username}'))

                # Update product status to 'completed' for this app
                playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
                self.stdout.write(self.style.SUCCESS(f'Status updated for {AppId}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fetching reviews for AppId {AppId}: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Google Play Store reviews'))

# import time
# import datetime
# import json
# from time import sleep
# from typing import List, Optional, Tuple

# from django.core.management.base import BaseCommand
# from django.contrib.contenttypes.models import ContentType

# from google_play_scraper import Sort
# from google_play_scraper.constants.element import ElementSpecs
# from google_play_scraper.constants.regex import Regex
# from google_play_scraper.constants.request import Formats
# from google_play_scraper.utils.request import post

# from platforms.models import playstoreProduct, review

# # Define MAX_COUNT_EACH_FETCH as per the new extraction technique
# MAX_COUNT_EACH_FETCH = 199

# # Redefine the _ContinuationToken class
# class _ContinuationToken:
#     __slots__ = (
#         "token",
#         "lang",
#         "country",
#         "sort",
#         "count",
#         "filter_score_with",
#         "filter_device_with",
#     )

#     def __init__(
#         self, token, lang, country, sort, count, filter_score_with, filter_device_with
#     ):
#         self.token = token
#         self.lang = lang
#         self.country = country
#         self.sort = sort
#         self.count = count
#         self.filter_score_with = filter_score_with
#         self.filter_device_with = filter_device_with

# # Redefine the _fetch_review_items function
# def _fetch_review_items(
#     url: str,
#     app_id: str,
#     sort: int,
#     count: int,
#     filter_score_with: Optional[int],
#     filter_device_with: Optional[int],
#     pagination_token: Optional[str],
# ):
#     dom = post(
#         url,
#         Formats.Reviews.build_body(
#             app_id,
#             sort,
#             count,
#             "null" if filter_score_with is None else filter_score_with,
#             "null" if filter_device_with is None else filter_device_with,
#             pagination_token,
#         ),
#         {"content-type": "application/x-www-form-urlencoded"},
#     )
#     match = json.loads(Regex.REVIEWS.findall(dom)[0])

#     return json.loads(match[0][2])[0], json.loads(match[0][2])[-2][-1]

# # Redefine the reviews function with the new extraction technique
# def reviews(
#     app_id: str,
#     lang: str = "en",
#     country: str = "us",
#     sort: Sort = Sort.MOST_RELEVANT,
#     count: int = 100,
#     filter_score_with: int = None,
#     filter_device_with: int = None,
#     continuation_token: _ContinuationToken = None,
# ) -> Tuple[List[dict], _ContinuationToken]:
#     sort = sort.value

#     if continuation_token is not None:
#         token = continuation_token.token

#         if token is None:
#             return (
#                 [],
#                 continuation_token,
#             )

#         lang = continuation_token.lang
#         country = continuation_token.country
#         sort = continuation_token.sort
#         count = continuation_token.count
#         filter_score_with = continuation_token.filter_score_with
#         filter_device_with = continuation_token.filter_device_with
#     else:
#         token = None

#     url = Formats.Reviews.build(lang=lang, country=country)

#     _fetch_count = count

#     result = []

#     while True:
#         if _fetch_count == 0:
#             break

#         if _fetch_count > MAX_COUNT_EACH_FETCH:
#             _fetch_count = MAX_COUNT_EACH_FETCH

#         try:
#             review_items, token = _fetch_review_items(
#                 url,
#                 app_id,
#                 sort,
#                 _fetch_count,
#                 filter_score_with,
#                 filter_device_with,
#                 token,
#             )
#         except (TypeError, IndexError):
#             # Continue on error to fetch as many reviews as possible
#             continue

#         for review in review_items:
#             result.append(
#                 {
#                     k: spec.extract_content(review)
#                     for k, spec in ElementSpecs.Review.items()
#                 }
#             )

#         _fetch_count = count - len(result)

#         if isinstance(token, list):
#             token = None
#             break

#     return (
#         result,
#         _ContinuationToken(
#             token, lang, country, sort, count, filter_score_with, filter_device_with
#         ),
#     )

# # You can also redefine reviews_all if needed
# def reviews_all(app_id: str, sleep_milliseconds: int = 0, **kwargs) -> list:
#     kwargs.pop("count", None)
#     kwargs.pop("continuation_token", None)

#     continuation_token = None

#     result = []

#     while True:
#         _result, continuation_token = reviews(
#             app_id,
#             count=MAX_COUNT_EACH_FETCH,
#             continuation_token=continuation_token,
#             **kwargs
#         )

#         result += _result

#         if continuation_token.token is None:
#             break

#         if sleep_milliseconds:
#             sleep(sleep_milliseconds / 1000)

#     return result

# # Now, define your management command as before
# class Command(BaseCommand):
#     help = 'Fetch Google Play Store reviews and save them to the database'
    
#     def add_arguments(self, parser):
#         parser.add_argument('--sessionId', type=str, help='The session ID')
#         parser.add_argument('--username', type=str, help='The username')

#     def handle(self, *args, **options):
#         # Get the sessionId and username from command line arguments
#         sessionId = options['sessionId']
#         username = options['username']

#         # Fetch AppIds with 'pending' status for the given sessionId
#         appid_list = playstoreProduct.objects.filter(Status='pending', sessionId=sessionId).values_list('AppId', flat=True).distinct()

#         for AppId in appid_list:
#             self.stdout.write(self.style.SUCCESS(f'Processing AppId: {AppId}'))
            
#             try:
#                 # Paginated fetching of reviews using the new extraction technique
#                 self.stdout.write(self.style.SUCCESS(f'Fetching reviews for {AppId}...'))
                
#                 continuation_token = None  # To handle pagination
#                 all_reviews = []
#                 fetched_reviews = 0  # Track the total number of fetched reviews

#                 while fetched_reviews < 2000:  # Updated limit to 2000 reviews per AppId
#                     # Fetch paginated reviews
#                     reviews_data, continuation_token = reviews(
#                         AppId,
#                         lang='en',        # Language of the reviews
#                         country='in',     # Fetch reviews from India
#                         sort=Sort.NEWEST, # Sort by newest reviews
#                         count=MAX_COUNT_EACH_FETCH,  # Use MAX_COUNT_EACH_FETCH from the new technique
#                         continuation_token=continuation_token  # Handle pagination
#                     )

#                     # If no reviews are fetched, break the loop to avoid infinite loop
#                     if len(reviews_data) == 0:
#                         self.stdout.write(self.style.WARNING(f'No reviews fetched for {AppId}, breaking the loop.'))
#                         break

#                     # Append fetched reviews
#                     all_reviews.extend(reviews_data)
#                     fetched_reviews += len(reviews_data)  # Update the fetched review count

#                     self.stdout.write(self.style.SUCCESS(f'Fetched {len(reviews_data)} reviews for {AppId}...'))

#                     # Break loop if no more reviews are available or we have reached the desired limit
#                     if continuation_token.token is None or fetched_reviews >= 2000:
#                         break

#                     # Optional: Sleep to prevent hitting request limits
#                     sleep(1)  # Sleep for 1 second between requests

#                 self.stdout.write(self.style.SUCCESS(f'Total reviews fetched for {AppId}: {len(all_reviews)}'))

#                 # Process and save the reviews
#                 for review_data in all_reviews:
#                     review_content = review_data.get('content', 'No content provided')
#                     review_date = review_data.get('at', datetime.date.min)  # Use the earliest representable date as a fallback
#                     rating = review_data.get('score', 0)
                    
#                     # Save each review as a separate entry in the database
#                     playstore_product_instance = playstoreProduct.objects.filter(AppId=AppId, Status='pending', sessionId=sessionId, user=username).first()
#                     if playstore_product_instance:
#                         content_type = ContentType.objects.get_for_model(playstoreProduct)
                        
#                         # Check for existing review to avoid duplicates
#                         existing_review = review.objects.filter(
#                             content_type=content_type,
#                             object_id=playstore_product_instance.id,
#                             reviewContent=review_content,
#                             user=username,
#                             sessionId=sessionId,
#                         ).exists()

#                         if not existing_review:
#                             try:
#                                 review_instance = review.objects.create(
#                                     content_type=content_type,
#                                     object_id=playstore_product_instance.id,
#                                     reviewContent=review_content,
#                                     rating=rating,
#                                     created_at=review_date,
#                                     user=username,
#                                     sessionId=sessionId,
#                                 )
#                             except Exception as save_error:
#                                 self.stdout.write(self.style.ERROR(f"Error saving review for AppId {AppId}: {save_error}"))
#                         else:
#                             self.stdout.write(self.style.WARNING(f'Skipping duplicate review for AppId {AppId} by {username}'))

#                 # Update product status to 'completed' for this app
#                 playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
#                 self.stdout.write(self.style.SUCCESS(f'Status updated for {AppId}'))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f'Error fetching reviews for AppId {AppId}: {e}'))

#         self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Google Play Store reviews'))

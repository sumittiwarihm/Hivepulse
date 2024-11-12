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
        sessionId = options['sessionId']
        username = options['username']

        appid_list = playstoreProduct.objects.filter(Status='pending', sessionId=sessionId).values_list('AppId', flat=True).distinct()

        for AppId in appid_list:
            self.stdout.write(self.style.SUCCESS(f'Processing AppId: {AppId}'))
            
            try:
                # Paginated fetching of reviews
                self.stdout.write(self.style.SUCCESS(f'Fetching reviews for {AppId}...'))
                continuation_token = None  # handlling pagination
                all_reviews = []
                fetched_reviews = 0  # Tracking  the total number of review fetched
                while fetched_reviews < 100:  # Limit to 100 reviews per app
                    # Fetch paginated reviews
                    reviews_data, continuation_token = reviews(
                        AppId,
                        lang='en',        
                        country='in',     
                        sort=Sort.NEWEST,
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
                            self.stdout.write(self.style.ERROR(f"Error saving review for AppId {AppId}: {save_error}"))
                # Update product status to 'completed' for this app
                playstoreProduct.objects.filter(AppId=AppId, sessionId=sessionId, user=username).update(Status='completed')
                self.stdout.write(self.style.SUCCESS(f'Status updated for {AppId}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fetching reviews for AppId {AppId}: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully fetched and saved Google Play Store reviews'))


# from django.core.management.base import BaseCommand
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# from scipy.special import softmax
# from platforms.models import review, sentimentResult  # Replace 'myapp' with your actual app name
# from django.core.management.base import BaseCommand
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# from scipy.special import softmax
# from django.contrib.contenttypes.models import ContentType
# from platforms.models import review, sentimentResult, amazonProduct  # Adjust import to match your app structure

# class Command(BaseCommand):
#     help = 'Performs sentiment analysis on reviews related to Amazon products and stores the results'

#     def handle(self, *args, **options):
#         # Load the RoBERTa model and tokenizer
#         MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
#         tokenizer = AutoTokenizer.from_pretrained(MODEL)
#         model = AutoModelForSequenceClassification.from_pretrained(MODEL)

#         def polarity_scores_roberta(text):
#             encoded_text = tokenizer(
#                 text, 
#                 return_tensors='pt', 
#                 truncation=True,  
#                 max_length=512    
#             )
#             if len(encoded_text['input_ids'][0]) > 512:
#                 print(f"Text truncated: {len(encoded_text['input_ids'][0])} tokens")
            
#             output = model(**encoded_text)
#             scores = output.logits[0].detach().cpu().numpy()
#             scores = softmax(scores)
#             scores_dict = {
#                 'negativeScore': scores[0],
#                 'neutralScore': scores[1],
#                 'positiveScore': scores[2]
#             }
#             return scores_dict

#         def classify_sentiment(pos_score, neg_score, neu_score, threshold=0.5):
#             if pos_score > neg_score and pos_score > neu_score and pos_score >= threshold:
#                 return 'Positive'
#             elif neg_score > pos_score and neg_score > neu_score and neg_score >= threshold:
#                 return 'Negative'
#             else:
#                 return 'Neutral'

#         def analyze_and_store_sentiment():
#             # Get the ContentType for the amazonProduct model
#             amazon_product_content_type = ContentType.objects.get_for_model(amazonProduct)
            
#             # Filter reviews related to amazonProduct
#             amazon_product_reviews = review.objects.filter(content_type=amazon_product_content_type)

#             for rev in amazon_product_reviews:
#                 # Check if this review has already been processed
#                 if sentimentResult.objects.filter(review_id=rev.id).exists():
#                     print(f'Sentiment already exists for review ID {rev.id}, skipping...')
#                     continue

#                 text = rev.reviewContent
#                 roberta_result = polarity_scores_roberta(text)
                
#                 # Classify sentiment
#                 estimated_result = classify_sentiment(
#                     roberta_result['positiveScore'], 
#                     roberta_result['negativeScore'], 
#                     roberta_result['neutralScore']
#                 )
                
#                 # Create and save sentimentResult instance, storing the primary key of the review
#                 sentiment = sentimentResult(
#                     review_id=rev.id,  # Storing the primary key directly
#                     positiveScore=roberta_result['positiveScore'],
#                     neutralScore=roberta_result['neutralScore'],
#                     negativeScore=roberta_result['negativeScore'],
#                     estimatedResult=estimated_result
#                 )
#                 sentiment.save()
#                 print(f'Sentiment saved for review ID {rev.id}')

#         # Execute sentiment analysis
#         analyze_and_store_sentiment()

from django.core.management.base import BaseCommand
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from django.contrib.contenttypes.models import ContentType
from platforms.models import review, sentimentResult, amazonProduct
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction, IntegrityError, reset_queries

class Command(BaseCommand):
    help = 'Performs sentiment analysis on reviews related to Amazon products and stores the results'
    def add_arguments(self, parser):
        parser.add_argument('--sessionId', type=str, help='The session ID')
        parser.add_argument('--username', type=str, help='The username')

    def handle(self, *args, **options):
        sessionId = options['sessionId']
        username = options['username']
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
            if len(encoded_text['input_ids'][0]) > 512:
                print(f"Text truncated: {len(encoded_text['input_ids'][0])} tokens")
            
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
                # Start a transaction to ensure atomicity
                with transaction.atomic():   # although this is not of much use beacause we are just taking snapshot of review and storing i array then doing mutithreading
                    # Lock the row for the review to prevent concurrent access
                    review_locked = review.objects.select_for_update().get(id=rev.id)
                  # #### we can improve this by selecting only unprocessed review so that we can avoide cheking for already present sentiment
                    # Check if this review has already been processed
                    if sentimentResult.objects.filter(review_id=review_locked.id).exists():
                        print(f'Sentiment already exists for review ID {review_locked.id}, skipping...')
                        return

                    text = review_locked.reviewContent
                    roberta_result = polarity_scores_roberta(text)
                    
                    # Classify sentiment
                    estimated_result = classify_sentiment(
                        roberta_result['positiveScore'], 
                        roberta_result['negativeScore'], 
                        roberta_result['neutralScore']
                    )
                    
                    # Create and save sentimentResult instance, storing the primary key of the review
                    sentiment = sentimentResult(
                        review_id=review_locked.id,  # Storing the primary key directly
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
                reset_queries()  # Clear the query cache to avoid memory bloat

        def analyze_and_store_sentiment():
            # Get the ContentType for the amazonProduct model
            amazon_product_content_type = ContentType.objects.get_for_model(amazonProduct)
            
            # Filter reviews related to amazonProduct
            amazon_product_reviews = review.objects.filter(content_type=amazon_product_content_type)
            review_toprocess=amazon_product_reviews.filter(user=username,sessionId=sessionId)
           # we can improve this by selecting only unprocessed review so that we can avoide cheking for already present sentiment
            # Use ThreadPoolExecutor to process reviews concurrently
            with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers based on your CPU
                future_to_review = {executor.submit(process_review, rev): rev for rev in review_toprocess}
                
                for future in as_completed(future_to_review):
                    try:
                        future.result()  # This will raise any exceptions caught during processing
                    except Exception as e:
                        print(f"Exception occurred while processing a review: {e}")

        # Execute sentiment analysis
        analyze_and_store_sentiment()



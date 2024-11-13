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

# utilsAmazonScrapping.py

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

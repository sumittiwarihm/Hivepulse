import re
from collections import defaultdict

# Define Categories, Keywords, and Synonyms
CATEGORY_KEYWORDS = {
    'appExperience': [
        'app', 'interface', 'ui', 'design', 'login', 'navigation', 'update', 'otp', 'layout', 'screen',
        'button', 'icon', 'responsive', 'crash', 'bug', 'slow', 'freeze', 'glitch', 'issue', 'error',
        'fix', 'loading', 'lag', 'technical', 'user-friendly', 'visuals', 'functionality', 'accessibility',
        'customization', 'interaction', 'feedback', 'usage', 'operation', 'performance', 'experience'
    ],
    'price': [
        'price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'worth', 'pricing', 'overpriced',
        'underpriced', 'discount', 'sale', 'budget', 'economical', 'high-priced', 'low-priced', 'deal',
        'bargain', 'fee', 'charge', 'expense'
    ],
    'deliveryRelated': [
        'delivery', 'shipping', 'courier', 'arrival', 'delayed', 'on-time', 'fast', 'slow', 'package',
        'tracking', 'lost', 'damaged', 'late', 'prompt', 'service', 'express', 'logistics', 'dispatch',
        'estimate', 'schedule', 'shipped', 'received'
    ],
    'qualityOfProduct': [
        'quality', 'durability', 'reliability', 'performance', 'defective', 'broken', 'faulty',
        'material', 'workmanship', 'finish', 'longevity', 'sturdy', 'well-made', 'substandard',
        'high-quality', 'low-quality', 'malfunction', 'damage', 'defect', 'issues', 'poor', 'good'
    ],
    'customerSupport': [
        'support', 'service', 'help', 'assistance', 'customer service', 'response', 'resolution',
        'feedback', 'complaint', 'representative', 'agent', 'chat', 'email', 'phone', 'inquiry',
        'issue', 'problem', 'satisfaction', 'follow-up', 'experience', 'contact', 'query'
    ],
    'paymentRelated': [
        'payment', 'transaction', 'billing', 'charge', 'checkout', 'invoice', 'refund', 'credit card',
        'debit card', 'paypal', 'method', 'currency', 'fee', 'gateway', 'online payment', 'processing',
        'authorization', 'declined', 'failed payment', 'installment', 'emi', 'wallet', 'receipt', 'order',
        'amount', 'confirmation', 'auto-pay', 'direct debit', 'overcharge', 'payment plan', 'payment method'
    ]
}

def assign_category(review_text, category_keywords, priority_order=None):
    """
    Assigns the most relevant category to the review based on keyword matches.
    If multiple categories match, selects based on priority_order.

    Parameters:
        review_text (str): The content of the review.
        category_keywords (dict): Dictionary mapping categories to lists of keywords.
        priority_order (list, optional): List defining category precedence in case of tie matches.

    Returns:
        str: The assigned category.
    """
    if not review_text:
        return 'other'

    # Clean and tokenize the review text using regex
    review_text_lower = review_text.lower()
    review_text_clean = re.sub(r'[^\w\s]', '', review_text_lower)
    words_in_review = set(review_text_clean.split())

    # Initialize match counts
    category_match_count = {}
    for category, keywords in category_keywords.items():
        matches = words_in_review.intersection(set(keywords))
        category_match_count[category] = len(matches)

    # Determine the category with the highest matches
    max_matches = max(category_match_count.values())
    
    if max_matches == 0:
        # Assign fallback category based on review length or common fallback (e.g., customerSupport for short reviews)
        if len(review_text_clean.split()) <= 5:  # Short review assumption
            return 'customerSupport'
        return 'other'
    else:
        # Get all categories with the maximum matches
        categories_with_max = [cat for cat, count in category_match_count.items() if count == max_matches]
        if priority_order:
            for cat in priority_order:
                if cat in categories_with_max:
                    return cat
        return categories_with_max[0]

def serialize_sentiment_aggregation(sentiment_counts):
    """
    Serializes the sentiment_counts dictionary into a list of dictionaries.

    Parameters:
        sentiment_counts (defaultdict): Aggregated sentiment counts.

    Returns:
        list: List of serialized data entries.
    """
    serialized_data = []
    for (brand, category), counts in sentiment_counts.items():
        data_entry = {
            'brand': brand,
            'category': category,
            'positiveCount': counts['positive'],
            'negativeCount': counts['negative'],
            'neutralCount': counts['neutral']
        }
        serialized_data.append(data_entry)
    return serialized_data

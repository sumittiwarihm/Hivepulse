from sentence_transformers import SentenceTransformer, util
# Load the pre-trained Sentence-BERT model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
# Define a description for each category that captures its semantic meaning
CATEGORY_DESCRIPTIONS1 = {
    'appExperience': 'Issues with the application design, layout, performance, and usability.',
    'price': 'Comments on the pricing, value, affordability, and costs.',
    'deliveryRelated': 'Feedback about delivery speed, condition of items on arrival, and tracking.',
    'qualityOfProduct': 'Quality and durability of the product, such as material and reliability.',
    'customerSupport': 'Experiences with customer service, help received, and complaint resolution.',
    'paymentRelated': 'Issues with payment processing, methods, transactions, and fees.'
}
CATEGORY_DESCRIPTIONS2 = {
    'Product Quality': 'Comments on the overall quality, durability, and reliability of the product, such as material and performance.',
    'Delivery & Service': 'Feedback on the delivery speed, condition of items on arrival, customer service, and issue resolution.',
    'Value & Affordability': 'Thoughts on pricing, value for money, and affordability in comparison to similar products.',
    'Appearance & Presentation': 'Observations on the product’s appearance, design, and presentation upon arrival.'
}

# Encode category descriptions
category_embeddings1 = {category: model.encode(description) for category, description in CATEGORY_DESCRIPTIONS1.items()}
category_embeddings2 = {category: model.encode(description) for category, description in CATEGORY_DESCRIPTIONS2.items()}

# Define a priority order for categories to resolve ties if needed
PRIORITY_ORDER1 = [
    'qualityOfProduct',
    'appExperience', 
    'price', 
    'deliveryRelated',  
    'paymentRelated'
    'customerSupport',
]
PRIORITY_ORDER2 =['Product Quality',
                  'Value & Affordability',
                    'Delivery & Service',
                    'Appearance & Presentation'
                  ]


def assign_category(review_text,  priority_order=PRIORITY_ORDER1):
    """
    Assigns the most relevant category to the review based on similarity scores.
    If multiple categories have the same similarity, resolves the tie based on priority_order.

    Parameters:
        review_text (str): The content of the review.
        priority_order (list): List defining category precedence in case of tie matches.

    Returns:
        str: The assigned category.
    """
    # Encode the review text
    review_embedding = model.encode(review_text)
    
    # Calculate similarity with each category and store in a dictionary
    similarities = {}
    for category, category_embedding in category_embeddings1.items():
        similarity = util.cos_sim(review_embedding, category_embedding).item()
        similarities[category] = similarity

    # Find category with the highest similarity
    best_category = max(similarities, key=similarities.get)
    max_similarity = similarities[best_category]

    # Check for any ties in similarity
    tied_categories = [cat for cat, sim in similarities.items() if sim == max_similarity]

    # If there's a tie, use priority order to decide the category
    if len(tied_categories) > 1:
        for category in priority_order:
            if category in tied_categories:
                return category

    return best_category
def assign_category2(review_text, priority_order=PRIORITY_ORDER2):
    """
    Assigns the most relevant category to the review based on similarity scores.
    If multiple categories have the same similarity, resolves the tie based on priority_order.

    Parameters:
        review_text (str): The content of the review.
        priority_order (list): List defining category precedence in case of tie matches.

    Returns:
        str: The assigned category.
    """
    # Encode the review text
    review_embedding = model.encode(review_text)
    
    # Calculate similarity with each category and store in a dictionary
    similarities = {}
    for category, category_embedding in category_embeddings2.items():
        similarity = util.cos_sim(review_embedding, category_embedding).item()
        similarities[category] = similarity

    # Find category with the highest similarity
    best_category = max(similarities, key=similarities.get)
    max_similarity = similarities[best_category]

    # Check for any ties in similarity
    tied_categories = [cat for cat, sim in similarities.items() if sim == max_similarity]

    # If there's a tie, use priority order to decide the category
    if len(tied_categories) > 1:
        for category in priority_order:
            if category in tied_categories:
                return category

    return best_category























# # import re
# # from collections import defaultdict
# CATEGORY_KEYWORDS = {
#     'appExperience': [
#         'app', 'interface', 'ui', 'design', 'login', 'navigation', 'update', 'otp', 'layout', 'screen',
#         'button', 'icon', 'responsive', 'crash', 'bug', 'slow', 'freeze', 'glitch', 'issue', 'error',
#         'fix', 'loading', 'lag', 'technical', 'user-friendly', 'visuals', 'functionality', 'accessibility',
#         'customization', 'interaction', 'feedback', 'usage', 'operation', 'performance', 'experience'
#     ],
#     'price': [
#         'price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'worth', 'pricing', 'overpriced',
#         'underpriced', 'discount', 'sale', 'budget', 'economical', 'high-priced', 'low-priced', 'deal',
#         'bargain', 'fee', 'charge', 'expense'
#     ],
#     'deliveryRelated': [
#         'delivery', 'shipping', 'courier', 'arrival', 'delayed', 'on-time', 'fast', 'slow', 'package',
#         'tracking', 'lost', 'damaged', 'late', 'prompt', 'service', 'express', 'logistics', 'dispatch',
#         'estimate', 'schedule', 'shipped', 'received'
#     ],
#     'qualityOfProduct': [
#         'quality', 'durability', 'reliability', 'performance', 'defective', 'broken', 'faulty',
#         'material', 'workmanship', 'finish', 'longevity', 'sturdy', 'well-made', 'substandard',
#         'high-quality', 'low-quality', 'malfunction', 'damage', 'defect', 'issues', 'poor', 'good'
#     ],
#     'customerSupport': [
#         'support', 'service', 'help', 'assistance', 'customer service', 'response', 'resolution',
#         'feedback', 'complaint', 'representative', 'agent', 'chat', 'email', 'phone', 'inquiry',
#         'issue', 'problem', 'satisfaction', 'follow-up', 'experience', 'contact', 'query'
#     ],
#     'paymentRelated': [
#         'payment', 'transaction', 'billing', 'charge', 'checkout', 'invoice', 'refund', 'credit card',
#         'debit card', 'paypal', 'method', 'currency', 'fee', 'gateway', 'online payment', 'processing',
#         'authorization', 'declined', 'failed payment', 'installment', 'emi', 'wallet', 'receipt', 'order',
#         'amount', 'confirmation', 'auto-pay', 'direct debit', 'overcharge', 'payment plan', 'payment method'
#     ]
# }


# def assign_category(review_text, category_keywords, priority_order=None,):
#     """
#     Assigns the most relevant category to the review based on keyword matches.
#     If multiple categories match, selects based on priority_order.

#     Parameters:
#         review_text (str): The content of the review.
#         category_keywords (dict): Dictionary mapping categories to lists of keywords.
#         priority_order (list, optional): List defining category precedence in case of tie matches.

#     Returns:
#         str: The assigned category.
#     """
#     if not review_text:
#         return 'other'

#     # Clean and tokenize the review text using regex
#     review_text_lower = review_text.lower()
#     review_text_clean = re.sub(r'[^\w\s]', '', review_text_lower)
#     words_in_review = set(review_text_clean.split())

#     # Initialize match counts
#     category_match_count = {}
#     for category, keywords in category_keywords.items():
#         matches = words_in_review.intersection(set(keywords))
#         category_match_count[category] = len(matches)
#     # Determine the category with the highest matches
#     max_matches = max(category_match_count.values())
#     if max_matches == 0:
#         return 'other'
#     else:
#         # Get all categories with the maximum matches
#         categories_with_max = [cat for cat, count in category_match_count.items() if count == max_matches]
#         if priority_order:
#             for cat in priority_order:
#                 if cat in categories_with_max:
#                     return cat
#         return categories_with_max[0]
    
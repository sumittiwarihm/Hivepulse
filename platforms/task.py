# import time
# from .models import TaskStatus
# from django.db import transaction
# def scrapping_task(user, session_id):
#     try:
#         with transaction.atomic():
#             TaskStatus.objects.update_or_create(
#                 user=user,
#                 session_id=session_id,
#                 defaults={'scrapping_status': "Running", 'scrapping_completed': False}
#             )
#         time.sleep(6)
#         TaskStatus.objects.filter(user=user, session_id=session_id).update(
#             scrapping_status="Completed", scrapping_completed=True
#         )
#         return f"Scrapping completed for session {session_id}"
#     except Exception as e:
#         TaskStatus.objects.filter(user=user, session_id=session_id).update(
#             scrapping_status=f"Error: {str(e)}"
#         )
#         raise
# def sentiment_task(user, session_id):
#     try:
#         with transaction.atomic():
#             TaskStatus.objects.update_or_create(
#                 user=user,
#                 session_id=session_id,
#                 defaults={'sentiment_status': "Running", 'sentiment_completed': False}
#             )
#         time.sleep(5) 
#         TaskStatus.objects.filter(user=user, session_id=session_id).update(
#             sentiment_status="Completed", sentiment_completed=True
#         )
#         return f"Sentiment Analysis completed for session {session_id}"
#     except Exception as e:
#         TaskStatus.objects.filter(user=user, session_id=session_id).update(
#             sentiment_status=f"Error: {str(e)}"
#         )
#         raise
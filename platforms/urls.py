from django.urls import path ,include
from . import views
urlpatterns = [
    path('' , views.home , name='home'),
    path('login/', views.login, name='login'),
    path('login-page/', views.loginPage, name='loginPage'),
    path('logout/', views.logout_view, name='logoutPage'),
    path('downloadAmazonTemplate/', views.DownloadAmazonExcelTemplateView.as_view(), name='downloadAmazonExcelTemplate'),
    path('downloadFlipkartExcelTemplate/' , views.downloadFlipkartExcelTemplate.as_view(), name='downloadFlipkartExcelTemplate') ,
    path('downloadPlaystoreExcelTemplate/' , views.downloadPlaystoreExcelTemplate.as_view(), name='downloadPlaystoreExcelTemplate') ,
    path('amazonPage/' , views.amazonPage, name='amazonPage') ,
    path('flipkartPage/' , views.flipkartPage, name='flipkartPage') ,
    path('playstorePage/' , views.playstorePage, name='playstorePage') ,
    path('uploadAmazon/', views.uploadAmazon.as_view(), name='uploadAmazon'),
    path('uploadFlipkart/', views.uploadFlipkart.as_view(), name='uploadFlipkart'),
    path('uploadPlaystore/', views.uploadPlaystore.as_view(), name='uploadPlaystore'),
    path('api/verify-token/', views.verify_token, name='verify_token'),
    path('run-amazonScript-scrapping/' ,views.runAmazonReviewScrappingScript.as_view(), name='runAmazonReviewScrappingScript'),
    path('run-amazonScript-sentiment/' , views.runAmazonReviewSentimentScript.as_view(),name='runAmazonReviewSentimentScript'),
    path('run-flipkartScript-scrapping/' ,views.runFlipkartReviewScrappingScript.as_view(), name='runFlipkartReviewScrappingScript'), 
    path('run-flipkartScript-sentiment/' , views.runFlipkartReviewSentimentScript.as_view(),name='runFlipkartReviewSentimentScript'),
    path('run-playstoreScript-scrapping/' ,views.runPlaystoreReviewScrappingScript.as_view(), name='runPlaystoreReviewScrappingScript'),
    path('run-playstoreScript-sentiment/' , views.runPlaystoreReviewSentimentScript.as_view(),name='runPlaystoreReviewSentimentScript'),
    path('product-sentiment/', views.product_sentiment_view, name='product_sentiment_view'),
    path('download-excel/', views.download_excel, name='download_excel'),
    #---------------experiment----------------------------------------------------
    path('session-input-playstore/', views.sessionInputPlaystore, name='sessionInputPlaystore1'),
    path('session-input-amazon/',views.sessionInputAmazon, name='sessionInputAmazon'),
    path('session-input-flipkart/',views.sessionInputFlipkart, name='sessionInputFlipkart'),
    # path('graph/', views.getDataForPlaystoreGraph, name='getDataForPlaystoreGraph'),
    path('dataforPlaystoreCategorization/',views.getDataforPlaystoreCategorization,name='getDataforPlaystoreCategorization'), 
    path('dataforAmazonCategorization/',views.getDataForAmazonCategorization,name='getDataForAmazonCategorization')  ,
    path('dataforFlipkartCategorization/',views.getDataForFlipkartCategorization,name='getDataForFlipkartCategorization'),
    path('RawReport/',views.GetRawPage,name="rawReportPage") 
]


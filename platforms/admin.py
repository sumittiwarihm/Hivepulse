from django.contrib import admin
from .models import amazonProduct,flipkartProduct,playstoreProduct,review,sentimentResult
# Register your models here.
admin.site.register(amazonProduct)
admin.site.register(flipkartProduct)
admin.site.register(playstoreProduct)
@admin.register(review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'reviewContent', 'rating', 'created_at')
admin.site.register(sentimentResult)


from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.contrib.auth.models import User
class amazonProduct(models.Model):
  
    id = models.AutoField(primary_key=True)
    Asin = models.CharField(max_length=50)
    Brand = models.CharField(max_length=500)
    Status = models.CharField(max_length=50, default="pending")
    Date = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100) 
    sessionId = models.CharField(max_length=100) 

    def __str__(self):
        return f"{self.Asin} - {self.Brand}"
    
class flipkartProduct(models.Model):
   
    id = models.AutoField(primary_key=True)
    Fsn = models.CharField(max_length=50)
    Brand = models.CharField(max_length=500)
    Status = models.CharField(max_length=50,  default="pending")
    Date = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100) 
    sessionId = models.CharField(max_length=100) 

    def __str__(self):
        return f"{self.Fsn} - {self.Brand}"

class playstoreProduct(models.Model):
    
    id = models.AutoField(primary_key=True)
    AppId = models.CharField(max_length=50)
    Brand = models.CharField(max_length=500)
    Status = models.CharField(max_length=50,  default="pending")
    Date = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100) 
    sessionId = models.CharField(max_length=100) 
    def __str__(self):
        return f"{self.AppId} - {self.Brand}"

class review(models.Model):
    id = models.AutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reviewContent = models.TextField()  # This field can store a large amount of text
    rating = models.IntegerField()
    user = models.CharField(max_length=100) 
    sessionId = models.CharField(max_length=100) 
    # Status = models.CharField(max_length=50,  default="pending")
    created_at =  models.DateField()  # No default, should be provided during instance creation
    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

class sentimentResult(models.Model):
    id = models.AutoField(primary_key=True)
    review = models.ForeignKey('review', on_delete=models.CASCADE, null=False, blank=False)
    positiveScore = models.FloatField(default=0)  
    neutralScore = models.FloatField(default=0)  
    negativeScore = models.FloatField(default=0)
    user = models.CharField(max_length=100) 
    sessionId = models.CharField(max_length=100) 
    estimatedResult= models.CharField(max_length=50 ,default='')  # it is not nesccesary to store because it can be computed on the fly



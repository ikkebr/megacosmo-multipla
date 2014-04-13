from django.db import models
from base.models import Planet

class Message(models.Model):
    date = models.DateTimeField(auto_now=True, auto_now_add=True)
    p_from = models.ForeignKey(Planet)
    p_to = models.ForeignKey(Planet, related_name="received")
    
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-date',)
        
        
class News(models.Model):
    date = models.DateTimeField(auto_now=True, auto_now_add=True)
    icon = models.CharField(max_length=30)
    content = models.TextField()
    planet = models.ForeignKey(Planet)
    
    read = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-date',)

    
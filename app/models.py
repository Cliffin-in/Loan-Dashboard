from django.db import models

# Create your models here.


class AccessToken(models.Model):
    location_id = models.CharField(unique=True,max_length=100)
    access = models.TextField()
    refresh = models.TextField()
    expiry = models.DateTimeField()

    def __str__(self):
        return self.location_id
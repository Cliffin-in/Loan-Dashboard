from django.db import models

# Create your models here.


class AccessToken(models.Model):
    location_id = models.CharField(unique=True,max_length=100)
    access = models.TextField()
    refresh = models.TextField()
    expiry = models.DateTimeField()

    def __str__(self):
        return self.location_id
    


class ProcessingOpportunities(models.Model):
    opp_id = models.CharField(unique=True,max_length=255)
    opp_name = models.TextField(null=True,blank=True)
    pipeline_id = models.TextField(null=True,blank=True)
    pipeline_name = models.TextField(null=True,blank=True)
    stage_id = models.TextField(null=True,blank=True)
    stage_name = models.TextField(null=True,blank=True)
    monetary_value = models.TextField(null=True,blank=True)
    close_due_date = models.TextField(null=True,blank=True)
    actual_closed_date = models.TextField(null=True,blank=True)
    original_close_due_date = models.TextField(null=True,blank=True)
    loan_type = models.TextField(null=True,blank=True)
    assigned_user_id = models.TextField(null=True,blank=True)
    assigned_user_name = models.TextField(null=True,blank=True)
    explanation = models.TextField(null=True,blank=True)
    how_many_times_lender_change = models.TextField(null=True,blank=True)
    exists_in_ghl = models.BooleanField(default=False)
    
class TotalOpportunties(models.Model):
    opp_id = models.CharField(unique=True,max_length=255)
    pipeline_id = models.TextField(null=True,blank=True)
    pipeline_name = models.TextField(null=True,blank=True)
    stage_id = models.TextField(null=True,blank=True)
    stage_name = models.TextField(null=True,blank=True)
    exists_in_ghl = models.BooleanField(default=False)

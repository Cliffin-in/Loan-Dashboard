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
    opp_name = models.TextField()
    pipeline_id = models.TextField()
    pipeline_name = models.TextField()
    stage_id = models.TextField()
    stage_name = models.TextField()
    monetary_value = models.TextField()
    close_due_date = models.TextField()
    actual_closed_date = models.TextField()
    loan_type = models.TextField()
    assigned_user_id = models.TextField()
    assigned_user_name = models.TextField()
    explanation = models.TextField()
    how_many_times_lender_change = models.TextField()
    exists_in_ghl = models.BooleanField(default=False)
    
class TotalOpportunties(models.Model):
    opp_id = models.CharField(unique=True,max_length=255)
    pipeline_id = models.TextField()
    pipeline_name = models.TextField()
    stage_id = models.TextField()
    stage_name = models.TextField()
    exists_in_ghl = models.BooleanField(default=False)

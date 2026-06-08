from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

User = get_user_model()


class ContentType(models.Model):
    TYPE_CHOICES = [
        ('blog', 'Blog Post'),
        ('article', 'Article'),
        ('cover_letter', 'Cover Letter'),
        ('social', 'Social Media Post'),
        ('email', 'Email'),
        ('product_desc', 'Product Description'),
        ('ad_copy', 'Ad Copy'),
        ('seo_meta', 'SEO Meta Description'),
        ('press_release', 'Press Release'),
        ('script', 'Video Script'),
    ]

    name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_prompt = models.TextField(help_text="System prompt for this content type")
    default_tokens = models.IntegerField(default=500)
    price_per_token = models.DecimalField(max_digits=10, decimal_places=6, default=0.000002)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_name']
        db_table = 'content_types'

    def __str__(self):
        return self.display_name
    


class ContentGenerationTasks(models.Model):
    STATUS_CHOICES = {
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('queued', 'Queued'),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_id = models.CharField(max_length=100, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_tasks')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='tasks')
    prompt = models.TextField()
    generated_content = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    
    parameters = models.JSONField(default=dict, help_text="Generation parameters")
    
    processing_time = models.FloatField(null=True, blank=True)
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    error_code = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        ordering = ['-created_at']
        db_table = 'content_tasks'
        indexes = [
            models.Index(fields=['status', 'user']),
            models.Index(fields=['celery_task_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'status', '-created_at']),
        ]

    
    def __str__(self):
        return f"Task {self.id} - {self.user.email} - {self.status}"
    

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"req_{uuid.uuid4().hex[:16]}"
        
        if self.status == 'processing' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.tokens_used > 0:
                self.user.profile.consume_credits(self.tokens_used, self.cost)
        
        super().save(*args, **kwargs)


class BatchJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_jobs')
    tasks = models.ManyToManyField(ContentGenerationTasks, related_name='batches')
    name = models.CharField(max_length=200, blank=True)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    failed_tasks = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    celery_group_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'batch_jobs'
    
    def __str__(self):
        return f"Batch {self.id} - {self.user.email}"
    
    def update_progress(self):
        self.completed_tasks = self.tasks.filter(status='completed').count()
        self.failed_tasks = self.tasks.filter(status='failed').count()
        
        if self.completed_tasks + self.failed_tasks == self.total_tasks:
            self.status = 'completed'
            self.completed_at = timezone.now()
        
        self.save()



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tier = models.CharField(max_length=20, default='free')
    monthly_token_limit = models.IntegerField(default=10000)
    monthly_token_used = models.IntegerField(default=0)
    monthly_request_limit = models.IntegerField(default=100)
    monthly_request_used = models.IntegerField(default=0)


    def has_remaining_creadits(self):
        return self.monthly_token_used < self.monthly_token_limit
    

    def __str__(self):
        return f"{self.user.email} - {self.tier}"
    

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver (post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
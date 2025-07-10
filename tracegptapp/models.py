from django.db import models
from django.utils import timezone
from multiselectfield import MultiSelectField

class ChatExample(models.Model):
    """Predefined chatbot examples with expected responses and tags"""
    
    TAG_CHOICES = (
        ('correct', 'Correct'),
        ('misleading', 'Misleading'),
        ('incomplete', 'Incomplete'),
        ('slow', 'Slow'),
    )
    
    title = models.CharField(max_length=100)
    input_prompt = models.TextField()
    expected_response = models.TextField()
    tags = MultiSelectField(choices=TAG_CHOICES, max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
        
class ChatTrace(models.Model):
    """Records of chatbot interactions and their traces"""
    
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('error', 'Error'),
    )
    
    TAG_CHOICES = (
        ('correct', 'Correct'),
        ('misleading', 'Misleading'),
        ('incomplete', 'Incomplete'),
        ('slow', 'Slow'),
    )
    
    run_id = models.CharField(max_length=100, unique=True)
    input_prompt = models.TextField()
    output_response = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    tags = MultiSelectField(choices=TAG_CHOICES, max_length=50, blank=True)
    runtime_seconds = models.FloatField(default=0.0)
    trace_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Trace {self.run_id[:8]} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']

class TraceStep(models.Model):
    """Individual steps within a chat trace"""
    
    trace = models.ForeignKey(ChatTrace, on_delete=models.CASCADE, related_name='steps')
    step_name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=50)
    input_data = models.JSONField(default=dict, null=True, blank=True)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    runtime_seconds = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.step_name} ({self.runtime_seconds:.2f}s)"
    
    class Meta:
        ordering = ['start_time']

class ContactMessage(models.Model):
    """Contact form submissions"""
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('spam', 'Spam'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Message from {self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

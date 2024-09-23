import mimetypes
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_project_name(value):
    if not value.isalnum():
        raise ValidationError(_("Project name must contain only alphanumeric characters."))

class User(AbstractUser):
    is_online = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)

class Project(models.Model):
    name = models.CharField(max_length=255, unique=True, validators=[validate_project_name])
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='projects')
    processed_location = models.CharField(max_length=255, blank=True, null=True)
    is_processing_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class UploadedFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(help_text="File size in bytes", null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.file_name or self.file.name} (Project: {self.project.name})"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.project.is_processing_complete = False
            self.project.save()
            
            # Populate file metadata
            if self.file:
                self.file_name = self.file.name
                self.file_size = self.file.size
                self.file_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-uploaded_at']

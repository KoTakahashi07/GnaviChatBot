from django.db import models
from django.utils import timezone
from django.conf import settings
 
class ChatBotSession(models.Model):
    user_id = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        default=''
        )
    watson_session = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        default=''
        )
    next_logic = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        default=''
        )
    expire_time = models.DateTimeField(
        default=timezone.now() + timezone.timedelta(minutes=settings.SESSION_EXPIRE_MIN)
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def check_session(self):
        session_flag = False
        if self.expire_time > timezone.now():
            session_flag = True
        else:
            session_flag = False
        return session_flag
 
    def update_expire_time(self):
        self.expire_time = timezone.now() + timezone.timedelta(minutes=settings.SESSION_EXPIRE_MIN)
        return self.expire_time
    
    
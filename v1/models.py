from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from rest_framework.views import APIView


class UserManager(BaseUserManager):
  use_in_migrations = True
  
  def _create_user(self, username, unique_id, grade, room, number, profile_image=None, **extra_fields):
    if not unique_id:
      raise ValueError('No unique id.')
    
    user = self.model(unique_id=unique_id, grade=grade, room=room, number=number, username=username, profile_image=profile_image, **extra_fields)
    user.save(using=self.db)
    
    return user
    
  def create_user(self, username, unique_id, grade, room, number, profile_image=None, **extra_fields):
    extra_fields.setdefault('is_staff', False)
    extra_fields.setdefault('is_superuser', False)
    
    return self._create_user(username, unique_id, grade, room, number, profile_image, **extra_fields)


class User(AbstractUser):
  object = UserManager()
  
  unique_id = models.CharField(verbose_name='pk', db_column='pk', primary_key='True', max_length=255, null=False, unique=True)
  username = models.CharField(verbose_name='user_name', db_column='user_name', max_length=10)
  grade = models.IntegerField(verbose_name='grade', db_column='grade')
  room = models.IntegerField(verbose_name='room', db_column='room')
  number = models.IntegerField(verbose_name='number', db_column='number')
  profile_image = models.CharField(verbose_name='profile_image', db_column='profile_image', max_length=255, null=True)
  
  USERNAME_FIELD = 'unique_id'


class Post(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True, null=False, unique=True)
  userName = models.CharField(verbose_name='user_name', db_column='user_name', max_length=255, default='')
  profileImage = models.CharField(verbose_name='profile_image', db_column='profile_image', max_length=255, null=True)
  content = models.TextField(default='', null=False)
  writeTime = models.DateField(default=timezone.now())

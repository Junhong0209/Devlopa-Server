from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import *
from .services.returnStatusForm import *
from .services.returnPostingObject import *

import requests
import os


@method_decorator(csrf_exempt, name='dispatch')
class DAuthUrl(APIView):
  def get(self, request):
    try:
      DAUTH_ID = os.environ.get('DAUTH_ID')
      REDIRECT_URL = os.environ.get('REDIRECT_URL')
    except TypeError:
      return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=CUSTOM_CODE(status=500, message='값을 가져오는 도중 문제가 생겼습니다.'))
    
    url = f'http://dauth.b1nd.com/login?client_id={DAUTH_ID}&redirect_uri={REDIRECT_URL}'
    
    data = {
      'DAuthURL': url
    }
    
    return Response(status=status.HTTP_200_OK, data=OK_200(data=data))


@method_decorator(csrf_exempt, name='dispatch')
class GetDodamUser(APIView):
  def post(self, request):
    try:
      code = request.data['code']
      DAUTH_ID = os.environ.get('DAUTH_ID')
      DAUTH_SECRET = os.environ.get('DAUTH_SECRET')
    except (KeyError, ValueError, TypeError):
      if TypeError:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=CUSTOM_CODE(status=500, message='값을 가져오는 도중 문제가 생겼습니다.'))
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(message='Some value is missing.'))

    body = {
      'code': code,
      'client_id': DAUTH_ID,
      'client_secret': DAUTH_SECRET
    }
    
    try:
      response = requests.post(os.environ.get('DODAM_TOKEN_API'), data=body)
      dodam_token = response.json()['access_token']
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=CUSTOM_CODE(status=400, message='도담 서버 토큰을 가져오지 못했습니다.'))

    header = {
      'Authorization': 'Bearer ' + dodam_token
    }
    
    try:
      response = requests.get(os.environ.get('DODAM_USER_API'), headers=header)
      user_data = response.json()['data']
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=CUSTOM_CODE(status=400, message='Some Values missing'))
    
    try:
      userModel = User.object.get(unique_id=user_data['uniqueId'])
    except ObjectDoesNotExist:
      userModel = User.object.create_user(
        username=user_data['name'],
        unique_id=user_data['uniqueId'],
        grade=user_data['grade'],
        room=user_data['room'],
        number=user_data['number'],
        profile_image=user_data['profileImage']
      )
      userModel.save()
    
    try:
      token = Token.objects.create(user=userModel)
    except IntegrityError:
      token = Token.objects.get(user=userModel)
    
    return Response(status=status.HTTP_200_OK, data=OK_200(message='도담의 유저 정보를 성공적으로 불러와 저장했습니다.', data={'token': token.key}))


@method_decorator(csrf_exempt, name='dispatch')
class UserPosting(APIView):
  def post(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(status=status.HTTP_401_UNAUTHORIZED, data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.'))

    try:
      content = request.data['content']
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(message='Some value is missing.'))

    posting = Post(
      user_id=request.user,
      userName=request.user.username,
      profileImage=request.user.profile_image,
      content=content
    )
    posting.save()
    
    return Response(status=status.HTTP_200_OK, data=OK_200(message='글이 성공적으로 저장되었습니다.'))
  
  def get(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(status=status.HTTP_401_UNAUTHORIZED, data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.'))

    try:
      posting_objects = Post.objects.all()
      data = PostingObject(posting_objects)
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(message='Some Value is missing.'))
      
    return Response(status=status.HTTP_200_OK, data=OK_200(message='전체 글 조회를 성공했습니다.', data=data))
  
  def put(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(status=status.HTTP_401_UNAUTHORIZED, data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.'))
    
    content = request.data['content']
    Post.content = content
    Post.save()
    
    return Response(status=status.HTTP_200_OK, data=OK_200(message='글이 성공적으로 수정되었습니다.'))


@method_decorator(csrf_exempt, name='dispatch')
class UserProfile(APIView):
  def get(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(status=status.HTTP_401_UNAUTHORIZED, data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.'))
    
    user_profile = {
      'profile_image': request.user.profile_image,
      'user_name': request.user.username,
      'grade': request.user.grade,
      'room': request.user.room,
      'number': request.user.number
    }
    
    posting_objects = Post.objects.filter(user_id=request.user)
    post_data = PostingObject(posting_objects)
    post_data['user_profile'] = user_profile
    
    return Response(status=status.HTTP_200_OK, data=OK_200(message='유저 프로필 조회를 성공했습니다.', data=post_data))

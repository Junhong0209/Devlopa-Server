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

import requests
import my_settings


@method_decorator(csrf_exempt, name='dispatch')
class DAuthUrl(APIView):
  def get(self, request):
    try:
      url = f'http://dauth.b1nd.com/login?client_id={my_settings.DAUTH_ID}&redirect_uri={my_settings.REDIRECT_URL}'
      
      data = {
        'DAuthURL': url
      }
    except:
      return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(data={"Something Error."}))
    
    return Response(status=status.HTTP_200_OK, data=OK_200(data=data))


@method_decorator(csrf_exempt, name='dispatch')
class GetDodamUser(APIView):
  def post(self, request):
    try:
      body = {
        'code': request.data['code'],
        'client_id': my_settings.DAUTH_ID,
        'client_secret': my_settings.DAUTH_SECRET
      }
    except (KeyError, ValueError, TypeError):
      if TypeError:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=CUSTOM_CODE(status=500, data={}, message='값을 가져오는 도중 문제가 생겼습니다.'))
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(message='Body에 값이 잘못 입력되었습니다.'))
    
    try:
      response = requests.post(my_settings.DODAM_TOKEN_API, data=body)
      dodam_token = response.json()['access_token']
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=CUSTOM_CODE(status=400, message='도담 서버 토큰을 가져오지 못했습니다.'))
    
    try:
      header = {
        'Authorization': 'Bearer ' + dodam_token
      }
      response = requests.get(my_settings.DODAM_USER_API, headers=header)
      user_data = response.json()['data']
    except (KeyError, ValueError):
      return Response(status=status.HTTP_400_BAD_REQUEST, data=CUSTOM_CODE(status=400, message='Some Values missing'))
    
    try:
      userModel = User.object.get(unique_id=user_data['uniqueId'])
      print(userModel)
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

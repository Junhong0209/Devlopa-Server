from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from .services.returnStatusForm import *

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
      data = {
        'code': request.data['code']
      }
    except (KeyError, ValueError, TypeError):
      if TypeError:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=CUSTOM_CODE(status=500, data={}, message='값을 가져오는 도중 문제가 생겼습니다.'))
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=BAD_REQUEST_400(message='Body에 아무것도 입력하지 않았습니다.'))
    
    return Response(status=status.HTTP_200_OK, data=OK_200(message='도담의 유저 정보를 성공적으로 불러와 저장했습니다.'))

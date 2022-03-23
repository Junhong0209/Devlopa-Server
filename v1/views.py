from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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
      return JsonResponse(BAD_REQUEST_400(data={"Something Error."}))
    
    return JsonResponse(OK_200(data=data))

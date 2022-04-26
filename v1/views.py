from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import *
from .services.returnStatusForm import *
from .services.returnPostingObject import *
from .services.returnCommentObject import *

import requests
import os


@method_decorator(csrf_exempt, name='dispatch')
class DAuthUrl(APIView):
  def get(self, request):
    try:
      DAUTH_ID = os.environ.get('DAUTH_ID')
      REDIRECT_URL = os.environ.get('REDIRECT_URL')
    except TypeError:
      return Response(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        data=CUSTOM_CODE(status=500, message='값을 가져오는 도중 문제가 생겼습니다.')
      )
    
    url = f'http://dauth.b1nd.com/login?client_id={DAUTH_ID}&redirect_uri={REDIRECT_URL}'
    
    data = {
      'DAuthURL': url
    }
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='성공적으로 DAuth Login URL을 가져왔습니다.', data=data)
    )


@method_decorator(csrf_exempt, name='dispatch')
class GetDodamUser(APIView):
  def post(self, request):
    try:
      code = request.data['code']
      DAUTH_ID = os.environ.get('DAUTH_ID')
      DAUTH_SECRET = os.environ.get('DAUTH_SECRET')
    except (KeyError, ValueError, TypeError):
      if TypeError:
        return Response(
          status=status.HTTP_500_INTERNAL_SERVER_ERROR,
          data=CUSTOM_CODE(
            status=500, message='값을 가져오는 도중 문제가 생겼습니다.')
        )
      else:
        return Response(
          status=status.HTTP_400_BAD_REQUEST,
          data=BAD_REQUEST_400(message='Some Values are missing.')
        )
    
    body = {
      'code': code,
      'client_id': DAUTH_ID,
      'client_secret': DAUTH_SECRET
    }
    
    try:
      response = requests.post(
        os.environ.get('DODAM_TOKEN_API'), data=body)
      dodam_token = response.json()['access_token']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=CUSTOM_CODE(status=400, message='도담 서버 토큰을 가져오지 못했습니다.')
      )
    
    header = {
      'Authorization': 'Bearer ' + dodam_token
    }
    
    try:
      response = requests.get(os.environ.get(
        'DODAM_USER_API'), headers=header)
      user_data = response.json()['data']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=CUSTOM_CODE(
          status=400, message='Some Values are missing.')
      )
    
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
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='도담의 유저 정보를 성공적으로 불러와 저장했습니다.',
                  data={'token': token.key})
    )


@method_decorator(csrf_exempt, name='dispatch')
class UserPosting(APIView):
  def post(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      content = request.data['content']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='Some Values are missing.')
      )
    
    if content.isspace():
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='공백만 입력되었습니다. 문자를 입력해주세요.')
      )
    
    posting = Post(
      user_id=request.user,
      userName=request.user.username,
      profileImage=request.user.profile_image,
      content=content
    )
    posting.save()
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='글이 성공적으로 저장되었습니다.')
    )
  
  def get(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      posting_objects = Post.objects.all()
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='Some Values are missing.')
      )
    
    user_profile = {
      'profile_image': request.user.profile_image,
      'user_name': request.user.username,
      'grade': request.user.grade,
      'room': request.user.room,
      'number': request.user.number
    }
    
    data = PostingObject(posting_objects)
    data['user_profile'] = user_profile
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='전체 글 조회를 성공했습니다.', data=data)
    )
  
  def put(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      content = request.data['content']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='Some Values are missing.')
      )
    
    Post.content = content
    Post.save()
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='글이 성공적으로 수정되었습니다.')
    )
  
  def delete(self, request):
    if not request.user.is_authenticatend or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      post_id = request.data['post_idx']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='게시글 idx가 존재하지 않습니다.')
      )
    
    try:
      post_data = Post.objects.get(primaryKey=post_id)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='존재하지 않는 댓글입니다.')
      )
    
    if post_data.user.unique_id == request.user:
      post_data.delete()
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='게시글이 성공적으로 삭제되었습니다.')
      )
    else:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='사용자의 게시글이 아닙니다.')
      )


@method_decorator(csrf_exempt, name='dispatch')
class UserProfile(APIView):
  def get(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    user_profile = {
      'profile_image': request.user.profile_image,
      'user_name': request.user.username,
      'grade': request.user.grade,
      'room': request.user.room,
      'number': request.user.number
    }
    
    try:
      posting_objects = Post.objects.filter(user_id=request.user)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='유저 데이터가 존재하지 않습니다.')
      )
    
    post_data = PostingObject(posting_objects)
    post_data['user_profile'] = user_profile
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='유저 프로필 조회를 성공했습니다.', data=post_data)
    )


@method_decorator(csrf_exempt, name='dispatch')
class PostComment(APIView):
  def post(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      post_idx = request.data['post_idx']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='게시글 idx가 존재 하지 않습니다.')
      )
    
    try:
      comment_data = request.data['comment']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='댓글이 작성 되지 않았습니다.')
      )
    
    comment = Comment(
      post_id=post_idx,
      comment=comment_data,
    )
    comment.save()
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='댓글이 성공적으로 작성되었습니다.')
    )
  
  def get(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      post_idx = request.GET['post_idx']
    except MultiValueDictKeyError:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='params에 게시글 idx가 존재 하지 않습니다.')
      )
    
    try:
      comment_objects = Comment.objects.filter(post_id=post_idx)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='게시글의 댓글이 존재하지 않습니다.')
      )
    
    comment_data = CommentObject(comment_objects)
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='댓글을 성공적으로 불러왔습니다.', data=comment_data)
    )
  
  def put(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      comment_idx = request.data['comment_idx']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='댓글 idx가 존재하지 않습니다.')
      )
    
    try:
      comment = request.data['comment']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='게시글 idx가 존재하지 않습니다.')
      )
    
    try:
      comment_data = Comment.objects.filter(primary_key=comment_idx)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='존재하지 않는 게시글입니다.')
      )
    
    if comment_data.user.unique_id == request.user:
      comment_data['comment'] = comment
      comment_data.save()
      
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='댓글이 성공적으로 수정되었습니다.')
      )
    else:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='사용자의 게시글이 아닙니다.')
      )
  
  def delete(self, request):
    if not request.user.is_authenticated or request.user.is_anonymous:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      comment_id = request.data['comment_idx']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='댓글 idx가 존재하지 않습니다.')
      )
    
    try:
      comment_data = Comment.objects.get(primary_key=comment_id)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='존재하지 않는 댓글입니다.')
      )
    
    if comment_data.user.unique_id == request.user:
      comment_data.delete()
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='댓글이 성공적으로 삭제되었습니다.')
      )
    else:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='사용자의 댓글이 아닙니다.')
      )

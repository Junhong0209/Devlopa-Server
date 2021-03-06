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
from .services.getDodamToken import *
from .services.getDodamUser import *

import asyncio
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
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='code가 존재하지 않습니다.')
      )

    loop = asyncio.new_event_loop()
    
    body = {
      'code': code,
      'client_id': DAUTH_ID,
      'client_secret': DAUTH_SECRET
    }
    
    try:
      dodam_token = loop.run_until_complete(get_dodam_token(body=body))
      token = dodam_token['access_token']
    except (KeyError, ValueError, TypeError):
      if TypeError:
        return Response(
          status=status.HTTP_403_FORBIDDEN,
          data=CUSTOM_CODE(status=403, message='위조된 코드입니다.')
        )
      else:
        return Response(
          status=status.HTTP_400_BAD_REQUEST,
          data=CUSTOM_CODE(status=400, message='도담 서버 토큰을 가져오지 못했습니다.')
        )
    
    header = {
      'Authorization': 'Bearer ' + token
    }

    try:
      user_data = loop.run_until_complete(get_dodam_user(header=header))
      user_data = user_data['data']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='Some Values are missing.')
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
      data=OK_200(message='도담의 유저 정보를 성공적으로 불러와 저장했습니다.', data={'token': token.key})
    )


@method_decorator(csrf_exempt, name='dispatch')
class UserPosting(APIView):
  def post(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      if request.GET['post_idx']:
        try:
          posting_object = Post.objects.get(primaryKey=request.GET['post_idx'], user_id=request.user)

          data = {
            'contents': {
              'idx': posting_object.primaryKey,
              'user_name': posting_object.user.username,
              'profile_image': posting_object.user.profile_image,
              'grade': posting_object.user.grade,
              'room': posting_object.user.room,
              'number': posting_object.user.number,
              'content': posting_object.content,
              'write_time': posting_object.writeTime.strftime('%Y-%m%d %H:%M:%S')
            }
          }

          return Response(
            status=status.HTTP_200_OK,
            data=OK_200(message='게시글 조회를 성공했습니다.', data=data)
          )
        except (KeyError, ValueError):
          return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=BAD_REQUEST_400(message='Some Values are missing.')
          )
        
    except MultiValueDictKeyError:
      try:
        posting_objects = Post.objects.all()
        
        user_profile = {
          'profile_image': request.user.profile_image,
          'user_name': request.user.username,
          'grade': request.user.grade,
          'room': request.user.room,
          'number': request.user.number
        }
        
        data = {'user_profile': {}, 'list_count': 0, 'comment_count': 0, 'contents': []}
        posting_objects = list(posting_objects.order_by('-writeTime'))

        data['user_profile'] = user_profile
        
        for posting_object in posting_objects:
          comments_objects = Comment.objects.filter(post_id=posting_object.primaryKey)
          comments_objects = list(comments_objects)
          if posting_object.user_id == request.user.unique_id:
            posting_data = {
              'idx': posting_object.primaryKey,
              'user_name': posting_object.user.username,
              'profile_image': posting_object.user.profile_image,
              'grade': posting_object.user.grade,
              'room': posting_object.user.room,
              'number': posting_object.user.number,
              'my_post': True,
              'content': posting_object.content,
              'write_time': posting_object.writeTime.strftime('%Y-%m-%d %H:%M:%S'),
              'comment': [],
              'comment_count': 0
            }
            for comments_object in comments_objects:
              comment_data = {
                'idx': comments_object.primary_key,
                'user_name': comments_object.user.username,
                'content': comments_object.comment,
                'my_comment': True
              }
              posting_data['comment_count'] += 1
              posting_data['comment'].append(comment_data)
          else:
            posting_data = {
              'idx': posting_object.primaryKey,
              'user_name': posting_object.user.username,
              'profile_image': posting_object.user.profile_image,
              'grade': posting_object.user.grade,
              'room': posting_object.user.room,
              'number': posting_object.user.number,
              'my_post': False,
              'content': posting_object.content,
              'write_time': posting_object.writeTime.strftime('%Y-%m-%d %H:%M:%S'),
              'comment': [],
              'comment_count': 0
            }
            for comments_object in comments_objects:
              comment_data = {
                'idx': comments_object.primary_key,
                'user_name': comments_object.user.username,
                'content': comments_object.comment,
                'my_comment': False
              }
              posting_data['comment_count'] += 1
              posting_data['comment'].append(comment_data)
          data['list_count'] += 1
          data['contents'].append(posting_data)
  
        return Response(
          status=status.HTTP_200_OK,
          data=OK_200(message='전체 글 조회를 성공했습니다.', data=data)
        )
      except (KeyError, ValueError):
        return Response(
          status=status.HTTP_400_BAD_REQUEST,
          data=BAD_REQUEST_400(message='Some Values are missing.')
        )
  
  def put(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      post_data = Post.objects.get(primaryKey=request.data['post_idx'])
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='존재하지 않는 게시글입니다.')
      )
    
    try:
      content = request.data['content']
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='Some Values are missing.')
      )
    
    if post_data.user.unique_id == request.user.unique_id:
      post_data.content = content
      post_data.save()
  
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='게시글이 성공적으로 수정되었습니다.')
      )
    else:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='사용자의 게시글이 아닙니다.')
      )
  
  def delete(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
      post_data = Post.objects.get(primaryKey=post_id, user_id=request.user)
      post_data.delete()
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='게시글이 성공적으로 삭제되었습니다.')
      )
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='본인의 게시글이 아닙니다.')
      )


@method_decorator(csrf_exempt, name='dispatch')
class UserProfile(APIView):
  def get(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
      
      data = {'user_profile': {}, 'list_count': 0, 'contents': []}
      
      posting_objects = list(posting_objects.order_by('-writeTime'))
      for posting_object in posting_objects:
        comments_objects = Comment.objects.filter(post_id=posting_object.primaryKey)
        comments_objects = list(comments_objects)
        posting_data = {
          'idx': posting_object.primaryKey,
          'user_name': posting_object.user.username,
          'profile_image': posting_object.user.profile_image,
          'grade': posting_object.user.grade,
          'room': posting_object.user.room,
          'number': posting_object.user.number,
          'my_post': True,
          'content': posting_object.content,
          'write_time': posting_object.writeTime.strftime('%Y-%m-%d %H:%M:%S'),
          'comment': [],
          'comment_count': 0
        }
        for comments_object in comments_objects:
          comment_data = {
            'idx': comments_object.primary_key,
            'user_name': comments_object.user.username,
            'content': comments_object.comment,
            'my_comment': False
          }
          posting_data['comment_count'] += 1
          posting_data['comment'].append(comment_data)
        data['list_count'] += 1
        data['contents'].append(posting_data)
      data['user_profile'] = user_profile
      
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='유저 프로필 조회를 성공했습니다.', data=data)
      )
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='유저 데이터가 존재하지 않습니다.')
      )


@method_decorator(csrf_exempt, name='dispatch')
class PostComment(APIView):
  def post(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
    
      comment = Comment(
        post_id=post_idx,
        comment=comment_data,
        user_id=request.user
      )
      comment.save()
      
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='댓글이 성공적으로 작성되었습니다.')
      )
    except (KeyError, ValueError):
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='댓글이 작성 되지 않았습니다.')
      )
  
  def get(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
      )
    
    try:
      post_idx = request.GET['post_idx']
    except MultiValueDictKeyError:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='params에 게시글 idx가 존재하지 않습니다.')
      )
    
    comment_objects = Comment.objects.filter(post_id=post_idx)

    data = {'list_count': 0, 'contents': []}

    comment_objects = comment_objects.order_by('write_time')
    comment_objects = list(comment_objects)
    for comment_object in comment_objects:
      if comment_object.user_id == request.user.unique_id:
        comment_data = {
          'idx': comment_object.primary_key,
          'user_name': comment_object.user.username,
          'my_comment': True,
          'content': comment_object.comment,
        }
      else:
        comment_data = {
          'idx': comment_object.primary_key,
          'user_name': comment_object.user.username,
          'my_comment': False,
          'content': comment_object.comment,
        }
      data['list_count'] += 1
      data['contents'].append(comment_data)
    
    if data['list_count'] != 0:
      return Response(
          status=status.HTTP_200_OK,
          data=OK_200(message='댓글을 성공적으로 불러왔습니다.', data=data)
        )
    else:
      return Response(
        status=status.HTTP_200_OK,
        data=OK_200(message='게시글의 댓글이 존재하지 않습니다.', data=data)
      )
  
  def put(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
        data=BAD_REQUEST_400(message='댓글 idx가 존재하지 않습니다.')
      )
    
    try:
      comment_data = Comment.objects.filter(primary_key=comment_idx)
    except ObjectDoesNotExist:
      return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data=BAD_REQUEST_400(message='존재하지 않는 게시글입니다.')
      )
    
    if comment_data.user.unique_id == request.user.unique_id:
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
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 존재하지 않습니다.')
        )
    except AttributeError:
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
    
    if comment_data.user.unique_id == request.user.unique_id:
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


@method_decorator(csrf_exempt, name='dispatch')
class CheckAuth(APIView):
  def get(self, request):
    try:
      if not request.user.is_authenticated or request.user.is_anonymous:
        data = {
          'verify_token': False
        }
        
        return Response(
          status=status.HTTP_401_UNAUTHORIZED,
          data=INVALID_TOKEN(message='토큰이 없거나 위조된 토큰입니다.', data=data)
        )
    except AttributeError:
      data = {
        'verify_token': False
      }
      
      return Response(
        status=status.HTTP_401_UNAUTHORIZED,
        data=INVALID_TOKEN(message='토큰이 없거나 위조된 토큰입니다.', data=data)
      )
    
    data = {
      'verify_token': True
    }
    
    return Response(
      status=status.HTTP_200_OK,
      data=OK_200(message='토큰 확인이 완료되었습니다.', data=data)
    )
  
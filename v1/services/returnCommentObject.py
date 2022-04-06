def CommentObject(value):
  data = {'list_count': 0, 'contents': []}
  
  comment_objects = value.order_by('writeTime')
  comment_objects = list(comment_objects)
  for comment_object in comment_objects:
    comment_data = {
      'idx': comment_object.primary_key,
      'user_name': comment_object.user.username,
      'profile_image': comment_object.user.profile_image,
      'content': comment_object.comment,
      'write_time': comment_object.write_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    data['list_count'] += 1
    data['contents'].append(comment_data)
  
  return data

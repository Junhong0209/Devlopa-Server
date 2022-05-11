def CommentObject(value):
  data = {'list_count': 0, 'contents': []}
  
  comment_objects = value.order_by('write_time')
  comment_objects = list(comment_objects)
  for comment_object in comment_objects:
    comment_data = {
      'idx': comment_object.primary_key,
      'user_name': comment_object.user.username,
      'content': comment_object.comment,
    }
    data['list_count'] += 1
    data['contents'].append(comment_data)
  
  return data

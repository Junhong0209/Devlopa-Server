def PostingObject(value):
  data = {'user_profile': {}, 'list_count': 0, 'contents': []}

  posting_objects = value.order_by('-writeTime')
  posting_objects = list(posting_objects)
  for posting_object in posting_objects:
    posting_data = {
      'idx': posting_object.primaryKey,
      'user_name': posting_object.user.username,
      'profile_image': posting_object.user.profile_image,
      'grade': posting_object.user.grade,
      'room': posting_object.user.room,
      'number': posting_object.user.number,
      'content': posting_object.content,
      'write_time': posting_object.writeTime.strftime('%Y-%m-%d %H:%M:%S')
    }
    data['list_count'] += 1
    data['contents'].append(posting_data)
    
  return data
  
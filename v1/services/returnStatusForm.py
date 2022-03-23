def CUSTOM_CODE(status=200, data={}, message='message'):
  STATUS_FORM = {
    'status': status,
    'detail': message,
    'data': data
  }
  return STATUS_FORM


def OK_200(data={}):
  return CUSTOM_CODE(status=200, message='Success', data=data)


def BAD_REQUEST_400(data={}, message='Bad Request'):
  return CUSTOM_CODE(status=400, message=message, data=data)


def INVALID_TOKEN(data={}, message='Invalid token.'):
  return CUSTOM_CODE(status=401, message=message, data=data)

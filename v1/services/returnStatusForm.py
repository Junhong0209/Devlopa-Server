def CUSTOM_CODE(status=200, data={}, message='message'):
  STATUS_FORM = {
    'status': status,
    'detail': message,
    'data': data
  }
  return STATUS_FORM


def OK_200(message='Success', data={}):
  return CUSTOM_CODE(status=200, message=message, data=data)


def BAD_REQUEST_400(message='Bad Request', data={}):
  return CUSTOM_CODE(status=400, message=message, data=data)


def INVALID_TOKEN(message='Invalid token.', data={}):
  return CUSTOM_CODE(status=401, message=message, data=data)

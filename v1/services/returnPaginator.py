from django.core.paginator import Paginator


def return_pagiantor(objects, page):
  objects = objects.order_by('-writeTime')
  paginator = Paginator(objects, 10, allow_empty_first_page=True)
  contents = paginator.get_page(page)
  
  all_page_list = paginator.page_range
  alpha = beta = 0
  
  if page - 2 <= 0:
    alpha = 3 - page
  elif page + 2 > len(all_page_list):
    beta = 2 + page - len(all_page_list)
  
  page_list = all_page_list[max((page - 1) - 2 - beta, 0): min((page - 1) + 3 + alpha, len(all_page_list))]
  
  context = {
    'contents': contents,
    'page_list': page_list
  }
  
  return context['contents']

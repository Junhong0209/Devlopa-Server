import os
import aiohttp


async def get_dodam_token(body):
  async with aiohttp.ClientSession() as sess:
    async with sess.post(os.environ.get('DODAM_TOKEN_API'), data=body) as res:
      return await res.json()

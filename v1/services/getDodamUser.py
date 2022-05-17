import os
import aiohttp


async def get_dodam_user(header):
  async with aiohttp.ClientSession() as sess:
    async with sess.get(os.environ.get('DODAM_USER_API'), headers=header) as res:
      return await res.json()

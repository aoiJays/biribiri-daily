# https://doc.justoneapi.com/
import os
SOURCE_URL = 'https://api.justoneapi.com'
API_TOKEN = os.getenv('JUSTONE_API_TOKEN', None)

if API_TOKEN is None:
    raise ValueError("API token not found in environment variables.")


ZHIHU_LIST = [
    {
        "title": "AI早报",
        "column_id": "c_1885342192987509163",
        "KEY_WORD": "AI 早报",
        "CATEGORY": "AI资讯",
    },
    {
        "title": "显卡日报",
        "column_id": "c_1433942042578157568",
        "KEY_WORD": "显卡日报",
        "CATEGORY": "硬件",
    }
]


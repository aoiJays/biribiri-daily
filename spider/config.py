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

WECHAT_LIST = [
    {   
        "title": "5E",
        "wxid": "cn5eplay",
        "KEY_WORD": ["CS晚报"], 
        "CATEGORY": "CS"
    },
    {   
        "title": "动感光波发射基地",
        "wxid": "gh_1a3b4a5c4888",
        "KEY_WORD": ["每日动漫资讯"], 
        "CATEGORY": "动漫"
    },
    {   
        "title": "科技荐闻",
        "wxid": "ITechNews",
        "KEY_WORD": ["世界早报", "商业早报", "美国早报", "科技早报", "科学早报", "体育早报"],
        "CATEGORY": "新闻",
    },
    {
        "title": "一个普通的F1粉丝",
        "wxid": "formula-one-Box",
        "KEY_WORD": "F1新闻晨报", 
        "CATEGORY": "F1"
    }
]

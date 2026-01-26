import os
from openai import OpenAI

def llm_conclude(data: str) -> str:

    PROMPT = f'''**角色**：你是一位专业、中立的新闻编辑，擅长提炼核心信息，并确保事实准确、逻辑清晰。

**任务**：请根据用户提供的新闻段落，生成一个简洁、客观、吸引人的**新闻标题**。

**要求**：
1.  **核心聚焦**：标题必须反映新闻最核心的事件或结论，抓住**5W1H**（何事、何人、何地等）中的最关键要素。
2.  **客观吸引**：基于提供的文本概括，确保事实准确、不添加未提及信息或个人观点，同时力求简洁有力、吸引读者注意。
3.  **格式规范**：标题应为**一句话**，长度适中（建议中文在15-25字之间），除非核心信息必须，否则一般不使用标点结尾。
4.  **保留关键信息**：如涉及重要组织、人物、突破性数字、关键决策或地点，应优先在标题中体现。

**输出格式**：
请直接输出新闻标题，无需添加任何前缀、引号或额外说明。

---
**用户输入**：
{data}

---
你的输出：
'''

    for i in range(3):
        try:

            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY")

            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1"),
            )

            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": PROMPT}],
                temperature=0.1,
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[retry {i}/3]调用 LLM 出错: {e}")
            if i == 2: return f"调用 LLM 出错: {e}"


def conclude_title(data: dict) -> dict:
    try:
        reply = {
            'category': data['category'],
            'title': llm_conclude(data['content']),
            'content': data['content']
        }
        return reply
    except Exception as e:
        print(f"生成标题出错: {e}")
        return {
            'category': None,
            'title': None,
            'content': None,
        }
    

if __name__ == "__main__":

    from split import split_news
    data = split_news('output/md/新闻_wechat_2026-01-20 美国早报.md')

    for i in data:
        print(i['content'])
        print('-----')
        print(conclude_title(i)['title'])
        print('===================')
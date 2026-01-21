import time
import os
from openai import OpenAI
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

debug = False

def fetch_recent_news_within_24h():
    # 1. 初始化浏览器配置
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 如果不想看到浏览器界面，可以取消注释这行
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 自动下载并设置 ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "https://sports.yahoo.co.jp/list/news/npb?genre=npb"
        print(f"正在打开网页: {url}")
        driver.get(url)

        # 定义时间阈值：当前时间 - 1天
        # 注意：实际运行时使用的是你电脑的系统时间。
        # 如果网页上的新闻时间是未来的（如示例中的2026年），这里的逻辑可能需要根据实际情况调整。
        current_time = datetime.now()
        time_threshold = current_time - timedelta(days=1)
        print(f"当前时间: {current_time.strftime('%Y/%m/%d %H:%M')}")
        print(f"截取时间阈值 (24小时前): {time_threshold.strftime('%Y/%m/%d %H:%M')}")

        wait = WebDriverWait(driver, 10)
        
        # ---------------------------------------------------------
        # 2. 循环点击“更多”按钮，并检查时间
        # ---------------------------------------------------------
        click_count = 0
        stop_loading = False

        while not stop_loading:
            try:
                # 获取当前页面上所有可见的时间元素
                # 我们只需要检查最后一个（最旧的）文章时间即可判断是否越界
                time_elements = driver.find_elements(By.CLASS_NAME, "cm-timeLine__itemTime")
                
                if time_elements:
                    last_time_str = time_elements[-1].text.strip()
                    try:
                        # 解析时间字符串，格式示例: 2026/1/21 21:29
                        article_time = datetime.strptime(last_time_str, "%Y/%m/%d %H:%M")
                        
                        # 检查是否超过1天
                        if article_time < time_threshold:
                            print(f"检测到文章时间 [{last_time_str}] 早于阈值，停止加载。")
                            stop_loading = True
                            break
                    except ValueError:
                        print(f"时间格式解析失败: {last_time_str}，跳过检查继续加载...")

                if click_count > 30:
                    print("点击次数超过25次，停止加载以防无限循环。")
                    break
                
                # 尝试点击“更多”按钮
                more_button = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, "moreViewButton"))
                )
                
                if not more_button.is_displayed():
                    print("没有更多按钮了，加载结束。")
                    break
                
                # 使用 JS 点击
                driver.execute_script("arguments[0].click();", more_button)
                click_count += 1
                print(f"第 {click_count} 次点击加载更多... (当前最旧文章: {last_time_str if time_elements else 'N/A'})")
                
                time.sleep(1.5) # 等待加载

            except Exception as e:
                print("未找到更多按钮或加载中断，停止循环。")
                break

        # ---------------------------------------------------------
        # 3. 解析最终页面数据并过滤
        # ---------------------------------------------------------
        print("-" * 30)
        print("开始提取并过滤数据...")
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        articles = soup.find_all("a", class_="cm-timeLine__itemArticleLink")

        results = []
        
        for article in articles:
            # 获取时间
            time_tag = article.find("time", class_="cm-timeLine__itemTime")
            date_str = time_tag.text.strip() if time_tag else ""
            
            # 二次过滤：确保提取到列表里的数据确实都在24小时内
            is_valid = False
            if date_str:
                try:
                    article_dt = datetime.strptime(date_str, "%Y/%m/%d %H:%M")
                    if article_dt >= time_threshold:
                        is_valid = True
                except ValueError:
                    pass
            
            if is_valid:
                title_tag = article.find("p", class_="cm-timeLine__itemTitle")
                title = title_tag.text.strip() if title_tag else "无标题"
                link = article.get("href")

                results.append({
                    "title": title,
                    "url": link,
                    "date": date_str
                })
                # print(f"[{date_str}] {title}")
                # print(f"URL: {link}")
                # print("-" * 20)

        print(f"\n共获取到 {len(results)} 篇 24小时内 的文章。")
        return results

    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        driver.quit()

def llm_rewrite(results):

    news_txt = ''.join([f"{result['title']}\n" for result in results])
    PROMPT = f"""# Role
你是一位拥有20年经验的资深棒球媒体主编。你的特长是从杂乱的海量资讯中提炼核心看点，并用生动、幽默且专业的中文撰写“每日棒球情报日报”。你的受众是深度棒球爱好者，他们希望在2分钟内掌握今日全球棒球圈（主要是NPB，其次是MLB）的所有动态。

# Task
请阅读我提供的【原始新闻列表】，按照下述要求生成一份《今日棒球情报日报》。

# Input Data
---
{news_txt}
---
# Workflow
1. 分析与去重：阅读所有新闻标题，去除重复内容，合并同一事件的不同报道。
2. 分类整理：将新闻归类到指定的五个板块（见Output Structure）。
3. 内容重写：不要仅仅翻译或罗列标题。要将同一球队或同一事件的新闻整合成流畅的段落，提炼出最有趣的点。
4. 格式美化：使用Markdown格式、Emoji表情和加粗字体来增强可读性。

# Output Structure (必须严格遵守的板块结构)
---
## ⚾️ 今日棒球情报日报 
### 🚨 【头条重磅：[副标题]】
   - 筛选出当天影响力最大、最令人震惊的3-4条新闻。

### 🇯🇵 【NPB 12球团动态：[副标题]】
    - 只有原标题中明确出现了球队名称的新闻，才归入此板块。不能出现遗漏
    - *注意：将同一支球队的新闻合并在一起写，不要散落在各处。*
    - 球队内部的新闻需要使用无序标题进行分点描述。
    - 可以使用类似“坏消息：”、“新星：”这样的小标签来引导阅读。
#### 中央联盟 (Central League)
##### 阪神
##### 横滨
##### 巨人
##### 养乐多
##### 中日
##### 广岛
#### 太平洋联盟 (Pacific League)
##### 火腿
##### 软银
##### 欧力士
##### 乐天
##### 西武
##### 罗德

### 🇺🇸 【MLB与海外：[副标题]】
   - 涉及MLB、小联盟、独立联盟或海外挑战选手的动态。

### 动态板块1
    - 可以由你自由添加2-4个，与以上板块彼此层级平行，内容不相交），格式需要与前文相同
    - 通常用于软性内容，如：场外花絮、选手私生活、粉丝服务、趣闻等。
    - 需要重点点出具体的人名，此处不需要强调队伍名称，防止出错。
    - 确保所有未出现在上文的新闻都被涵盖在内。
### 动态板块2
...

### 动态板块n
...

--- 

# Style & Tone Guidelines
- 语言风格：统一使用中文，推荐使用棒球圈用语，不要出现日语。
- 语气：生动有趣，像是一个懂球的朋友在给你讲故事，而不是冷冰冰的机器播报。
- 排版要求：
  - 核心人名、球队名、关键数据（如20轰、离谱）需要加粗。
  - 每个大板块下使用无序列表（*）。
- Emoji使用：适当使用Emoji来增强情感表达，但不要过度堆砌，保持专业感。
- 只用规范的Markdown语法输出结果，不要输出任何多余的说明文字

# Output
"""


    try:

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY")

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1"),
        )

        resp = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": PROMPT}],
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"调用 LLM 出错: {e}")
        return ""
    

if __name__ == "__main__":

    
    if debug == True:
        with open('baseball_news_24h.json', 'r', encoding='utf-8') as f:
            import json
            results = json.load(f)
    else:
        results = fetch_recent_news_within_24h()

    # format_results = llm_rewrite(results)

    # with open('output/md/baseball_news_report.md', 'w', encoding='utf-8') as f:
    #     f.write(format_results)


import os
import openai
import glob
import shutil

import numpy as np
import pandas as pd

import json
import io
import inspect
import requests
import re
import random
import string
import base64

from bs4 import BeautifulSoup
import dateutil.parser as parser
import tiktoken
from lxml import etree

import sys
from dotenv import load_dotenv
from openai import OpenAI

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

load_dotenv()
python_inter_args = '{"py_code": "import numpy as np\\narr = np.array([1, 2, 3, 4])\\nsum_arr = np.sum(arr)\\nsum_arr"}'

# 工具定义
python_inter_tool = {
    "type": "function",
    "function": {
        "name": "python_inter",
        "description": f"当用户需要编写Python程序并执行时，请调用该函数。该函数可以执行一段Python代码并返回最终结果，需要注意，本函数只能执行非绘图类的代码，若是绘图相关代码，则需要调用fig_inter函数运行。\n同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，例如如以下形式字符串就是合规字符串：{python_inter_args}",
        "parameters": {
            "type": "object",
            "properties": {
                "py_code": {
                    "type": "string",
                    "description": "The Python code to execute."
                },
                "g": {
                    "type": "string",
                    "description": "Global environment variables, default to globals().",
                    "default": "globals()"
                }
            },
            "required": ["py_code"]
        }
    }
} 

fig_inter_tool = {
    "type": "function",
    "function": {
        "name": "fig_inter",
        "description": (
            "当用户需要使用 Python 进行可视化绘图任务时，请调用该函数。"
            "该函数会执行用户提供的 Python 绘图代码，并自动将生成的图像对象保存为图片文件并展示。\n\n"
            "调用该函数时，请传入以下参数：\n\n"
            "1. `py_code`: 一个字符串形式的 Python 绘图代码，**必须是完整、可独立运行的脚本**，"
            "代码必须创建并返回一个命名为 `fname` 的 matplotlib 图像对象；\n"
            "2. `fname`: 图像对象的变量名（字符串形式），例如 'fig'；\n"
            "3. `g`: 全局变量环境，默认保持为 'globals()' 即可。\n\n"
            "📌 请确保绘图代码满足以下要求：\n"
            "- 包含所有必要的 import（如 `import matplotlib.pyplot as plt`, `import seaborn as sns` 等）；\n"
            "- 必须包含数据定义（如 `df = pd.DataFrame(...)`），不要依赖外部变量；\n"
            "- 推荐使用 `fig, ax = plt.subplots()` 显式创建图像；\n"
            "- 使用 `ax` 对象进行绘图操作（例如：`sns.lineplot(..., ax=ax)`）；\n"
            "- 最后明确将图像对象保存为 `fname` 变量（如 `fig = plt.gcf()`）。\n\n"
            "📌 不需要自己保存图像，函数会自动保存并展示。\n\n"
            "✅ 合规示例代码：\n"
            "```python\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import pandas as pd\n\n"
            "df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})\n"
            "fig, ax = plt.subplots()\n"
            "sns.lineplot(data=df, x='x', y='y', ax=ax)\n"
            "ax.set_title('Line Plot')\n"
            "fig = plt.gcf()  # 一定要赋值给 fname 指定的变量名\n"
            "```"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "py_code": {
                    "type": "string",
                    "description": (
                        "需要执行的 Python 绘图代码（字符串形式）。"
                        "代码必须创建一个 matplotlib 图像对象，并赋值为 `fname` 所指定的变量名。"
                    )
                },
                "fname": {
                    "type": "string",
                    "description": "图像对象的变量名（例如 'fig'），代码中必须使用这个变量名保存绘图对象。"
                },
                "g": {
                    "type": "string",
                    "description": "运行环境变量，默认保持为 'globals()' 即可。",
                    "default": "globals()"
                }
            },
            "required": ["py_code", "fname"]
        }
    }
}

get_answer_tool = {
    "type": "function",
    "function": {
        "name": "get_answer",
        "description": (
            "联网搜索工具，当用户提出的问题超出你的知识库范畴时，或该问题你不知道答案的时候，请调用该函数来获得问题的答案。该函数会自动从知乎上搜索得到问题相关文本，而后你可围绕文本内容进行总结，并回答用户提问。需要注意的是，当用户点名要求想要了解GitHub上的项目时候，请调用get_answer_github函数。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "一个满足知乎搜索格式的问题，用字符串形式进行表示。",
                    "example": "什么是MCP?"
                },
                "g": {
                    "type": "string",
                    "description": "Global environment variables, default to globals().",
                    "default": "globals()"
                }
            },
            "required": ["q"]
        }
    }
}
# 工具函数
def python_inter(py_code, g='globals()'):
    """
    专门用于执行python代码，并获取最终查询或处理结果。
    :param py_code: 字符串形式的Python代码，
    :param g: g，字符串形式变量，表示环境变量，无需设置，保持默认参数即可
    :return：代码运行的最终结果
    """    
    print("正在调用python_inter工具运行Python代码...")
    try:
        return str(eval(py_code, g))
    except Exception as e:
        global_vars_before = set(g.keys())
        try:            
            exec(py_code, g)
        except Exception as e:
            return f"代码执行时报错{e}"
        global_vars_after = set(g.keys())
        new_vars = global_vars_after - global_vars_before
        if new_vars:
            result = {var: g[var] for var in new_vars}
            print("代码已顺利执行，正在进行结果梳理...")
            return str(result)
        else:
            print("代码已顺利执行，正在进行结果梳理...")
            return "已经顺利执行代码"

def fig_inter(py_code, fname, g='globals()'):
    print("正在调用fig_inter工具运行Python代码...")
    import matplotlib
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    # 切换为无交互式后端
    current_backend = matplotlib.get_backend()
    matplotlib.use('Agg')

    # 用于执行代码的本地变量
    local_vars = {"plt": plt, "pd": pd, "sns": sns}

    # 相对路径保存目录
    pics_dir = 'data/pics'
    if not os.path.exists(pics_dir):
        os.makedirs(pics_dir)

    try:
        # 执行用户代码
        exec(py_code, g, local_vars)
        g.update(local_vars)

        # 获取图像对象
        fig = local_vars.get(fname, None)
        print(fig)
        if fig:
            rel_path = os.path.join(pics_dir, f"{fname}.png")
            fig.savefig(rel_path, bbox_inches='tight')
            print("代码已顺利执行，正在进行结果梳理...")
            return f"✅ 图片已保存，相对路径: {rel_path}"
        else:
            return "⚠️ 代码执行成功，但未找到图像对象，请确保有 `fig = ...`。"
    except Exception as e:
        return f"❌ 执行失败：{e}"
    finally:
        # 恢复原有绘图后端
        matplotlib.use(current_backend)

def google_search(query, num_results=10, site_url=None):
    
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("CSE_ID")
    print("Google API key:", api_key, "CSE ID:", cse_id)
    url = "https://www.googleapis.com/customsearch/v1"

    # API 请求参数
    if site_url == None:
        params = {
        'q': query,          
        'key': api_key,      
        'cx': cse_id,        
        'num': num_results   
        }
    else:
        params = {
        'q': query,         
        'key': api_key,      
        'cx': cse_id,        
        'num': num_results,  
        'siteSearch': site_url
        }

    # 发送请求
    response = requests.get(url, params=params)
    response.raise_for_status()

    # 解析响应
    search_results = response.json().get('items', [])

    # 提取所需信息
    results = [{
        'title': item['title'],
        'link': item['link'],
        'snippet': item['snippet']
    } for item in search_results]

    return results

def windows_compatible_name(s, max_length=255):
    """
    将字符串转化为符合Windows文件/文件夹命名规范的名称。
    
    参数:
    - s (str): 输入的字符串。
    - max_length (int): 输出字符串的最大长度，默认为255。
    
    返回:
    - str: 一个可以安全用作Windows文件/文件夹名称的字符串。
    """

    # Windows文件/文件夹名称中不允许的字符列表
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

    # 使用下划线替换不允许的字符
    for char in forbidden_chars:
        s = s.replace(char, '_')

    # 删除尾部的空格或点
    s = s.rstrip(' .')

    # 检查是否存在以下不允许被用于文档名称的关键词，如果有的话则替换为下划线
    reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
                      "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    if s.upper() in reserved_names:
        s += '_'

    # 如果字符串过长，进行截断
    if len(s) > max_length:
        s = s[:max_length]

    return s

def get_search_text(q, url):
    cookie = os.getenv('search_cookie')
    user_agent = os.getenv('search_ueser_agent')

    code_ = False
    headers = {
        'authority': 'www.zhihu.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': cookie,
        'upgrade-insecure-requests': '1',
        'user-agent':user_agent,
    }

    # 普通问答地址
    if 'zhihu.com/question' in url:
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title = res_xpath.xpath('//div/div[1]/div/h1/text()')[0]
        text_d_elements = res_xpath.xpath('//div[contains(@class, "RichText")]//p/text()') # 替换为测试有效的XPath
        if text_d_elements:
            text_d = text_d_elements
        else:
            print(f"Warning: Could not find main text for URL: {url}. Check XPath for text_d.")
            text_d = [] # 确保 text_d 仍然是一个列表，即使是空的，以便后续循环不会报错
    
    # 专栏地址
    elif 'zhuanlan' in url:
        headers['authority'] = 'zhuanlan.zhihu.com'
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title_elements = res_xpath.xpath('//h1[contains(@class, "Post-Title")]/text()')
        if title_elements:
            title = title_elements[0]
        else:
            # 处理未找到标题的情况，例如打印警告，或者设置 title 为 None
            print(f"Warning: Could not find title for URL: {url}. HTML structure might have changed.")
            title = None # 或者 raise Exception("Title not found")
        #title = res_xpath.xpath('//div[1]/div/main/div/article/header/h1/text()')[0]
        text_d_elements = res_xpath.xpath('//div[contains(@class, "RichText")]//p/text()') # 替换为测试有效的XPath
        if text_d_elements:
            text_d = text_d_elements
        else:
            print(f"Warning: Could not find main text for URL: {url}. Check XPath for text_d.")
            text_d = [] # 确保 text_d 仍然是一个列表，即使是空的，以便后续循环不会报错

        code_elements = res_xpath.xpath('//div/main/div/article/div[1]/div/div/div//pre/code/text()')
        if code_elements:
            code_ = code_elements
        else:
            code_ = [] # 同样确保 code_ 是列表
            
    # 特定回答的问答网址
    elif 'answer' in url:
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title = res_xpath.xpath('//div/div[1]/div/h1/text()')[0]
        text_d_elements = res_xpath.xpath('//div[contains(@class, "RichText")]//p/text()') # 替换为测试有效的XPath
        if text_d_elements:
            text_d = text_d_elements
        else:
            print(f"Warning: Could not find main text for URL: {url}. Check XPath for text_d.")
            text_d = [] # 确保 text_d 仍然是一个列表，即使是空的，以便后续循环不会报错

    if title == None:
        return None
    
    else:
        title = windows_compatible_name(title)

        # 创建问题答案正文
        text = ''
        for t in text_d:
            txt = str(t).replace('\n', ' ')
            text += txt

        # 如果有code，则将code追加到正文的追后面
        if code_:
            for c in code_:
                co = str(c).replace('\n', ' ')    
                text += co

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")     
        json_data = [
            {
                "link": url,
                "title": title,
                "content": text,
                "tokens": len(encoding.encode(text))
            }
        ]
        
        # 自动创建目录，如果不存在的话
        dir_path = f'./data/auto_search/{q}'
        os.makedirs(dir_path, exist_ok=True)
    
        with open('./data/auto_search/%s/%s.json' % (q, title), 'w') as f:
            json.dump(json_data, f)

        return title
    
def get_answer(q, g='globals()'):
    """
    当你无法回答某个问题时，调用该函数，能够获得答案
    :param q: 必选参数，询问的问题，字符串类型对象
    :param g: g，字符串形式变量，表示环境变量，无需设置，保持默认参数即可
    :return：某问题的答案，以字符串形式呈现
    """
    # 默认搜索返回5个答案
    print('正在接入谷歌搜索，查找和问题相关的答案...')
    results = google_search(query=q, num_results=5, site_url='https://zhihu.com/')
    
    # 创建对应问题的子文件夹
    folder_path = './data/auto_search/%s' % q
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # 单独提取links放在一个list中
    num_tokens = 0
    content = ''
    for item in results:
        url = item['link']
        print('正在检索：%s' % url)
        title = get_search_text(q, url)
        with open('./data/auto_search/%s/%s.json' % (q, title), 'r') as f:
            jd = json.load(f)
        num_tokens += jd[0]['tokens']
        if num_tokens <= 12000:
            # print(jd[0]['content'])
            content += jd[0]['content']
        else:
            break
    return(content)

def print_code_if_exists(function_args):
    """
    如果存在代码片段，则打印代码
    """
    if function_args.get('py_code'):
        code = function_args['py_code']
        print("即将执行以下代码：")
        print(code)
        
if __name__ == "__main__":
    #test_python_inter()
    #test_fig_inter()
    url = 'https://www.zhihu.com/question/7762420288'
    q = "什么是MCP"
    print(get_answer(q))
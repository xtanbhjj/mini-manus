# mini-manus

## 项目简介

Mini-Manus 是一个基于 OpenAI API 的智能助手，能够执行 Python 代码、进行数据可视化、联网搜索信息，并帮助用户解决各种问题。它特别适合用于技术研究、数据分析和编程辅助任务。

## 功能特点

1. **Python 代码执行**：支持执行非绘图类的 Python 代码并返回结果
2. **数据可视化**：支持通过 matplotlib 和 seaborn 进行数据可视化
3. **联网搜索**：能够从知乎等网站获取问题答案
4. **深度研究**：提供专业的研究辅助功能，帮助用户深入分析问题
5. **交互式对话**：支持多轮对话，保持上下文理解

## 安装与配置

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone [仓库地址]
   cd mini-manus
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 创建 `.env` 文件并配置 API 密钥：
   ```
   API_KEY=your_openai_api_key
   BASE_URL=your_openai_api_base_url
   MODEL=your_preferred_model
   GOOGLE_SEARCH_API_KEY=your_google_search_api_key
   CSE_ID=your_custom_search_engine_id
   search_cookie=your_zhihu_cookie
   search_ueser_agent=your_user_agent
   ```

## 使用方法

### 基础对话模式

```python
from manus import miniManusClass

bot = miniManusClass()
bot.chat()  # 进入交互式对话
```

### 研究任务模式

```python
from manus import miniManusClass

bot = miniManusClass()
bot.research_task("你的研究问题")  # 进行深入研究
```

### 功能调用示例

1. **执行 Python 代码**：
   ```python
   # 会自动调用 python_inter 函数
   "请计算 1 到 100 的和"
   ```

2. **数据可视化**：
   ```python
   # 会自动调用 fig_inter 函数
   "请绘制 sin(x) 函数的图像，x 范围从 0 到 2π"
   ```

3. **联网搜索**：
   ```python
   # 会自动调用 get_answer 函数
   "什么是 MCP 技术？"
   ```

## 文件结构

```
mini-manus/
├── funcs.py        # 功能函数和工具定义
├── manus.py        # 主程序逻辑和交互类
├── .env            # 环境变量配置文件
├── data/           # 数据存储目录
│   ├── auto_search/ # 联网搜索结果
│   ├── pics/       # 生成的图片
│   └── research/   # 研究报告
└── README.md       # 本文件
```

## 注意事项

1. 使用前请确保已正确配置所有 API 密钥
2. 联网搜索功能需要有效的 Google 自定义搜索 API 和知乎 cookie
3. 代码执行功能有潜在安全风险，请勿执行不可信代码
4. 可视化功能需要正确安装 matplotlib 和 seaborn

## 贡献

欢迎提交 issue 或 pull request 来改进项目。

## 许可证

[MIT License](LICENSE)
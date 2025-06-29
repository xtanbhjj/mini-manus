from funcs import *

tools = [python_inter_tool,fig_inter_tool,get_answer_tool]

def create_function_response_messages(messages, response):
    available_functions = {
        "python_inter": python_inter,
        "fig_inter": fig_inter,
        "get_answer": get_answer,
    }
    
    # 提取function call messages
    function_call_messages = response.choices[0].message.tool_calls

    # 将function call messages追加到消息列表中
    messages.append(response.choices[0].message.model_dump())

    # 提取本次外部函数调用的每个任务请求
    for function_call_message in function_call_messages:
        
        # 提取外部函数名称
        tool_name = function_call_message.function.name
        # 提取外部函数参数
        tool_args = json.loads(function_call_message.function.arguments)       
        
        # 查找外部函数
        fuction_to_call = available_functions[tool_name]

        # 打印代码
        print_code_if_exists(function_args=tool_args)

        # 运行外部函数
        try:
            tool_args['g'] = globals()
            # 运行外部函数
            function_response = fuction_to_call(**tool_args)
        except Exception as e:
            function_response = "函数运行报错如下:" + str(e)

        # 拼接消息队列
        messages.append(
            {
                "role": "tool",
                "content": function_response,
                "tool_call_id": function_call_message.id,
            }
        )
        
    return messages     

def chat_base(messages, client, model):
    """
    获得一次模型对用户的响应。若其中需要调用外部函数，
    则会反复多次调用create_function_response_messages函数获得外部函数响应。
    """
    
    client = client
    model = model
    
    try:
        response = client.chat.completions.create(
            model=model,  
            messages=messages,
            tools=tools,
        )
        
    except Exception as e:
        print("模型调用报错" + str(e))
        return None

    if response.choices[0].finish_reason == "tool_calls":
        while True:
            messages = create_function_response_messages(messages, response)
            response = client.chat.completions.create(
                model=model,  
                messages=messages,
                tools=tools,
            )
            if response.choices[0].finish_reason != "tool_calls":
                break
    
    return response

def save_markdown_to_file(content: str, filename_hint: str, directory="data/research"):
    # 在当前项目目录下创建 research_task 文件夹
    save_dir = os.path.join(os.getcwd(), directory)

    # 如果目录不存在则创建
    os.makedirs(save_dir, exist_ok=True)

    # 创建文件名（取前8个字符并加上...）
    filename = f"{filename_hint[:4]}....md"

    # 完整文件路径
    file_path = os.path.join(save_dir, filename)

    # 将内容保存为Markdown文档
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"文件已成功保存到：{file_path}")

class miniManusClass:
    def __init__(self):
        
        load_dotenv(override=True)
        
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("MODEL")
        self.base_url = os.getenv("BASE_URL")
        self.messages = [{"role":"system", "content":"你miniManus，是Alpha的助手，一名助人为乐的助手。"}]
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        try:
            print("正在测试模型能否正常调用...")
            self.models = self.client.models.list()
            
            if self.models:
                print("▌ MiniManus初始化完成，欢迎使用！")
            else:
                print("模型无法调用，请检查网络环境或本地模型配置。")

        except Exception as e:
            print("初始化失败，可能是网络或配置错误。详细信息：", str(e))

    def chat(self):
        print("你好，我是Alpha的MiniManus，有什么需要帮助的？")
        while True:
            question = input("请输入您的问题(输入quit以结束对话): ")
            if question == "quit":
                break  
                
            self.messages.append({"role": "user", "content": question})
            self.messages = self.messages[-20: ]
            
            response = chat_base(messages=self.messages, 
                                 client=self.client, 
                                 model=self.model)
            print(response.choices[0].message.content)
            self.messages.append(response.choices[0].message)
            
    def research_task(self, question):
        prompt_style1 = """
        你是一名专业且细致的助手，你的任务是在用户提出问题后，通过友好且有引导性的追问，更深入地理解用户真正的需求背景。这样，你才能提供更精准和更有效的帮助。
        当用户提出一个宽泛或者不够明确的问题时，你应当积极主动地提出后续问题，引导用户提供更多背景和细节，以帮助你更准确地回应。
        示例引导问题：
        
        用户提问示例：
        最近，在大模型技术领域，有一项非常热门的技术，名叫MCP，model context protocol，调用并深度总结，这项技术与OpenAI提出的function calling之间的区别。
        
        你应该给出的引导式回应示例：
        在比较MCP（Model Context Protocol）与OpenAI的Function Calling时，我可以涵盖以下几个方面：
        - 定义和基本概念：MCP和Function Calling的基本原理和目标。
        - 工作机制：它们如何处理模型的输入和输出。
        - 应用场景：它们分别适用于哪些具体场景？
        - 技术优势与局限性：各自的优劣势分析。
        - 生态和兼容性：它们是否能与现有的大模型和应用集成。
        - 未来发展趋势：这些技术未来的发展方向。
        请问你是否希望我特别关注某些方面，或者有特定的技术细节需要深入分析？
        
        再比如用户提问：
        请你帮我详细整理，华为910B2x鲲鹏920，如何部署DeepSeek模型。
        
        你应该给出的引导式回应示例：
        请提供以下详细信息，以便我能为您整理完整的部署指南：
        1. 您希望部署的DeepSeek模型具体是哪一个？（例如DeepSeek-VL、DeepSeek-Coder等）
        2. 目标系统环境（操作系统、已有软件环境等）？
        3. 是否有特定的深度学习框架要求？（如PyTorch、TensorFlow）
        4. 是否需要优化部署（如使用昇腾NPU加速）？
        5. 期望的使用场景？（如推理、训练、微调等）
        请提供这些信息后，我将为您整理具体的部署步骤。
        
        记住，保持友好而专业的态度，主动帮助用户明确需求，而不是直接给出不够精准的回答。现在用户提出问题如下：{}，请按照要求进行回复。
        """
        
        prompt_style2 = """
        你是一位知识广博、擅长利用多种外部工具的资深研究员。当用户已明确提出具体需求：{}，现在你的任务是：
        首先明确用户问题的核心及相关细节。
        尽可能调用可用的外部工具（例如：联网搜索工具get_answer、GitHub搜索工具get_answer_github、本地代码运行工具python_inter以及其他工具），围绕用户给出的原始问题和补充细节，进行广泛而深入的信息收集。
        综合利用你从各种工具中获取的信息，提供详细、全面、专业且具有深度的解答。你的回答应尽量达到2000字以上，内容严谨准确且富有洞察力。
        
        示例流程：
        用户明确需求示例：
        我目前正在学习 ModelContextProtocol（MCP），主要关注它在AI模型开发领域中的具体应用场景、技术细节和一些业界最新的进展。
        你的回应流程示例：
        首先重述并确认用户的具体需求。
        明确你将调用哪些外部工具，例如：
        使用联网搜索工具查询官方或权威文档对 MCP 在AI模型开发领域的具体应用说明；
        调用GitHub搜索工具，寻找业界针对MCP技术项目；
        整理并分析通过工具获取的信息，形成一篇逻辑清晰、结构合理的深度报告。
        
        再比如用户需要编写数据分析报告示例：
        我想针对某电信公司过去一年的用户数据，编写一份详细的用户流失预测数据分析报告，报告需要包括用户流失趋势分析、流失用户特征分析、影响用户流失的关键因素分析，并给出未来减少用户流失的策略建议。
        你的回应流程示例：
        明确并确认用户需求，指出分析内容包括用户流失趋势、流失用户特征、关键影响因素以及策略建议。
        明确你将调用哪些外部工具，例如：
        使用数据分析工具对提供的用户数据进行流失趋势分析，生成趋势图表；
        使用代码执行环境（如调用python_inter工具）对流失用户进行特征分析，确定典型特征；
        通过统计分析工具识别影响用户流失的关键因素（如服务质量、价格敏感度、竞争对手促销），同时借助绘图工具（fig_inter）进行重要信息可视化展示；
        使用互联网检索工具检索行业内最新的客户保留策略与实践，提出有效的策略建议。
        
        记住，回答务必详细完整，字数至少在2000字以上，清晰展示你是如何运用各种外部工具进行深入研究并形成专业结论的。
        
        """
        
        response = self.client.chat.completions.create(model=self.model,
                                                  messages=[{"role": "user", "content": prompt_style1.format(question)}])
        
        print(response.choices[0].message.content)
        new_messages = [
            {"role": "user", "content": question},
            response.choices[0].message.model_dump()
        ]
        
        new_question = input("请输入您的补充说明(输入quit以结束对话): ")
        if new_question == "quit":
            return None
        else:
            new_messages.append({"role": "user", "content":prompt_style2.format(new_question)})
            
            second_response = chat_base(messages=new_messages, 
                                        client=self.client, 
                                        model=self.model)
            
            print("done")
            print(second_response.choices[0].message.content)
            save_markdown_to_file(content=second_response.choices[0].message.content, 
                                  filename_hint=question)
            
        def clear_messages(self):
            self.messages = []

if __name__ == "__main__":
    test_bot = miniManusClass()
    test_bot.chat()
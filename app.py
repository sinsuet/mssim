import os
import json
from flask import Flask, request, jsonify
from pydantic import ValidationError
import dashscope
from dashscope.api_entities.dashscope_response import Role
from dotenv import load_dotenv

# 加载 .env 文件中的 API Key
load_dotenv()

# 导入协议定义
from protocol import ContextPack, SearchSpec

app = Flask(__name__)

# 配置 Qwen 模型
MODEL_NAME = 'qwen-plus' 

# 检查 API Key
if not os.environ.get("DASHSCOPE_API_KEY") and not dashscope.api_key:
    print("⚠️ Warning: DASHSCOPE_API_KEY not found. Please set it in .env or environment variables.")

def call_qwen_brain(context_md: str) -> str:
    """
    封装 DashScope API 调用逻辑
    """
    # --- [关键修改] 注入强 JSON 结构的 System Prompt ---
    system_prompt = """
    你是一个卫星热控系统的AI设计专家 (DV1.2 Brain)。
    你的任务是根据输入的物理设计现状 (ContextPack)，输出符合严格 Schema 定义的优化指令 (SearchSpec)。

    【输出格式要求】
    你必须输出如下结构的纯 JSON (不要使用 Markdown 代码块):
    {
        "plan_id": "PLAN_YYYYMMDD_001",
        "reasoning_summary": "这里写宏观策略，解释为什么要选这个方向（例如：因为+X方向有干涉，所以尝试往-Y方向移动）",
        "actions": [
            {
                "op_id": "MOVE",
                "target_component": "组件名称",
                "search_axis": "Y", 
                "bounds": [-50.0, 0.0],
                "unit": "mm",
                "conflicts": ["关联的违规ID"],
                "hints": ["Try moving away from heat source"]
            }
        ]
    }

    【物理规则约束】
    1. search_axis 只能是 "X", "Y", 或 "Z" 中的一个。
    2. bounds 必须是两个数字的列表 [min, max]，代表相对于当前位置的搜索范围。
    3. op_id 只能是: "MOVE", "SWAP", "ADD_SURFACE"。
    4. 如果是 MOVE 操作，请只选择一个最有可能解决问题的轴向进行搜索，不要同时给出三个轴。
    """

    messages = [
        {'role': Role.SYSTEM, 'content': system_prompt},
        {'role': Role.USER, 'content': f"当前设计状态如下：\n{context_md}"}
    ]

    try:
        response = dashscope.Generation.call(
            model=MODEL_NAME,
            messages=messages,
            result_format='message',
            temperature=0.5, # 降低温度，让结构更稳定
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"Qwen API Error: {response.code} - {response.message}")

    except Exception as e:
        raise Exception(f"Model Inference Failed: {str(e)}")

@app.route('/optimize', methods=['POST'])
def optimize_design():
    try:
        # Step 1: 接收输入
        input_data = request.json
        context = ContextPack(**input_data)
        
        # Step 2: 转换为 Prompt
        context_md = context.to_markdown_prompt()
        print(f"--- [Log] Sending to {MODEL_NAME} ---\n{context_md[:100]}...")

        # Step 3: 调用 LLM
        llm_raw_output = call_qwen_brain(context_md)
        print(f"--- [Log] Qwen Response (Raw) ---\n{llm_raw_output}")

        # Step 4: 清洗数据 (处理可能存在的 Markdown 标记)
        clean_json_str = llm_raw_output.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        
        spec_dict = json.loads(clean_json_str.strip())

        # Step 5: Pydantic 强校验
        validated_spec = SearchSpec(**spec_dict)

        # Step 6: 返回结果
        return jsonify(validated_spec.model_dump()), 200

    except ValidationError as ve:
        print(f"❌ Protocol Violation: {ve}")
        # 返回详细的 Pydantic 错误信息以便调试
        return jsonify({"error": "Protocol Violation", "details": ve.errors()}), 400
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON: {llm_raw_output}")
        return jsonify({"error": "Invalid JSON from LLM", "raw_output": llm_raw_output}), 500
    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Satellite Semantic Engine (powered by {MODEL_NAME}) is running on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
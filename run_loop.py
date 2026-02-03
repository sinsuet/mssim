import requests
import json
import random
from protocol import ContextPack, ViolationItem, ViolationType

# API 地址
URL = "http://localhost:5000/optimize"

def run_simulation_loop():
    print("🚀 Starting DV1.0 Neuro-Symbolic Loop...\n")

    # =================================================================
    # 1. 模拟物理引擎 (SimEval) 生成当前状态
    # =================================================================
    # 场景：电池包与安装支架发生碰撞，且过热
    # 构造符合 Protocol v1.0 的数据包
    context_data = {
        "design_iteration": 42,
        "metrics": {
            "max_temp": 65.5,  # 摄氏度
            "total_mass": 12.4, # kg
            "power_usage": 120.0 # W
        },
        "violations": [
            {
                "id": "VIO_THERMAL_01",
                "type": ViolationType.THERMAL_OVERHEAT,
                "description": "Battery_Pack exceeds operational limit (65.5C > 50C).",
                "involved_components": ["Battery_Pack", "Power_Amplifier"],
                "severity": 0.9
            },
            {
                "id": "VIO_GEO_02",
                "type": ViolationType.GEOMETRY_CLASH,
                "description": "Hard clash detected between Battery_Pack and Structural_Rib_X.",
                "involved_components": ["Battery_Pack", "Structural_Rib_X"],
                "severity": 1.0
            }
        ],
        "geometry_summary": (
            "Battery_Pack is mounted on +X Panel. It is sandwiched between "
            "Structural_Rib_X (distance -2mm, CLASH) and Power_Amplifier (+Z side). "
            "Available space exists in the -Y direction."
        ),
        "thermal_summary": (
            "Heat accumulation on +X Panel. Power_Amplifier is blocking radiative "
            "heat path of Battery_Pack."
        ),
        "history_trace": [
            "Iter 40: Moved Battery_Pack +X by 5mm -> Resulted in Clash VIO_GEO_02."
        ]
    }
    
    # 使用 Pydantic 校验并转为 JSON (确保客户端发出的数据也是合规的)
    try:
        payload = ContextPack(**context_data).model_dump(mode='json')
    except Exception as e:
        print(f"❌ Client Data Error: {e}")
        return

    print(f"📡 [Macro] Sending Design State to Brain (Iter {payload['design_iteration']})...")
    
    # =================================================================
    # 2. 调用语义层 (Semantic Layer) 获取搜索规格
    # =================================================================
    try:
        response = requests.post(URL, json=payload)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Is 'app.py' running?")
        return

    if response.status_code != 200:
        print(f"❌ Server Error: {response.text}")
        return

    search_spec = response.json()
    print(f"✅ [Macro] Received SearchSpec from Qwen.")
    print(f"   Reasoning: \"{search_spec['reasoning_summary']}\"")

    # =================================================================
    # 3. 模拟数值求解器 (Solver - Micro Optimization)
    # =================================================================
    # 这里对应文档中的 "Solver: 处理连续参数与物理约束" [cite: 40]
    # 我们不让 LLM 猜坐标，而是让它给范围，Solver 在范围内找最优解。
    
    print("\n⚙️ [Micro] Solver initiated based on Spec...")
    
    for action in search_spec['actions']:
        print(f"   -> Optimization Task: {action['op_id']} on '{action['target_component']}'")
        
        if action['op_id'] == "MOVE" and action['bounds']:
            # 模拟：求解器在 bounds 范围内运行梯度下降
            # 这里我们用随机采样模拟求解过程
            min_b, max_b = action['bounds']
            axis = action['search_axis']
            
            # 模拟寻找最优解的过程
            simulated_best_val = round(random.uniform(min_b, max_b), 2)
            
            print(f"      Constraint Bounds: [{min_b}, {max_b}] {action['unit']}")
            print(f"      Solver Action: Run Gradient Descent along {axis}-axis...")
            print(f"      🎯 OPTIMAL PARAMETER FOUND: {axis} = {simulated_best_val} {action['unit']}")
            print(f"      (Status: Conflicts {action['conflicts']} resolved)")
        else:
            print(f"      Action type {action['op_id']} executed symbolically.")

if __name__ == "__main__":
    run_simulation_loop()
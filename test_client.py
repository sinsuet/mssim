import requests
import json

# 定义目标 URL
url = "http://localhost:5000/optimize"

# 模拟：物理引擎检测到的状态 (ContextPack)
payload = {
    "design_iteration": 12,
    "violations": [
        "Component 'Battery_Pack_Main' is overlapping with 'Star_Tracker_Bracket' (Clash Depth: 3mm)",
        "Thermal Violation: 'Battery_Pack_Main' temp predicted 55C (Limit 45C)"
    ],
    "hotspots": {
        "Battery_Pack_Main": 55.0,
        "CPU_Module": 48.0
    },
    "geometry_summary": "The Battery_Pack_Main is mounted on the +X Panel. It is strictly constrained by the Star_Tracker_Bracket in the +Y direction. -Y direction is empty space."
}

print(f"📡 Sending Context to Semantic Engine...")

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("\n✅ [Success] Received Optimization Plan from Qwen:")
        data = response.json()
        
        # 打印 Qwen 的决策逻辑
        print(f"Strategy: {data['strategy_summary']}")
        print(f"Actions:")
        for action in data['actions']:
            print(f"  - Op: {action['op_id']}")
            print(f"    Target: {action['target_component']}")
            print(f"    Reasoning: {action['reasoning']}")
            print(f"    Search Bounds: {action['bounds']}")
    else:
        print(f"\n❌ [Error] {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Connection failed: {e}")
# run_pro.py
import requests
import time
import json
from scipy.optimize import minimize_scalar
from protocol import ViolationType
from logger import ExperimentLogger # 导入刚才写的 Logger
from logger import ExperimentLogger
from analyzer import render_dashboard  # [新增] 导入绘图模块
# --- 配置 ---
URL = "http://localhost:5000/optimize"
RIB_X = 10.0
HEAT_X, HEAT_Z = 0.0, 20.0
SAFE_DIST = 3.0
TEMP_LIMIT = 50.0

class EngineeringLoop:
    def __init__(self):
        # 初始化日志系统
        self.logger = ExperimentLogger()
        
        # 初始物理状态
        self.pos = {"x": 8.0, "y": 0.0, "z": 18.0}
        self.iter = 0
        self.history = []
        
        # 当前状态缓存
        self.max_temp = 0.0
        self.dist_to_rib = 0.0
        self.violations = []
        self.last_solver_cost = 0.0
        self.last_reasoning = ""

    def physics_update(self):
        """SimEval: 计算物理场"""
        self.violations = []
        
        # 1. Geometry
        self.dist_to_rib = abs(self.pos["x"] - RIB_X)
        if self.dist_to_rib < SAFE_DIST:
            self.violations.append({
                "id": f"VIO_GEO_{self.iter}",
                "type": ViolationType.GEOMETRY_CLASH,
                "description": f"Gap to Rib {self.dist_to_rib:.2f}mm < {SAFE_DIST}mm",
                "involved_components": ["Battery", "Rib"],
                "severity": 1.0
            })

        # 2. Thermal
        d_sq = (self.pos["x"] - HEAT_X)**2 + (self.pos["z"] - HEAT_Z)**2
        self.max_temp = 20.0 + 800.0 / (d_sq + 10.0)
        if self.max_temp > TEMP_LIMIT:
            self.violations.append({
                "id": f"VIO_THERM_{self.iter}",
                "type": ViolationType.THERMAL_OVERHEAT,
                "description": f"Temp {self.max_temp:.1f}C > {TEMP_LIMIT}C",
                "involved_components": ["Battery", "HeatSrc"],
                "severity": (self.max_temp - TEMP_LIMIT)/TEMP_LIMIT
            })

    def get_context(self):
        """Semantic: 生成 ContextPack"""
        geo = (f"Battery at ({self.pos['x']:.2f}, {self.pos['y']:.2f}, {self.pos['z']:.2f}). "
               f"Rib (Fixed Wall) at X={RIB_X}. HeatSource at ({HEAT_X}, {HEAT_Z}).")
        
        return {
            "design_iteration": self.iter,
            "metrics": {"max_temp": self.max_temp, "min_dist": self.dist_to_rib},
            "violations": self.violations,
            "geometry_summary": geo,
            "thermal_summary": f"Max Temp {self.max_temp:.1f}C.",
            "history_trace": self.history[-3:], # 只带最近3条历史
            "allowed_ops": ["MOVE"] # [新增] 动态约束：本场景只允许移动
        }

    def cost_func(self, val, axis):
        """Micro-Solver: 代价函数 (带安全裕度)"""
        orig = self.pos[axis]
        self.pos[axis] = val
        
        cost = 0.0
        # Clash Penalty
        d = abs(self.pos["x"] - RIB_X)
        if d < SAFE_DIST: cost += 1000 * (SAFE_DIST - d)**2
        elif d < SAFE_DIST + 1.0: cost += 10 * (1.0 - (d - SAFE_DIST))
        
        # Thermal Penalty
        d_sq = (self.pos["x"] - HEAT_X)**2 + (self.pos["z"] - HEAT_Z)**2
        t = 20.0 + 800.0 / (d_sq + 10.0)
        if t > TEMP_LIMIT: cost += 50 * (t - TEMP_LIMIT)
        else: cost += 0.05 * t
        
        self.pos[axis] = orig
        return cost

    def run(self):
        print(f"🚀 Starting Engineering Run. Logs -> {self.logger.run_dir}")
        
        for i in range(1, 6): # Max 5 iters
            self.iter = i
            print(f"\n--- Iteration {self.iter} ---")
            
            # 1. Physics Check
            self.physics_update()
            is_safe = len(self.violations) == 0
            
            # 2. Logging Data Update (CSV)
            self.logger.log_metrics({
                "iteration": self.iter,
                "pos_x": self.pos["x"], "pos_y": self.pos["y"], "pos_z": self.pos["z"],
                "max_temp": self.max_temp,
                "min_dist_rib": self.dist_to_rib,
                "is_safe": is_safe,
                "solver_cost": self.last_solver_cost,
                "ai_reasoning": self.last_reasoning
            })

            if is_safe:
                print("✅ Design Converged & Safe!")
                self.logger.save_summary("SUCCESS", self.iter)
                break

            # 3. LLM Call
            ctx = self.get_context()
            try:
                resp = requests.post(URL, json=ctx)
                spec = resp.json()
                
                # [关键] 记录完整的 LLM 交互对
                self.logger.log_llm_interaction(self.iter, ctx, spec)
                
                self.last_reasoning = spec.get("reasoning_summary", "")
                print(f"🧠 AI Strategy: {self.last_reasoning[:80]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                self.logger.save_summary(f"FAILED: {e}", self.iter)
                break

            # 4. Solver Execution
            actions = spec.get("actions", [])
            if actions:
                act = actions[0]
                axis = act["search_axis"].lower()
                bounds = act["bounds"]
                curr = self.pos[axis]
                
                print(f"⚙️ Solver optimizing {axis.upper()} in [{bounds[0]}, {bounds[1]}]...")
                res = minimize_scalar(
                    self.cost_func, 
                    bounds=(curr + bounds[0], curr + bounds[1]), 
                    args=(axis,), method='bounded'
                )
                
                if res.success:
                    self.pos[axis] = res.x
                    self.last_solver_cost = res.fun
                    delta = res.x - curr
                    
                    # 记录历史用于下一轮 Prompt
                    self.history.append(f"Iter {self.iter}: AI tried MOVE {axis.upper()} range {bounds}. Solver delta: {delta:.2f}. Result: {'Safe' if delta!=0 else 'Stuck'}")
                    print(f"🎯 Optimal: {axis.upper()}={res.x:.4f} (Delta {delta:.2f})")
                else:
                    print("⚠️ Solver failed.")
            
            time.sleep(1)
        else:
            print("❌ Max iterations reached.")
            self.logger.save_summary("TIMEOUT", 5)
        print("\n🎨 Generating Analysis Report...")
        render_dashboard(self.logger.run_dir)
        print(f"✨ Experiment Finished. Check folder: {self.logger.run_dir}")


if __name__ == "__main__":
    eng = EngineeringLoop()
    eng.run()
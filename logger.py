# logger.py
import os
import json
import csv
import time
from datetime import datetime

class ExperimentLogger:
    def __init__(self, base_dir="experiments"):
        # 1. 创建带时间戳的实验文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(base_dir, f"run_{timestamp}")
        os.makedirs(self.run_dir, exist_ok=True)
        
        # 2. 创建子文件夹
        self.llm_log_dir = os.path.join(self.run_dir, "llm_interactions")
        os.makedirs(self.llm_log_dir, exist_ok=True)
        
        # 3. 初始化 CSV 统计文件
        self.csv_path = os.path.join(self.run_dir, "evolution_trace.csv")
        self._init_csv()
        
        print(f"📁 [Logger] Experiment initialized at: {self.run_dir}")

    def _init_csv(self):
        """初始化CSV表头"""
        headers = [
            "iteration", "pos_x", "pos_y", "pos_z", 
            "max_temp", "min_dist_rib", "is_safe", 
            "solver_cost", "ai_reasoning_len"
        ]
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def log_llm_interaction(self, iteration, context_dict, response_dict):
        """保存每一次 LLM 的输入输出 (用于 Traceability)"""
        # 保存 Input (Context)
        with open(os.path.join(self.llm_log_dir, f"iter_{iteration:02d}_req.json"), 'w', encoding='utf-8') as f:
            json.dump(context_dict, f, indent=2, ensure_ascii=False)
            
        # 保存 Output (Spec)
        with open(os.path.join(self.llm_log_dir, f"iter_{iteration:02d}_resp.json"), 'w', encoding='utf-8') as f:
            json.dump(response_dict, f, indent=2, ensure_ascii=False)

    def log_metrics(self, data: dict):
        """追加一行数据到 CSV"""
        row = [
            data.get("iteration"),
            f"{data.get('pos_x'):.4f}",
            f"{data.get('pos_y'):.4f}",
            f"{data.get('pos_z'):.4f}",
            f"{data.get('max_temp'):.2f}",
            f"{data.get('min_dist_rib'):.2f}",
            data.get("is_safe"),
            f"{data.get('solver_cost', 0):.4f}",
            len(data.get("ai_reasoning", ""))
        ]
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
    def save_summary(self, status, total_iter):
        """生成最终报告"""
        summary_path = os.path.join(self.run_dir, "report.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# Optimization Report\n")
            f.write(f"- **Date**: {datetime.now()}\n")
            f.write(f"- **Status**: {status}\n")
            f.write(f"- **Total Iterations**: {total_iter}\n")
            f.write(f"- **Log Path**: `{self.run_dir}`\n")
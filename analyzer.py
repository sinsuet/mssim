# analyzer.py
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def render_dashboard(run_dir):
    """
    读取实验数据，生成工程仪表盘图片
    """
    csv_path = os.path.join(run_dir, "evolution_trace.csv")
    save_path = os.path.join(run_dir, "design_dashboard.png")
    
    if not os.path.exists(csv_path):
        print(f"⚠️ Data file not found: {csv_path}")
        return

    # 1. 读取数据
    data = {
        "iter": [], "x": [], "z": [], 
        "temp": [], "dist": [], "cost": []
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data["iter"].append(int(row["iteration"]))
                data["x"].append(float(row["pos_x"]))
                data["z"].append(float(row["pos_z"]))
                data["temp"].append(float(row["max_temp"]))
                data["dist"].append(float(row["min_dist_rib"]))
                data["cost"].append(float(row["solver_cost"]))
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return

    # 2. 设置画布 (2x2 布局)
    plt.style.use('seaborn-v0_8-whitegrid') # 如果没有这个style，可删掉或换成 'ggplot'
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Satellite Design Evolution Report\n{os.path.basename(run_dir)}', fontsize=16)

    # --- 子图 1: 演化轨迹 (Trajectory) ---
    ax1 = axs[0, 0]
    # 绘制环境
    ax1.axvline(x=10.0, color='gray', linestyle='-', linewidth=3, label='Rib (Wall)')
    ax1.axvspan(7.0, 10.0, color='gray', alpha=0.2, label='Clash Zone (<3mm)')
    ax1.scatter(0, 20, c='orange', s=200, marker='*', label='Heat Source')
    
    # 绘制轨迹
    ax1.plot(data["x"], data["z"], 'b--o', alpha=0.7, label='Path')
    ax1.scatter(data["x"][0], data["z"][0], c='green', s=100, label='Start')
    ax1.scatter(data["x"][-1], data["z"][-1], c='red', s=100, marker='P', label='End')
    
    # 标注点
    for i, txt in enumerate(data["iter"]):
        ax1.annotate(f"Iter{txt}", (data["x"][i], data["z"][i]), xytext=(5, 5), textcoords='offset points')

    ax1.set_title("Trajectory (X-Z Plane)")
    ax1.set_xlabel("Position X (mm)")
    ax1.set_ylabel("Position Z (mm)")
    ax1.set_xlim(-5, 15)
    ax1.set_ylim(10, 25)
    ax1.legend(loc='upper left')

    # --- 子图 2: 温度收敛曲线 (Thermal Convergence) ---
    ax2 = axs[0, 1]
    ax2.plot(data["iter"], data["temp"], 'r-o', linewidth=2)
    ax2.axhline(y=50.0, color='red', linestyle='--', label='Limit (50C)')
    ax2.fill_between(data["iter"], 0, 50, color='green', alpha=0.1, label='Safe Zone')
    
    ax2.set_title("Max Temperature vs Iteration")
    ax2.set_ylabel("Temp (°C)")
    ax2.set_xlabel("Iteration")
    ax2.legend()

    # --- 子图 3: 几何间隙曲线 (Geometry Clearance) ---
    ax3 = axs[1, 0]
    ax3.plot(data["iter"], data["dist"], 'g-o', linewidth=2)
    ax3.axhline(y=3.0, color='black', linestyle='--', label='Min Dist (3mm)')
    ax3.fill_between(data["iter"], 0, 3.0, color='red', alpha=0.1, label='Violation Zone')
    
    ax3.set_title("Distance to Rib vs Iteration")
    ax3.set_ylabel("Gap (mm)")
    ax3.set_xlabel("Iteration")
    ax3.legend()

    # --- 子图 4: 求解器代价 (Solver Cost) ---
    ax4 = axs[1, 1]
    ax4.plot(data["iter"], data["cost"], 'k-x', linestyle=':')
    ax4.set_title("Micro-Solver Cost Function")
    ax4.set_ylabel("Cost Value")
    ax4.set_xlabel("Iteration")

    # 3. 保存
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(save_path, dpi=150)
    plt.close()
    
    print(f"📊 Dashboard generated: {save_path}")
from enum import Enum
from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field, field_validator

# =============================================================================
# 1. 基础枚举定义 (Enums) - 对应 OpsGeo 和 SimEval 模块
# =============================================================================

class OperatorType(str, Enum):
    """
    定义系统支持的拓扑算子。
    Source: [cite: 188-194] OpsGeo Module
    """
    MOVE = "MOVE"              # 移动组件位置
    SWAP = "SWAP"              # 交换两个组件
    ADD_SURFACE = "ADD_SURFACE" # 增加辅助散热面
    ROTATE = "ROTATE"          # (预留) 旋转组件

class ViolationType(str, Enum):
    """
    违规类型定义，用于归因分析。
    Source:  Violation Attribution
    """
    THERMAL_OVERHEAT = "THERMAL_OVERHEAT"   # 过热
    GEOMETRY_CLASH = "GEOMETRY_CLASH"       # 干涉/碰撞
    MASS_LIMIT = "MASS_LIMIT"               # 超重
    PATH_BLOCK = "PATH_BLOCK"               # 路径/视场遮挡

# =============================================================================
# 2. 输出协议 (Output) - LLM -> Solver (SearchSpec)
# =============================================================================

class SearchAction(BaseModel):
    """
    单个优化动作定义。
    完全对齐文档 P11 JSON Schema [cite: 241-247]
    """
    op_id: OperatorType = Field(..., description="算子ID，例如 'MOVE'")
    target_component: str = Field(..., description="操作的目标组件标识符，例如 'BAT_01'")
    
    # 搜索空间定义 (The Subspace)
    # LLM 不给具体值，只给范围，由 Solver 进行 Micro-Optimization [cite: 203]
    search_axis: Optional[str] = Field(None, description="搜索轴向 (X, Y, Z)，仅 MOVE 有效")
    bounds: List[float] = Field(..., min_items=2, max_items=2, description="参数搜索上下界 [min, max]")
    unit: str = Field("mm", description="单位，默认为 mm")
    
    # 辅助推理字段
    conflicts: List[str] = Field(default_factory=list, description="该动作试图解决的违规ID列表 [cite: 244]")
    hints: List[str] = Field(default_factory=list, description="给 Solver 的启发式建议，例如 'Try moving +Y' ")

    @field_validator('bounds')
    def check_bounds_order(cls, v):
        if v[0] > v[1]:
            raise ValueError(f"Bounds must be [min, max], got {v}")
        return v

class SearchSpec(BaseModel):
    """
    LLM 返回的完整搜索规格说明书。
    Source: [cite: 149] ContextPack -> LLM -> SearchSpec
    """
    plan_id: str = Field(..., description="本次决策的唯一追踪ID")
    reasoning_summary: str = Field(..., description="宏观策略的自然语言解释")
    actions: List[SearchAction] = Field(..., description="建议执行的动作序列")

# =============================================================================
# 3. 输入协议 (Input) - Solver/Sim -> LLM (ContextPack)
# =============================================================================

class ViolationItem(BaseModel):
    """
    结构化的违规描述
    """
    id: str = Field(..., description="违规项唯一ID")
    type: ViolationType
    description: str
    involved_components: List[str] = Field(..., description="涉及的组件列表")
    severity: float = Field(1.0, description="严重程度 (0-1)")

class ContextPack(BaseModel):
    """
    发送给 LLM 的物理状态包。
    Source: [cite: 172] ContextPack (Markdown + JSON)
    """
    design_iteration: int
    
    # 指标字典 (MetricsDict) 
    metrics: Dict[str, Union[float, str]] = Field(
        ..., 
        description="关键性能指标，如 {'max_temp': 65.0, 'mass': 12.5}"
    )
    
    # 违规列表 (Violations)
    violations: List[ViolationItem] = Field(default_factory=list)
    
    # 几何与物理摘要 (Readable Summary) [cite: 231]
    # "LLM 仅接收'可读摘要'，不接触底层网格"
    geometry_summary: str = Field(..., description="组件空间关系的自然语言描述")
    thermal_summary: str = Field(..., description="热流路径与热点分布的自然语言描述")
    
    # 历史轨迹 (Traceability) [cite: 180]
    history_trace: List[str] = Field(
        default_factory=list, 
        description="之前的尝试记录，防止循环。例如 ['Iter 10: Moved Bat_01 +X -> Failed']"
    )

    def to_markdown_prompt(self) -> str:
        """
        将结构化数据转换为 LLM 易读的 Markdown Prompt。
        这是 'Semantic Gatekeeper' 的关键步骤 [cite: 251]。
        """
        md = f"# Satellite Design State (Iter {self.design_iteration})\n\n"
        
        md += "## 1. Key Metrics (关键指标)\n"
        for k, v in self.metrics.items():
            md += f"- **{k}**: {v}\n"
            
        md += "\n## 2. Active Violations (当前违规)\n"
        if not self.violations:
            md += "None. Design is feasible.\n"
        for v in self.violations:
            md += f"- [**{v.type.value}**] (ID: {v.id})\n"
            md += f"  - Detail: {v.description}\n"
            md += f"  - Components: {', '.join(v.involved_components)}\n"
            
        md += "\n## 3. Physical Context (物理环境)\n"
        md += f"### Geometry\n{self.geometry_summary}\n"
        md += f"### Thermal\n{self.thermal_summary}\n"
        
        if self.history_trace:
            md += "\n## 4. History (Do not repeat failures)\n"
            for h in self.history_trace:
                md += f"- {h}\n"
                
        return md
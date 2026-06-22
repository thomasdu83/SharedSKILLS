# Web 展示层参考

QuantSystem Web 应用开发规范，包含 **FastAPI + Jinja2 架构**、**ECharts 图表规范**、**静态资源管理**与**专业量化配色**。默认视觉语言参考 `jpmorgan.com`：克制、机构化、薄分隔线、稀疏铜色强调，而不是 SaaS 落地页风格。页面默认使用中文简体，并优先只展示核心功能。

---

## 1. 技术栈

### 核心组件

- **后端**: FastAPI
- **模板**: Jinja2
- **图表**: ECharts（交互式，默认优先）

### 图表渲染优先级

除非用户明确指定其他技术栈，QuantSystem Web 图表默认按以下顺序选择：

1. **ECharts**：用于交互式图表、dashboard、tooltip、联动筛选、缩放、时间序列、散点图、分布图、热力图和图表矩阵。
2. **内联 SVG**：用于小型静态图、微型图表、自定义注释、紧凑图例或无需依赖的简单图形。
3. **Python 静态图**：仅在需要 Python 专属计算、特殊统计图、复杂离线生成或必须以静态审计图片交付时使用；先生成图片，再作为前端资源加载。

不要在 ECharts 能直接渲染的 Web 图表场景中默认使用 Python 生成图片。

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
```

---

## 2. 专业量化配色（Professional Quant）

### 默认品牌语气

QuantSystem 前端在未指定其他品牌风格时，默认采用 J.P. Morgan 网站风格的抽象化版本：

- 白色或极浅冷灰底
- 炭黑正文与低饱和深蓝辅助
- 铜色或古铜色作为少量强调色
- 细边框、直角或极小圆角、几乎无阴影
- 信息优先，避免营销横幅和装饰型卡片
- 默认中文简体文案
- 默认只保留核心操作和核心信息，不堆叠辅助功能

### 涨跌色规范

**中国市场惯例**: 红涨绿跌

```python
COLORS = {
    "rise": "#d62728",    # 上涨 - 红
    "fall": "#2ca02c",    # 下跌 - 绿
    "neutral": "#7f7f7f", # 平盘 - 灰
}
```

### 多系列图表调色板

Tableau-10 调色板（区分度高、专业感强）:

```python
CHART_PALETTE = [
    '#1f77b4',  # 蓝
    '#ff7f0e',  # 橙
    '#2ca02c',  # 绿
    '#d62728',  # 红
    '#9467bd',  # 紫
    '#8c564b',  # 棕
    '#e377c2',  # 粉
    '#7f7f7f',  # 灰
    '#bcbd22',  # 黄绿
    '#17becf',  # 青
]
```

### 页面推荐色板

```python
PAGE_COLORS = {
    "bg": "#f5f7f8",         # 极浅冷灰背景
    "paper": "#ffffff",      # 主内容面
    "ink": "#31373d",        # 正文主色
    "muted": "#66707a",      # 次级文字
    "line": "#d7dde2",       # 分隔线
    "navy": "#2f5e88",       # 深蓝辅助
    "copper": "#936846",     # 稀疏强调
}
```

### ECharts 配置模板

```javascript
option = {
    tooltip: {
        trigger: 'axis',  // 坐标轴触发（时间序列）
        axisPointer: {
            type: 'cross'  // 十字准星
        }
    },
    dataZoom: [
        {
            type: 'slider',    // 滑块缩放
            xAxisIndex: 0,
            filterMode: 'none'
        },
        {
            type: 'inside',    // 鼠标缩放
            xAxisIndex: 0,
            filterMode: 'none'
        }
    ],
    // ... 其他配置
};
```

---

## 3. 静态资源管理（本地优先）

### 使用本地 CDN

**禁止直接使用外部** CDN，统一使用本地资源:

```html
<!-- ✓ 正确 - 本地资源CDN -->
<script src="{{ url_for('vendor', path='echarts/5.4.3/echarts.min.js') }}"></script>
<link href="{{ url_for('vendor', path='bootstrap/5.3.2/css/bootstrap.min.css') }}" rel="stylesheet">

<!-- ✗ 错误 - 外部CDN（可能不可用） -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
```

### FastAPI 静态资源挂载

**关键**: 挂载顺序决定路由优先级，**具体路径必须在通用路径之前**

```python
import logging
from pathlib import Path
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# 中央资源目录（所有项目共享/central_assets/）
CENTRAL_ASSETS = Path("central_assets").resolve()

# 正确挂载顺序：具体在前，通用在后
if CENTRAL_ASSETS.exists():
    # 1. 先挂载具体路径 /static/vendor
    app.mount(
        "/static/vendor",
        StaticFiles(directory=str(CENTRAL_ASSETS)),
        name="vendor"  # name用于url_for
    )
    logger.info("Mounted central assets: %s", CENTRAL_ASSETS)
else:
    logger.warning("Central assets not found: %s", CENTRAL_ASSETS)

# 2. 后挂载项目静态资源 /static（如有需要）
# app.mount("/static", StaticFiles(directory="static"), name="static")
```

**反模式**:
```python
# ✗ 错误 - 挂载顺序颠倒导致路由被覆盖
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/vendor", StaticFiles(...), name="vendor")  # 永远无法命中
```

### Jinja2 模板引用

**统一使用 `url_for('vendor', path='...')`**:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>组合报告</title>
    
    <!-- ✓ 正确 - url_for调用 -->
    <link href="{{ url_for('vendor', path='bootstrap/5.3.2/css/bootstrap.min.css') }}" rel="stylesheet">
    <script src="{{ url_for('vendor', path='jquery/3.7.1/jquery.min.js') }}"></script>
    <script src="{{ url_for('vendor', path='echarts/5.4.3/echarts.min.js') }}"></script>
    
    <!-- ✗ 错误 - 硬编码路径 -->
    <script src="/static/vendor/echarts/5.4.3/echarts.min.js"></script>
</head>
<body>
    <!-- 内容 -->
</body>
</html>
```

---

## 4. 目录结构规范

```
QuantSystem/
├── central_assets/              # 中央静态资源（所有项目共享）
│   ├── bootstrap/
│   │   └── 5.3.2/
│   │       ├── css/
│   │       │   ├── bootstrap.min.css
│   │       │   └── bootstrap.min.css.map
│   │       └── js/
│   │           ├── bootstrap.bundle.min.js
│   │           └── bootstrap.bundle.min.js.map
│   ├── jquery/
│   │   └── 3.7.1/
│   │       ├── jquery.min.js
│   │       └── jquery.min.map
│   ├── echarts/
│   │   └── 5.4.3/
│   │       ├── echarts.min.js
│   │       └── echarts.min.js.map
│   └── ...
└── <project>/
    ├── main.py                   # FastAPI入口
    ├── templates/                # Jinja2模板
    └── static/                   # 项目专属静态资源
```

---

## 5. FastAPI 完整模板

```python
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="QuantSystem Web")
templates = Jinja2Templates(directory="templates")

# 中央静态资源挂载
CENTRAL_ASSETS = Path("central_assets").resolve()
if CENTRAL_ASSETS.exists():
    app.mount(
        "/static/vendor",
        StaticFiles(directory=str(CENTRAL_ASSETS)),
        name="vendor"
    )
    logger.info("Mounted central assets: %s", CENTRAL_ASSETS)
else:
    logger.warning("Central assets not found: %s", CENTRAL_ASSETS)


@app.get("/")
async def index(request: Request):
    """首页。"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "组合管理"}
    )


@app.get("/report/{scheme_id}")
async def report(request: Request, scheme_id: str):
    """方案报告页。"""
    data = load_scheme_data(scheme_id)
    
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "scheme_id": scheme_id,
            "data": data,
        }
    )


def load_scheme_data(scheme_id: str) -> dict:
    """加载方案数据（示例）。"""
    # 实际从数据库或文件加载
    return {
        "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "nav_values": [1.0, 1.02, 1.01],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 6. Jinja2 报告模板

```html
<!-- templates/report.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ scheme_id }} - 方案报告</title>
    
    <!-- Bootstrap CSS -->
    <link href="{{ url_for('vendor', path='bootstrap/5.3.2/css/bootstrap.min.css') }}" rel="stylesheet">
    
    <style>
        :root {
            --bg: #f5f7f8;
            --paper: #ffffff;
            --ink: #31373d;
            --muted: #66707a;
            --line: #d7dde2;
            --navy: #2f5e88;
            --copper: #936846;
        }
        body {
            background: var(--bg);
            color: var(--ink);
            font-family: Amplitude, "Helvetica Neue", Arial, sans-serif;
        }
        .chart-container {
            width: 100%;
            height: 500px;
            margin-bottom: 2rem;
            border: 1px solid var(--line);
            background: #fbfcfd;
        }
        .metric-card {
            text-align: center;
            padding: 1.5rem;
            border: 1px solid var(--line);
            border-radius: 0;
            box-shadow: none;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--navy);
        }
        .metric-value.positive { color: #d62728; }
        .metric-value.negative { color: #2ca02c; }
        .section-label {
            color: var(--copper);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <p class="section-label">Strategy Review</p>
        <h1>方案报告: {{ scheme_id }}</h1>
        
        <!-- 关键指标卡片 -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value positive">+12.5%</div>
                    <div>累计收益</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value">8.2%</div>
                    <div>年化波动</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value">1.52</div>
                    <div>夏普比率</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value negative">-3.2%</div>
                    <div>最大回撤</div>
                </div>
            </div>
        </div>
        
        <!-- ECharts图表 -->
        <div id="nav-chart" class="chart-container"></div>
    </div>
    
    <!-- jQuery -->
    <script src="{{ url_for('vendor', path='jquery/3.7.1/jquery.min.js') }}"></script>
    
    <!-- Bootstrap JS -->
    <script src="{{ url_for('vendor', path='bootstrap/5.3.2/js/bootstrap.bundle.min.js') }}"></script>
    
    <!-- ECharts -->
    <script src="{{ url_for('vendor', path='echarts/5.4.3/echarts.min.js') }}"></script>
    
    <script>
        // ECharts初始化
        const chartDom = document.getElementById('nav-chart');
        const myChart = echarts.init(chartDom);
        
        const option = {
            title: {
                text: '净值曲线',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['组合净值', '基准'],
                bottom: 10
            },
            dataZoom: [
                {
                    type: 'slider',
                    xAxisIndex: 0,
                    filterMode: 'none',
                    bottom: 40
                },
                {
                    type: 'inside',
                    xAxisIndex: 0,
                    filterMode: 'none'
                }
            ],
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: {{ data.dates | tojson }},
                axisLabel: {
                    rotate: 45
                }
            },
            yAxis: {
                type: 'value',
                name: '净值',
                axisLabel: {
                    formatter: '{value}'
                }
            },
            series: [
                {
                    name: '组合净值',
                    type: 'line',
                    data: {{ data.nav_values | tojson }},
                    itemStyle: {
                        color: '#1f77b4'
                    },
                    lineStyle: {
                        width: 2
                    },
                    showSymbol: false
                }
            ]
        };
        
        myChart.setOption(option);
        
        // 响应式调整
        window.addEventListener('resize', function() {
            myChart.resize();
        });
    </script>
</body>
</html>
```

---

## 7. 图表类型规范

### 净值曲线（Line Chart）

```javascript
const navChartOption = {
    title: { text: '净值曲线' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    dataZoom: [{ type: 'slider' }, { type: 'inside' }],
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    series: [{
        type: 'line',
        data: navValues,
        showSymbol: false,
        lineStyle: { width: 2 }
    }]
};
```

### 持仓饼图（Pie Chart）

```javascript
const holdingPieOption = {
    title: { text: '持仓分布', left: 'center' },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
        type: 'pie',
        radius: ['40%', '70%'],  // 环形图
        data: holdingData,
        label: {
            formatter: '{b}\n{d}%'
        }
    }]
};
```

### 收益柱状图（Bar Chart）

```javascript
const returnBarOption = {
    title: { text: '月度收益' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{
        type: 'bar',
        data: monthlyReturns,
        itemStyle: {
            color: function(params) {
                return params.value >= 0 ? '#d62728' : '#2ca02c';
            }
        }
    }]
};
```

---

## 8. 检查清单

Web 开发完成后检查：

- [ ] 静态资源目录: `QuantSystem/central_assets/`
- [ ] FastAPI 挂载顺序正确（ `/static/vendor`在 `/static`前）
- [ ] 模板使用 `url_for('vendor', path='...')` 引用资源
- [ ] 无任何外部 CDN 引用
- [ ] ECharts 配置 `tooltip` 和 `dataZoom`
- [ ] 颜色使用专业量化配色（红涨绿跌）
- [ ] 页面风格符合 J.P. Morgan 式机构化语气：白底、细分隔线、稀疏铜色强调、极少阴影
- [ ] 首屏直接说明主题、样本区间、核心结论，不做营销型 hero
- [ ] 响应式布局（`window.resize` 处理）

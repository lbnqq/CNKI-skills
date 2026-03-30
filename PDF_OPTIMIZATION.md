# CNKI下载器 - PDF优先优化说明

## 🎯 优化目标

将PDF格式设为**默认且核心**的下载格式，确保用户优先获得PDF格式的论文。

## 📝 更新内容

### 1. 配置文件更新 (`src/config.py`)

在 `DownloadSettings` 类中添加PDF相关配置：

```python
@dataclass
class DownloadSettings:
    """下载设置"""
    # ... 原有配置 ...

    # PDF下载策略（核心配置）
    pdf_preferred: bool = True  # 优先下载PDF格式（默认true）
    pdf_only: bool = False  # 仅下载PDF（false时PDF不可用降级到CAJ）
    skip_paid_papers: bool = True  # 跳过需要付费的论文
```

### 2. 浏览器操作更新 (`src/cnki_browser.py`)

#### 2.1 构造函数添加PDF参数

```python
def __init__(
    self,
    # ... 原有参数 ...
    pdf_preferred: bool = True,  # PDF优先下载
    pdf_only: bool = False,  # 仅下载PDF模式
):
    # ... 原有代码 ...
    self.pdf_preferred = pdf_preferred
    self.pdf_only = pdf_only
```

#### 2.2 下载逻辑优化

实现三种下载策略：

**策略1: PDF专用模式** (`pdf_only=true`)
- 仅查找PDF下载按钮
- 未找到PDF时跳过该论文
- 日志：`"PDF专用模式：仅查找PDF下载按钮..."`

**策略2: PDF优先模式** (`pdf_preferred=true`, `pdf_only=false`) - **默认**
- 优先查找PDF下载按钮
- PDF不可用时降级到CAJ
- 日志：`"PDF优先模式：优先查找PDF下载按钮..."`

**策略3: CAJ优先模式** (不推荐)
- 仅用于向后兼容

### 3. 下载器更新 (`src/downloader.py`)

在创建 `CNKIBrowser` 实例时传递PDF配置：

```python
browser = CNKIBrowser(
    # ... 原有参数 ...
    pdf_preferred=self.config.download.pdf_preferred if self.config else True,
    pdf_only=self.config.download.pdf_only if self.config else False,
)
```

### 4. 文档更新

#### 4.1 skill.json

- 版本号更新为 `1.1.0`
- 描述添加"默认PDF格式下载"
- capabilities中添加"【核心】默认PDF格式下载"
- configuration.schema中添加PDF相关配置项
- changelog记录本次更新

#### 4.2 README.md

- 标题下方添加**默认PDF格式下载**说明
- 特性部分第一条强调PDF优先
- 配置说明添加PDF下载策略章节
- 详细说明三种PDF下载策略

## 🚀 使用效果

### 默认行为（无需配置）

用户直接使用即可享受PDF优先下载：

```
用户: 下载3篇关于人工智能的学位论文

系统:
✓ PDF优先模式已启用
✓ 优先查找PDF下载按钮
✓ 找到PDF下载按钮
```

### PDF专用模式（可选）

如需仅下载PDF格式，修改配置：

```json
{
  "download_settings": {
    "pdf_preferred": true,
    "pdf_only": true
  }
}
```

## 📊 版本对比

| 项目 | v1.0.0 | v1.1.0 |
|------|--------|--------|
| 默认格式 | CAJ优先 | **PDF优先** |
| PDF支持 | 可选 | **默认启用** |
| 降级策略 | 无 | PDF→CAJ自动降级 |
| 配置选项 | 基础 | 添加PDF策略配置 |

## ✅ 验证清单

- [x] 配置文件添加PDF相关参数
- [x] 浏览器类支持PDF配置
- [x] 下载器传递PDF配置
- [x] 实现PDF优先下载逻辑
- [x] 实现PDF专用模式
- [x] 更新skill.json元数据
- [x] 更新README.md文档
- [x] 添加详细的PDF策略说明

## 📅 更新日期

2026-03-30

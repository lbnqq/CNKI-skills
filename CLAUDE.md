# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 CNKI（中国知网）论文批量下载器的 Claude Skill，使用 Python + Playwright 实现浏览器自动化，支持从 CNKI 批量下载 10 种文献类型的学术论文。

**核心架构**：异步并发下载（默认 3 个任务同时），基于 Playwright 的浏览器自动化，模块化设计。

---

## 快速参考

### 核心命令

```bash
# 安装依赖
pip install playwright
playwright install chromium

# 测试输入解析器
python src/parser.py

# 运行完整测试
python src/main.py

# 测试单次下载
python test_download.py
```

### 项目结构

```
src/
├── models.py           # 数据模型 (DownloadRequest, Paper, DownloadResult, DownloadSummary)
├── parser.py           # 自然语言输入解析器
├── config.py           # 配置管理 (~/.cnki_downloader/config.json)
├── cnki_browser.py     # CNKI 浏览器自动化操作
├── downloader.py       # 并发下载器 (asyncio.Semaphore 控制)
├── utils.py            # 工具函数 (文件名清理、目录管理、日志)
└── main.py             # 主入口 (CNKIPaperDownloaderSkill 类)
```

---

## 架构说明

### 模块依赖关系

```
main.py (CNKIPaperDownloaderSkill)
  ├─ parser.py (InputParser) - 解析自然语言输入
  │   └─ models.py (DownloadRequest, DocumentType)
  ├─ downloader.py (CNKIDownloader) - 并发下载管理
  │   ├─ cnki_browser.py (CNKIBrowser) - 浏览器操作
  │   └─ models.py (Paper, DownloadResult, DownloadSummary)
  ├─ config.py (ConfigManager) - 配置加载
  └─ utils.py - 工具函数
```

### 核心数据流

1. **用户输入** → `InputParser.parse()` → `DownloadRequest`
2. **DownloadRequest** → `CNKIDownloader.download_from_request()` → `DownloadSummary`
3. **CNKIBrowser** 执行实际的浏览器操作（导航、检索、下载）

### 关键设计模式

- **单例模式**：`get_skill()` 返回全局唯一的 Skill 实例
- **数据类**：所有数据结构使用 `@dataclass` 定义
- **异步并发**：使用 `asyncio.Semaphore` 控制并发数（默认 3）
- **多选择器策略**：CNKI 操作使用多个 CSS 选择器提高容错性

---

## 开发指南

### 修改文献类型映射

编辑 `src/parser.py` 中的 `DOC_TYPE_ALIASES` 字典：

```python
DOC_TYPE_ALIASES = {
    "学术期刊": ["期刊", "期刊文章", "journal", ...],
    "学位论文": ["学位", "硕博论文", "thesis", ...],
    # ... 添加新的别名映射
}
```

### 更新浏览器选择器

CNKI 页面结构变化时，修改 `src/cnki_browser.py` 中的选择器列表：

```python
# 示例：文献类型选择器
DOC_TYPE_SELECTORS = [
    "div.docType-wrap a[data-name='{}']",
    "div.doc-type-tab a[title='{}']",
    # 添加新的备用选择器
]
```

### 调整并发配置

编辑 `~/.cnki_downloader/config.json`：

```json
{
  "download_settings": {
    "max_concurrent": 5,  // 修改并发数
    "timeout": 60000      // 修改超时时间
  }
}
```

### 添加新的错误代码

在 `src/utils.py` 中定义错误，并在 `src/cnki_browser.py` 中使用：

```python
raise CnkiDownloadError(
    error_code="E010",
    message="新的错误描述",
    paper_title=paper.title
)
```

---

## 支持的文献类型

| 类型 | 标识符 | CNKI 参数 |
|------|--------|----------|
| 学术期刊 | `ACADEMIC_JOURNAL` | `YZ` |
| 学位论文 | `DISSERTATION` | `CDMD` |
| 会议 | `CONFERENCE` | `CJFD` |
| 报纸 | `NEWSPAPER` | `CCND` |
| 年鉴 | `YEARBOOK` | `CYFD` |
| 专利 | `PATENT` | `SCOD` |
| 标准 | `STANDARD` | `SDSC` |
| 成果 | `ACHIEVEMENT` | `CPRD` |
| 学术辑刊 | `JOURNAL_COLLECTION` | `SZPD` |
| 图书 | `BOOK` | `BOOK` |
| 文库 | `WENKU` | `WENKU` |

---

## 常见任务

### 测试单个模块

```bash
# 测试解析器
python -c "from src.parser import InputParser; p = InputParser(); print(p.parse('下载5篇AI论文到 D:\\test\\'))"

# 测试配置加载
python -c "from src.config import ConfigManager; c = ConfigManager(); print(c.get())"

# 测试文件名清理
python -c "from src.models import Paper; p = Paper(title='测试/文件:名?'); print(p.get_filename())"
```

### 运行完整下载测试

```python
from src.main import get_skill
import asyncio

skill = get_skill()
result = asyncio.run(skill.download_papers(
    "帮我下载1篇测试论文到 D:\\test\\"
))
print(result)
```

### 查看日志

日志位置：`~/cnki_downloader_logs/`

### 调试浏览器操作

在 `src/cnki_browser.py` 中设置 `headless=False` 可看到浏览器窗口：

```python
browser = await playwright.chromium.launch(headless=False)
```

---

## 已知限制

1. **CNKI 页面结构依赖**：选择器可能随 CNKI 更新失效
2. **并发限制**：过高并发可能被 CNKI 限制 IP
3. **付费论文**：需要权限的论文会自动跳过
4. **网络依赖**：完全依赖网络稳定性

---

## 配置文件位置

| 系统 | 配置文件 |
|------|---------|
| Windows | `%USERPROFILE%\.cnki_downloader\config.json` |
| Linux/Mac | `~/.cnki_downloader/config.json` |

---

## 关键文件路径

- **主入口**：`src/main.py` - `CNKIPaperDownloaderSkill` 类
- **输入解析**：`src/parser.py` - `InputParser` 类
- **浏览器操作**：`src/cnki_browser.py` - `CNKIBrowser` 类
- **并发下载**：`src/downloader.py` - `CNKIDownloader` 类
- **数据模型**：`src/models.py` - 所有数据类定义
- **Skill 配置**：`skill.json` - Skill 元数据
- **用户文档**：`README.md` - 详细使用说明

---

## 调用示例

```python
# 方式1：自然语言接口
from src.main import get_skill
skill = get_skill()
result = await skill.download_papers("下载5篇AI论文到 D:\\papers\\")

# 方式2：简化接口
result = await skill.download(
    keyword="人工智能",
    count=5,
    doc_type="学位论文",
    save_dir="D:\\thesis\\"
)

# 方式3：同步包装
from src.main import download_papers_sync
result = download_papers_sync("下载5篇AI论文到 D:\\papers\\")
```

# CNKI下载器 - 工具文档

## 核心工具

### 1. Playwright (Python)

**官网**: https://playwright.dev/python/
**版本**: >=1.40.0

#### 概述

Playwright是一个现代化的浏览器自动化工具，支持Chromium、Firefox、WebKit三大浏览器。相比Selenium，Playwright具有更好的性能、更稳定的API和更强大的调试能力。

#### 在本技能中的应用

```python
from playwright.async_api import async_playwright, Page, Browser

# 启动浏览器
playwright = await async_playwright().start()
browser = await playwright.chromium.launch(
    headless=False,
    slow_mo=500  # 操作延迟500ms
)

# 创建上下文
context = await browser.new_context(
    accept_downloads=True,
    viewport={'width': 1366, 'height': 768},
    locale='zh-CN',
    timezone_id='Asia/Shanghai',
    user_agent='Mozilla/5.0 ...'
)

# 创建页面
page = await context.new_page()

# 导航到URL
await page.goto('https://www.cnki.net/', timeout=45000)

# 定位元素
search_box = await page.wait_for_selector('input[placeholder*="文献"]')

# 输入文本
await search_box.fill('人工智能')

# 点击按钮
await page.click('button:has-text("检索")')

# 等待加载
await page.wait_for_load_state('domcontentloaded')
await asyncio.sleep(10000)  # 固定等待10秒
```

#### 关键API说明

##### 页面导航

```python
# 导航到URL
await page.goto(url, timeout=45000)

# 等待页面加载状态
await page.wait_for_load_state('domcontentloaded')  # HTML解析完成
await page.wait_for_load_state('load')              # 所有资源加载完成
# 不推荐: await page.wait_for_load_state('networkidle')  # CNKI不适用
```

##### 元素定位

```python
# 等待元素出现
element = await page.wait_for_selector('selector', timeout=15000)

# 等待元素可见
await page.wait_for_selector('selector', state='visible', timeout=15000)

# 检查元素是否存在
if await page.locator('selector').count() > 0:
    # 元素存在
    pass

# 多选择器策略（提高容错性）
selectors = [
    'input[placeholder*="文献"]',
    'input[type="text"].search-input',
    'input[class*="search"]'
]
for selector in selectors:
    try:
        element = await page.wait_for_selector(selector, timeout=5000)
        break
    except:
        continue
```

##### 元素操作

```python
# 输入文本
await element.fill(text)

# 点击元素
await element.click()

# 获取文本
text = await element.text_content()

# 获取属性
href = await element.get_attribute('href')
```

##### 文件下载

```python
# 监听下载事件
async with page.expect_download() as download_info:
    await page.click('a:has-text("PDF下载")')
download = await download_info.value

# 保存文件
await download.save_as(file_path)
```

#### 最佳实践

1. **使用异步API**: 所有Playwright操作都是异步的，使用 `async/await`
2. **设置合理的超时**: CNKI页面慢，建议设置45000ms
3. **组合等待策略**: 固定等待 + 选择器等待
4. **多选择器备选**: 提高元素定位成功率
5. **避免networkidle**: CNKI页面持续加载，使用domcontentloaded

---

### 2. Python asyncio

**文档**: https://docs.python.org/3/library/asyncio.html

#### 概述

asyncio是Python的异步I/O库，用于编写并发代码。本技能使用asyncio实现异步浏览器操作和下载管理。

#### 在本技能中的应用

##### 异步等待

```python
import asyncio

# 异步睡眠（不阻塞事件循环）
await asyncio.sleep(10)  # 等待10秒

# 与time.sleep的区别
# time.sleep(10)  # 阻塞整个线程
# asyncio.sleep(10)  # 只等待当前协程，其他协程可继续执行
```

##### 异步上下文管理器

```python
# 使用async with管理资源
async with browser:
    # 执行操作
    await page.goto(url)
    # 自动关闭浏览器
```

##### 并发控制

```python
# 使用Semaphore控制并发数
semaphore = asyncio.Semaphore(3)  # 最多3个并发

async def download_paper(paper):
    async with semaphore:
        # 获取信号量
        result = await do_download(paper)
        # 释放信号量
        return result
```

##### 串行执行

```python
# 串行执行任务（本技能采用的方式）
results = []
for task in tasks:
    result = await task  # 等待任务完成
    results.append(result)
```

##### 异常处理

```python
try:
    await page.goto(url)
except TimeoutError:
    print("页面加载超时")
except Exception as e:
    print(f"发生错误: {e}")
```

#### 最佳实践

1. **所有I/O操作使用异步**: 网络、文件操作都用async版本
2. **合理使用asyncio.sleep**: 不要用time.sleep
3. **串行优于并发**: 对于CNKI这种慢速网站，串行更稳定
4. **完善异常处理**: 捕获并记录所有异常

---

### 3. pathlib

**文档**: https://docs.python.org/3/library/pathlib.html

#### 概述

pathlib提供了面向对象的文件系统路径操作，比os.path更直观、更安全。

#### 在本技能中的应用

```python
from pathlib import Path

# 创建路径对象
download_dir = Path("D:/papers")

# 创建目录
download_dir.mkdir(parents=True, exist_ok=True)

# 检查路径是否存在
if download_dir.exists():
    print("目录存在")

# 连接路径
file_path = download_dir / "论文.pdf"

# 获取文件名
filename = file_path.name  # "论文.pdf"

# 获取父目录
parent = file_path.parent  # Path("D:/papers")

# 遍历目录
for file in download_dir.glob("*.pdf"):
    print(file)
```

#### 跨平台路径处理

```python
# pathilb自动处理路径分隔符
# Windows: C:\papers\test.pdf
# Linux/macOS: /home/user/papers/test.pdf

# 推荐方式：使用Path
path = Path("folder") / "subfolder" / "file.txt"

# 不推荐：使用字符串拼接
path = "folder/subfolder/file.txt"  # Windows兼容性问题
```

---

### 4. 数据类 (dataclasses)

**文档**: https://docs.python.org/3/library/dataclasses.html

#### 概述

dataclasses提供了一种简洁的方式来定义类，主要用于存储数据。

#### 在本技能中的应用

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Paper:
    """论文信息"""
    title: str
    authors: Optional[str] = None
    source: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None

    def get_filename(self) -> str:
        """获取文件名"""
        from src.utils import sanitize_filename
        return sanitize_filename(self.title)

@dataclass
class DownloadResult:
    """下载结果"""
    paper: Paper
    status: DownloadStatus
    file_path: Optional[Path] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def is_success(self) -> bool:
        """是否成功"""
        return self.status == DownloadStatus.SUCCESS
```

---

## 依赖安装

### 安装步骤

```bash
# 1. 安装Playwright
pip install playwright

# 2. 安装Chromium浏览器
playwright install chromium

# 3. 验证安装
python -c "from playwright.sync_api import sync_playwright; print('安装成功')"
```

### 系统要求

| 系统 | Python版本 | 浏览器 |
|------|-----------|--------|
| Windows 10/11 | 3.8+ | Chromium |
| macOS 10.15+ | 3.8+ | Chromium |
| Linux | 3.8+ | Chromium |

---

## 开发工具

### 调试技巧

#### 1. 使用非无头模式

```python
# 设置headless=False可以看到浏览器窗口
browser = await playwright.chromium.launch(headless=False)
```

#### 2. 添加日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("开始下载")
logger.debug(f"论文信息: {paper}")
logger.error("下载失败")
```

#### 3. 慢动作模式

```python
# slow_mo参数让每个操作延迟n毫秒
browser = await playwright.chromium.launch(slow_mo=1000)  # 1秒
```

#### 4. 截图调试

```python
# 在关键步骤截图
await page.screenshot(path="debug.png")
```

---

## 常见问题

### Q1: Playwright下载速度慢

**原因**: 浏览器启动需要时间，首次使用会下载浏览器

**解决**:
- 使用 `playwright install chromium` 预先下载
- 重用浏览器实例，不要频繁启动关闭

### Q2: 元素定位失败

**原因**: 页面结构变化或元素未加载

**解决**:
- 使用多个选择器备选
- 增加等待时间
- 检查页面是否完全加载

### Q3: 下载文件保存失败

**原因**: 目录不存在或没有权限

**解决**:
- 使用 `Path.mkdir(parents=True, exist_ok=True)`
- 检查目录写入权限

### Q4: 内存占用过高

**原因**: 浏览器实例未正确关闭

**解决**:
- 确保使用 `async with` 或手动关闭
- 定期重启浏览器（每下载20-30篇）

---

## 参考资料

- [Playwright Python文档](https://playwright.dev/python/)
- [Python asyncio文档](https://docs.python.org/3/library/asyncio.html)
- [Python pathlib文档](https://docs.python.org/3/library/pathlib.html)
- [CNKI官方网站](https://www.cnki.net/)

# CNKI下载器 - 经典文献

## 文献类型

### 1. CNKI官方使用指南

**文献**: 中国知网使用帮助文档
**来源**: https://www.cnki.net/

**核心要点**:
- CNKI支持11种文献类型的检索和下载
- 不同文献类型有不同的下载权限和格式
- 学位论文通常提供CAJ格式，部分提供PDF格式
- 期刊文章大部分提供PDF下载

**对本技能的指导意义**:
- 理解CNKI的文献分类体系
- 了解不同文献类型的下载限制
- 掌握PDF/CAJ格式的适用场景

---

### 2. 学术文献管理最佳实践

**文献**: [学术文献管理系统的设计与实现](https://example.com/paper-management)

**核心观点**:
- 文献命名应包含：标题、作者、年份、来源
- 文件名应避免特殊字符，确保跨平台兼容
- 建议使用清晰的目录结构组织文献
- 定期备份文献库

**对本技能的指导意义**:
- 实现了智能文件命名（基于论文标题）
- 自动清理特殊字符
- 支持用户自定义保存目录
- 文件冲突自动处理（添加序号）

---

### 3. 浏览器自动化测试最佳实践

**文献**: Playwright官方文档 - Best Practices
**来源**: https://playwright.dev/docs/best-practices

**核心要点**:
- 使用 `wait_for_selector` 而不是固定 `sleep`
- 优先使用 `data-testid` 等稳定选择器
- 避免使用 `networkidle`，改用 `domcontentloaded`
- 并发操作要考虑页面加载时间

**对本技能的指导意义**:
- 采用"固定等待 + 选择器等待"组合策略
- 使用多选择器备选方案提高稳定性
- 使用 `domcontentloaded` 代替 `networkidle`
- 改为串行下载避免并发超时问题

---

### 4. Python异步编程实践

**文献**: [Async IO in Python: A Complete Walkthrough](https://realpython.com/async-io-python/)

**核心观点**:
- `asyncio.sleep` 用于异步等待
- 使用 `async with` 管理资源
- `Semaphore` 用于控制并发数
- 异常处理要考虑异步上下文

**对本技能的指导意义**:
- 所有等待操作使用 `asyncio.sleep`
- 浏览器操作使用 `async with` 管理
- 使用 `Semaphore` 控制下载并发数
- 完善的异常捕获和日志记录

---

### 5. 反爬虫与反检测策略

**文献**: Web Scraping Anti-Bot Strategies

**核心要点**:
- 设置真实的 User-Agent
- 模拟真实用户的操作延迟
- 覆盖 `navigator.webdriver` 属性
- 添加常用的 HTTP 头

**对本技能的指导意义**:
- 实现了完整的反检测配置
- 使用 `slow_mo=500ms` 操作延迟
- 注入 JavaScript 覆盖自动化特征
- 设置真实的语言和时区（zh-CN, Asia/Shanghai）

---

## 核心概念定义

### 文献类型（Document Types）

| 类型 | 说明 | 下载格式 |
|------|------|----------|
| 学术期刊 | 学术期刊文章 | PDF/CAJ |
| 学位论文 | 硕士/博士论文 | CAJ为主，部分PDF |
| 会议 | 会议论文集 | PDF/CAJ |
| 报纸 | 报纸文章 | PDF/CAJ |
| 年鉴 | 统计年鉴 | PDF/Excel |
| 专利 | 专利文档 | PDF |
| 标准 | 国家/行业标准 | PDF |
| 成果 | 科技成果 | PDF |
| 辑刊 | 学术辑刊 | PDF/CAJ |
| 图书 | 电子图书 | PDF/CAJ |
| 文库 | 知网文库 | PDF |

### 检索策略（Search Strategies）

1. **简单检索**: 直接输入关键词
2. **高级检索**: 使用检索式（字段名+关键词）
3. **二次检索**: 在结果基础上进一步筛选

### 下载流程（Download Process）

```
1. 解析用户输入 → 提取关键词、文献类型、数量
2. 打开CNKI首页 → 等待10秒确保加载
3. 选择文献类型 → 等待页面切换
4. 执行检索 → 等待10秒加载结果
5. 提取论文列表 → 获取标题、作者、来源
6. 串行下载 → 每篇间隔5秒
7. 生成报告 → 统计成功/失败/跳过
```

---

## 关键经验总结

### CNKI页面加载规律

| 操作 | 平均加载时间 | 推荐等待时间 |
|------|-------------|-------------|
| 首页加载 | 8-12秒 | 10秒 |
| 搜索结果 | 10-15秒 | 10秒 |
| 详情页 | 8-10秒 | 8秒 |
| PDF下载准备 | 3-5秒 | 5秒 |

### 超时配置建议

```yaml
页面导航超时: 45000ms (45秒)
元素定位超时: 15000ms (15秒)
下载操作超时: 30000ms (30秒)
整体任务超时: 300000ms (5分钟)
```

### 稳定性优化策略

1. **固定等待 > 智能等待**: CNKI页面慢，先固定等待10秒
2. **串行 > 并发**: 避免复杂并发导致的超时
3. **多选择器策略**: 提高元素定位成功率
4. **操作确认**: 每步操作后验证状态
5. **容错设计**: 失败后继续，不中断整体流程

---

## 参考资料

- [CNKI官方网站](https://www.cnki.net/)
- [Playwright Python文档](https://playwright.dev/python/)
- [Python asyncio文档](https://docs.python.org/3/library/asyncio.html)
- [学术文献管理规范](https://example.org/scholarly-paper-management)

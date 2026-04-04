# CNKI论文批量下载器

> 一个自动化从中国知网(CNKI)批量下载学术论文的Claude Skill
>
> **🔥 默认PDF格式下载** - 优先下载PDF，PDF不可用时自动降级到CAJ

## ✨ 特性

- 📄 **PDF优先** - 默认下载PDF格式（兼容性更好），PDF不可用时自动降级到CAJ
- 🎯 **智能识别** - 支持自然语言输入，自动解析下载需求
- 📚 **全面覆盖** - 支持10种文献类型：期刊、学位论文、会议、报纸、年鉴、专利、标准、成果、辑刊、图书、文库
- 🚀 **高效下载** - 并发下载（默认3个任务同时进行），提升效率
- 📁 **智能命名** - 自动清理文件名，处理重名冲突
- ⚠️ **容错处理** - 完善的异常处理机制，自动跳过付费论文
- 📊 **详细报告** - 提供完整的下载统计和日志

## 📦 安装

### 前置要求

- Python 3.8+
- Claude Code
- 网络连接

### 安装步骤

1. **克隆或下载本项目**

```bash
git clone https://github.com/yourusername/cnki-downloader-skill.git
cd cnki-downloader-skill
```

2. **安装Python依赖**

```bash
pip install playwright
playwright install chromium
```

3. **安装到Claude Code**

```bash
# 复制到Claude Skills目录
cp -r cnki-downloader-skill ~/.claude/skills/

# 或者，如果在Windows上：
xcopy /E /I cnki-downloader-skill %USERPROFILE%\.claude\skills\cnki-downloader-skill
```

4. **重启Claude Code**

## 🚀 使用方法

### 基础用法

在Claude Code中，直接用自然语言描述下载需求：

```
用户: 帮我下载5篇跟"人工智能"相关的学位论文到 D:\papers\

Claude: 好的，我来帮您下载论文。

🔍 正在解析输入...
   关键词: 人工智能
   文献类型: 学位论文
   数量: 5篇
   保存目录: D:\papers\

🌐 正在打开CNKI...
✓ 已访问首页

📚 正在选择文献类型...
✓ 已选择"学位论文"

🔎 正在执行检索...
✓ 已检索"人工智能"

📥 正在下载论文...
   [████████░░░░░░░░░░] 40% (2/5)
   ✅ 智能赋影，融合创新.pdf
   ✅ 人工智能在医疗诊断中的应用.pdf
   ⏳ 正在下载第3篇...

✅ 下载完成！

📊 下载统计:
   总计: 5篇
   成功: 5篇
   跳过: 0篇

📁 保存位置: D:\papers\
```

### 更多示例

```
✅ 下载10篇关于机器学习的期刊文章到 C:\docs\

✅ 帮我下20个会议论文，主题是深度学习，保存到 ~/papers/

✅ 下载5篇专利，关键词是区块链，到 D:\patents\

✅ 下载十篇硕博论文到 D:\thesis\
```

### 命令格式

```
下载 {数量} 篇关于 "{关键词}" 的 {文献类型} 到 {目录}
```

**必需参数：**
- **数量** - 要下载的论文篇数
- **关键词** - 检索关键词（用引号括起来）
- **文献类型** - 论文类型（见下方支持的类型）
- **目录** - 保存路径

### 支持的文献类型

| 标准名称 | 别名/变体 |
|---------|-----------|
| 学术期刊 | 期刊、期刊文章、期刊论文、journal、核心期刊 |
| 学位论文 | 学位、硕博论文、硕士论文、博士论文、thesis、dissertation |
| 会议 | 会议、会议论文、会议文章、conference、proceedings |
| 报纸 | 报纸、报纸文章、newspaper |
| 年鉴 | 年鉴、统计年鉴、yearbook |
| 专利 | 专利、patent、专利文献 |
| 标准 | 标准、standard、标准文献、规范 |
| 成果 | 成果、科技成果、achievements |
| 学术辑刊 | 辑刊 |
| 图书 | 图书、图书章节、book |
| 文库 | 文库、知网文库、wenku |

**默认值：** 如果不指定文献类型，默认使用"学术期刊"

## ⚙️ 配置

### 配置文件

配置文件位置：`~/.cnki_downloader/config.json`

### 默认配置

```json
{
  "download_settings": {
    "default_dir": "~/Downloads/CNKI",
    "max_concurrent": 3,
    "timeout": 30000,
    "retry_times": 2,
    "pdf_preferred": true,
    "pdf_only": false,
    "skip_paid_papers": true
  },
  "browser_settings": {
    "headless": false,
    "slow_mo": 100
  },
  "file_settings": {
    "sanitize_filename": true,
    "max_filename_length": 200,
    "conflict_strategy": "append_number"
  }
}
```

### 配置说明

| 设置 | 说明 | 默认值 |
|------|------|--------|
| **PDF下载策略** |
| `pdf_preferred` | **优先下载PDF格式**（核心配置） | `true` |
| `pdf_only` | **仅下载PDF**（false时PDF不可用降级到CAJ） | `false` |
| **基础设置** |
| `default_dir` | 默认下载目录 | `~/Downloads/CNKI` |
| `max_concurrent` | 最大并发下载数 | `3` |
| `timeout` | 页面加载超时（毫秒） | `30000` (30秒) |
| `skip_paid_papers` | 跳过需要付费的论文 | `true` |
| **浏览器设置** |
| `headless` | 是否无头模式（不显示浏览器） | `false` |
| `slow_mo` | 操作延迟（毫秒） | `100` |
| **文件设置** |
| `sanitize_filename` | 是否清理文件名特殊字符 | `true` |
| `max_filename_length` | 最大文件名长度 | `200` |

### PDF下载策略说明

本下载器**默认使用PDF优先策略**：

1. **PDF优先模式**（默认）：`pdf_preferred=true, pdf_only=false`
   - 优先尝试下载PDF格式
   - PDF不可用时自动降级到CAJ格式
   - 适合：需要获取文献，对格式要求不严格

2. **PDF专用模式**：`pdf_preferred=true, pdf_only=true`
   - 仅下载PDF格式
   - PDF不可用时跳过该论文
   - 适合：必须使用PDF格式的场景

### 自定义配置

1. 编辑配置文件：`~/.cnki_downloader/config.json`

2. 修改需要的设置：

```json
{
  "download_settings": {
    "max_concurrent": 5,  // 增加并发数
    "timeout": 60000       // 增加超时时间
  },
  "browser_settings": {
    "headless": true      // 使用无头模式
  }
}
```

3. 保存并重启Claude Code

## 📖 进阶使用

### 下载大量论文

```
下载100篇关于"数据科学"的学术期刊到 D:\DataScience\
```

**提示：**
- 大量下载可能需要较长时间
- 建议分批下载，避免请求过于频繁

### 处理付费论文

遇到需要付费的论文时，Skill会自动跳过并记录原因：

```
⚠️ 未成功下载 (2篇):
   ⚠️ 高级算法综述.pdf - 原因: 需要付费权限
   ⚠️ 前沿技术研究.pdf - 原因: 需要付费权限
```

**解决方法：**
- 确保你的CNKI账号已登录
- 检查账号是否具有下载权限
- 机构用户通常有更多权限

### 文件命名规则

下载的文件名基于论文标题，并自动处理：

1. **清理特殊字符** - 将 `\ / : * ? " < > |` 替换为 `_`
2. **限制长度** - 最大200字符，超长则截断
3. **处理重名** - 自动添加序号后缀（如：`论文_1.pdf`）

### 查看日志

日志文件位置：`~/cnki_downloader_logs/`

日志文件包含：
- 操作过程记录
- 错误信息
- 下载统计

## 🔧 故障排除

### 常见问题

#### Q: 提示"无法定位搜索框"？

**可能原因：**
- 网络连接问题
- CNKI页面加载缓慢
- 页面结构已变化

**解决方法：**
1. 检查网络连接
2. 尝试手动访问 https://www.cnki.net/
3. 稍后重试
4. 查看错误日志

#### Q: 下载速度很慢？

**可能原因：**
- 网络速度慢
- CNKI服务器响应慢
- 并发数设置过高

**解决方法：**
1. 检查网络连接
2. 减少并发数配置（改为1或2）
3. 避开高峰时段（如工作日白天）

#### Q: 部分论文下载失败？

**可能原因：**
- 论文需要付费权限
- 机构IP未认证
- 临时网络故障

**解决方法：**
1. 检查是否已登录CNKI账号
2. 确认账号权限
3. 查看跳过论文的具体原因
4. 稍后重试失败的论文

#### Q: 文件名乱码？

**可能原因：**
- 系统编码问题

**解决方法：**
1. 确保系统使用UTF-8编码
2. 检查系统语言设置

### 错误代码

| 代码 | 说明 | 处理建议 |
|------|------|---------|
| E001 | 无法解析用户输入 | 检查输入格式 |
| E002 | 网络连接失败 | 检查网络连接 |
| E003 | 页面加载超时 | 刷新重试 |
| E004 | 无法定位元素 | 检查页面结构 |
| E005 | 下载失败 | 重试或跳过 |
| E006 | 权限不足 | 登录账号 |
| E007 | 磁盘空间不足 | 清理磁盘空间 |
| E008 | 目录权限不足 | 检查目录权限 |
| E009 | 文件名冲突 | 自动处理或询问用户 |

## 📝 开发

### 项目结构

```
cnki-downloader-skill/
├── skill.json                 # Skill配置
├── README.md                  # 本文档
├── src/
│   ├── __init__.py
│   ├── main.py               # 主入口
│   ├── config.py             # 配置管理
│   ├── parser.py             # 输入解析器
│   ├── cnki_browser.py       # 浏览器操作
│   ├── downloader.py         # 下载器
│   ├── models.py             # 数据模型
│   └── utils.py              # 工具函数
├── tests/                    # 测试
└── docs/                     # 文档
```

### 运行测试

```bash
# 测试解析器
python src/parser.py

# 测试主程序
python src/main.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发计划

- [ ] 支持按年份、影响因子筛选
- [ ] 添加断点续传功能
- [ ] 支持批量任务
- [ ] 添加图形界面（可选）
- [ ] 支持代理服务器
- [ ] OCR识别扫描版论文

## 📄 许可证

MIT License

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化框架
- [CNKI](https://www.cnki.net/) - 中国知网

## 📮 联系

- 问题反馈：https://github.com/yourusername/cnki-downloader-skill/issues
- 邮箱：your.email@example.com

---

**Made with ❤️ by Claude**

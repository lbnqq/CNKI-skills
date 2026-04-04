# CNKI 论文下载器 Skill 打包说明

## 压缩包信息

- **文件名**: `cnki-paper-downloader-v5.1.0.zip`
- **版本**: 5.1.0-cli-native
- **大小**: 38KB
- **打包日期**: 2026-04-03

## 目录结构

```
cnki-paper-downloader/
├── SKILL.md          # 核心定义文件（必需，包含YAML frontmatter）
├── scripts/          # 可执行脚本目录
│   ├── __init__.py
│   ├── main.py       # 主入口
│   ├── parser.py     # 自然语言解析器
│   ├── config.py     # 配置管理
│   ├── cnki_browser.py  # 浏览器自动化操作
│   ├── downloader.py # 并发下载器
│   ├── models.py     # 数据模型
│   └── utils.py      # 工具函数
└── references/       # 参考文档目录
    ├── classic-literature.md  # 经典文献
    ├── concepts.md           # 核心概念
    └── tools.md              # 工具文档
```

## 安装方法

### Claude Code 安装

```bash
# 解压到 Claude Code skills 目录
unzip cnki-paper-downloader-v5.1.0.zip -d ~/.claude/skills/
mv ~/.claude/skills/cnki-paper-downloader-v5.1.0 ~/.claude/skills/cnki-paper-downloader

# 重启 Claude Code
```

### WorkBuddy 安装

```bash
# 解压到 WorkBuddy skills 目录
unzip cnki-paper-downloader-v5.1.0.zip -d ~/.workbuddy/skills/

# 重启 WorkBuddy
```

## 验证安装

安装后，在 Claude Code 中测试：

```
帮我下载1篇测试论文到 D:\test\
```

## 依赖要求

- Python >= 3.8
- Playwright >= 1.40.0
- Chromium 浏览器

安装依赖：

```bash
pip install playwright
playwright install chromium
```

## SKILL.md 格式说明

本 Skill 严格遵循 WorkBuddy Skill 格式规范：

```markdown
---
name: cnki-paper-downloader
description: CNKI论文批量下载器
allowed-tools: []
disable: false
---

# CNKI 论文下载器

详细指令...
```

## 特性说明

- ✅ **YAML frontmatter**: 包含必需的元数据
- ✅ **scripts 目录**: 包含所有 Python 执行脚本
- ✅ **references 目录**: 包含参考文档
- ✅ **指令性语言**: 使用第二人称，清晰易懂
- ✅ **精简结构**: SKILL.md 保持简洁，长篇内容在 references/

## 版本历史

- 5.1.0-cli-native (2026-04-03): 首次发布符合 WorkBuddy 标准的版本
  - 完整的 YAML frontmatter
  - 规范的目录结构
  - 11种文献类型支持
  - 串行稳定下载

## 许可证

MIT License

---

**打包完成！可以直接上传使用。**

"""
CNKI论文下载器 - 工具函数
提供各种辅助功能
"""

import re
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from src.models import Paper, ErrorLog


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    清理文件名中的非法字符

    Args:
        filename: 原始文件名
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    # 移除文件扩展名（如果有）
    name = Path(filename).stem

    # 替换非法字符
    illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in illegal_chars:
        name = name.replace(char, '_')

    # 替换全角符号
    name = name.replace('：', '_')
    name = name.replace('、', '_')
    name = name.replace('，', '_')
    name = name.replace('。', '_')
    name = name.replace('（', '_')
    name = name.replace('）', '_')
    name = name.replace('《', '_')
    name = name.replace('》', '_')

    # 清理多个连续的特殊字符
    name = re.sub(r'[_\-\.]{2,}', '_', name)

    # 清理多个空格
    name = '_'.join(name.split())

    # 去除首尾的特殊字符和空格
    name = name.strip('_.- ')

    # 限制长度
    if len(name) > max_length:
        name = name[:max_length-3] + '...'

    # 如果清理后为空，使用默认名称
    if not name:
        name = "unnamed"

    return name


def generate_unique_filename(filename: str, existing_files: List[Path]) -> str:
    """
    生成唯一文件名（处理重名）

    Args:
        filename: 期望的文件名
        existing_files: 已存在的文件列表

    Returns:
        唯一的文件名
    """
    name = Path(filename).stem
    ext = Path(filename).suffix

    # 检查是否已存在
    existing_names = [f.stem for f in existing_files]

    if name not in existing_names:
        return filename

    # 添加序号后缀
    counter = 1
    while True:
        new_name = f"{name}_{counter}"
        if new_name not in existing_names:
            return f"{new_name}{ext}"
        counter += 1

        # 防止无限循环
        if counter > 10000:
            # 使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{name}_{timestamp}{ext}"


def ensure_directory(directory: Path) -> bool:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径

    Returns:
        是否成功
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ 无法创建目录 {directory}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小（如：1.5 MB）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    格式化时间时长

    Args:
        seconds: 秒数

    Returns:
        格式化后的时长（如：2分15秒）
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分"


def setup_logging(log_dir: Path, level: str = "INFO") -> logging.Logger:
    """
    设置日志

    Args:
        log_dir: 日志目录
        level: 日志级别

    Returns:
        Logger对象
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建logger
    logger = logging.getLogger("cnki_downloader")
    logger.setLevel(getattr(logging, level.upper()))

    # 清除已有的处理器
    logger.handlers.clear()

    # 文件处理器
    log_file = log_dir / f"cnki_downloader_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def save_error_log(error_log: ErrorLog, log_dir: Path) -> None:
    """
    保存错误日志

    Args:
        error_log: 错误日志对象
        log_dir: 日志目录
    """
    try:
        log_dir.mkdir(parents=True, exist_ok=True)

        error_file = log_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(error_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(error_log.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"📍 错误日志已保存: {error_file}")
    except Exception as e:
        print(f"⚠️ 无法保存错误日志: {e}")


def generate_download_report(summary) -> str:
    """
    生成下载报告

    Args:
        summary: DownloadSummary对象

    Returns:
        格式化的报告文本
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("📊 下载统计:")
    report_lines.append(f"   总计: {summary.total}篇")
    report_lines.append(f"   成功: {summary.success_count}篇")
    report_lines.append(f"   跳过: {summary.skipped_count}篇")
    report_lines.append(f"   失败: {summary.failed_count}篇")

    if summary.files:
        report_lines.append(f"\n📁 保存位置: {summary.request.save_dir}")

        report_lines.append(f"\n📄 下载文件列表 ({len(summary.files)}篇):")
        for i, file_path in enumerate(summary.files, 1):
            report_lines.append(f"   ✅ {file_path.name}")

    if summary.skipped_count > 0 or summary.failed_count > 0:
        report_lines.append(f"\n⚠️ 未成功下载 ({summary.skipped_count + summary.failed_count}篇):")
        for result in summary.results:
            if not result.is_success():
                paper_info = result.paper.title[:50] + "..." if len(result.paper.title) > 50 else result.paper.title
                if result.error_message:
                    report_lines.append(f"   ⚠️ {paper_info} - 原因: {result.error_message}")
                else:
                    report_lines.append(f"   ⚠️ {paper_info}")

    elapsed = summary.get_elapsed_time()
    if elapsed:
        report_lines.append(f"\n⏱️  耗时: {format_duration(elapsed)}")

        speed = summary.get_speed()
        if speed:
            report_lines.append(f"🚀 平均速度: {speed:.1f}篇/分钟")

    report_lines.append("=" * 60)

    return "\n".join(report_lines)


def extract_paper_info_from_text(text: str) -> dict:
    """
    从文本中提取论文信息（备用方案）

    Args:
        text: 包含论文信息的文本

    Returns:
        论文信息字典
    """
    info = {
        "title": "",
        "authors": "",
        "source": "",
        "year": ""
    }

    # 提取标题（通常是最长的行）
    lines = text.strip().split('\n')
    if lines:
        # 找最长的非空行作为标题
        title_line = max((line for line in lines if line.strip()), key=len, default="")
        info["title"] = title_line.strip()

    # 提取年份（4位数字）
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        info["year"] = year_match.group(0)

    return info


def is_valid_download_directory(directory: Path) -> tuple[bool, Optional[str]]:
    """
    检查目录是否可用于下载

    Args:
        directory: 目录路径

    Returns:
        (是否有效, 错误信息)
    """
    # 检查是否存在
    if not directory.exists():
        # 尝试创建
        try:
            directory.mkdir(parents=True)
        except Exception as e:
            return False, f"无法创建目录: {e}"

    # 检查是否是目录
    if not directory.is_dir():
        return False, "路径不是一个目录"

    # 检查写入权限
    test_file = directory / f".write_test_{datetime.now().timestamp()}"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        return False, f"没有写入权限: {e}"

    # 检查磁盘空间（至少需要100MB）
    try:
        stat = disk_usage(str(directory))
        if stat.free < 100 * 1024 * 1024:
            return False, "磁盘空间不足（至少需要100MB）"
    except:
        pass  # 跳过磁盘空间检查

    return True, None


def disk_usage(path: str) -> object:
    """获取磁盘使用情况（跨平台）"""
    import shutil
    return shutil.disk_usage(path)


# 测试代码
if __name__ == "__main__":
    # 测试文件名清理
    test_filenames = [
        "人工智能/医学影像：应用与展望",
        "AI、ML、DL在医疗领域的应用**",
        "A" * 300,
        "正常文件名.pdf"
    ]

    print("文件名清理测试:")
    for filename in test_filenames:
        cleaned = sanitize_filename(filename)
        print(f"  原始: {filename[:50]}...")
        print(f"  清理: {cleaned}")
        print()

    # 测试唯一文件名生成
    print("\n唯一文件名测试:")
    existing = [Path("论文.pdf"), Path("论文_1.pdf")]
    new_name = generate_unique_filename("论文.pdf", existing)
    print(f"  期望: 论文.pdf")
    print(f"  生成: {new_name}")

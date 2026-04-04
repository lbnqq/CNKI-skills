"""
CNKI论文下载器 - 数据模型
定义所有核心数据结构
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """文献类型枚举"""
    ACADEMIC_JOURNAL = "学术期刊"
    DISSERTATION = "学位论文"
    CONFERENCE = "会议"
    NEWSPAPER = "报纸"
    YEARBOOK = "年鉴"
    PATENT = "专利"
    STANDARD = "标准"
    ACHIEVEMENT = "成果"
    JOURNAL_COLLECTION = "学术辑刊"
    BOOK = "图书"
    WENKU = "文库"


class DownloadStatus(Enum):
    """下载状态枚举"""
    PENDING = "待下载"
    DOWNLOADING = "下载中"
    SUCCESS = "成功"
    FAILED = "失败"
    SKIPPED = "跳过"


@dataclass
class DownloadRequest:
    """下载请求数据模型"""
    keyword: str                    # 检索关键词
    count: int                      # 下载数量
    doc_type: str                   # 文献类型（中文）
    save_dir: Path                  # 保存目录

    # 可选参数
    language: str = "CHS"           # 语言（默认中文）
    uniplatform: str = "NZKPT"      # 平台标识

    def __post_init__(self):
        """初始化后处理"""
        # 确保save_dir是Path对象
        if not isinstance(self.save_dir, Path):
            self.save_dir = Path(self.save_dir)

        # 确保count是正整数
        if self.count <= 0:
            raise ValueError("下载数量必须大于0")

        # 展开用户目录
        if str(self.save_dir).startswith("~"):
            self.save_dir = self.save_dir.expanduser()


@dataclass
class Paper:
    """论文信息数据模型"""
    title: str                      # 论文标题
    authors: Optional[str] = None   # 作者
    source: Optional[str] = None    # 来源（期刊/学位授予单位）
    year: Optional[str] = None      # 发表年份
    url: Optional[str] = None       # 详情页URL
    download_url: Optional[str] = None  # 下载链接

    # 文献类型
    doc_type: Optional[str] = None  # 文献类型
    abstract: Optional[str] = None  # 摘要
    keywords: Optional[List[str]] = None  # 关键词

    # 统计信息
    cite_count: Optional[int] = None    # 被引频次
    download_count: Optional[int] = None  # 下载频次

    def get_filename(self, sanitize: bool = True) -> str:
        """
        获取文件名

        Args:
            sanitize: 是否清理特殊字符

        Returns:
            文件名（不含路径）
        """
        title = self.title

        if sanitize:
            # 清理文件名中的非法字符
            illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for char in illegal_chars:
                title = title.replace(char, '_')

            # 清理全角符号
            title = title.replace('：', '_')
            title = title.replace('、', '_')
            title = title.replace('，', '_')
            title = title.replace('。', '_')

            # 清理多个空格
            title = '_'.join(title.split())

            # 限制长度（Windows限制255字符）
            max_length = 200
            if len(title) > max_length:
                title = title[:max_length-3] + '...'

        # 添加.pdf后缀
        return f"{title}.pdf"


@dataclass
class DownloadResult:
    """单篇论文下载结果"""
    paper: Paper                     # 论文信息
    status: DownloadStatus           # 下载状态
    file_path: Optional[Path] = None # 保存路径（成功时）
    error_message: Optional[str] = None  # 错误信息（失败时）
    download_time: Optional[float] = None  # 下载耗时（秒）

    def is_success(self) -> bool:
        """是否下载成功"""
        return self.status == DownloadStatus.SUCCESS


@dataclass
class DownloadSummary:
    """批量下载汇总"""
    request: DownloadRequest         # 原始请求
    total: int = 0                   # 总数
    success_count: int = 0           # 成功数
    failed_count: int = 0            # 失败数
    skipped_count: int = 0           # 跳过数

    results: List[DownloadResult] = field(default_factory=list)  # 所有结果
    files: List[Path] = field(default_factory=list)  # 成功下载的文件列表

    start_time: Optional[datetime] = None  # 开始时间
    end_time: Optional[datetime] = None    # 结束时间

    def add_result(self, result: DownloadResult):
        """添加一个下载结果"""
        self.results.append(result)
        self.total += 1

        if result.is_success():
            self.success_count += 1
            if result.file_path:
                self.files.append(result.file_path)
        elif result.status == DownloadStatus.SKIPPED:
            self.skipped_count += 1
        else:
            self.failed_count += 1

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100

    def get_elapsed_time(self) -> Optional[float]:
        """获取耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def get_speed(self) -> Optional[float]:
        """获取下载速度（篇/分钟）"""
        elapsed = self.get_elapsed_time()
        if elapsed and elapsed > 0 and self.success_count > 0:
            return (self.success_count / elapsed) * 60
        return None


@dataclass
class ErrorLog:
    """错误日志"""
    timestamp: datetime = field(default_factory=datetime.now)
    error_code: str = ""            # 错误代码
    error_message: str = ""         # 错误信息
    paper_title: Optional[str] = None   # 相关论文标题
    stack_trace: Optional[str] = None   # 堆栈跟踪
    context: Optional[dict] = None  # 上下文信息

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "paper_title": self.paper_title,
            "stack_trace": self.stack_trace,
            "context": self.context
        }

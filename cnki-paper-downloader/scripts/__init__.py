"""
CNKI论文下载器
一个自动化下载CNKI学术论文的Claude Skill
"""

__version__ = "1.0.0"
__author__ = "Claude"

from src.main import CNKIPaperDownloaderSkill, get_skill, download_papers_sync

__all__ = [
    "CNKIPaperDownloaderSkill",
    "get_skill",
    "download_papers_sync"
]

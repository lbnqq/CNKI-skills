"""
CNKI论文下载器 - 主入口
提供对外接口，整合所有模块
"""

import asyncio
import sys
from pathlib import Path

from src.parser import InputParser
from src.downloader import CNKIDownloader
from src.config import ConfigManager
from src.models import DownloadRequest
from src.utils import ensure_directory, setup_logging


class CNKIPaperDownloaderSkill:
    """CNKI论文下载器Skill"""

    def __init__(self):
        """初始化Skill"""
        # 加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get()

        # 初始化日志
        self.logger = setup_logging(
            self.config.logging.log_dir,
            self.config.logging.level
        )

        # 初始化解析器
        self.parser = InputParser(
            default_doc_type=self.config.defaults.doc_type
        )

        # 初始化下载器
        self.downloader = CNKIDownloader(config=self.config)

    async def download_papers(self, user_input: str) -> str:
        """
        下载论文（主接口）

        Args:
            user_input: 用户输入文本

        Returns:
            下载结果报告
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("收到下载请求")
            self.logger.info(f"用户输入: {user_input}")
            self.logger.info("=" * 60)

            # 解析用户输入
            self.logger.info("🔍 正在解析用户输入...")
            request = self.parser.parse(user_input)

            self.logger.info(f"✓ 解析成功:")
            self.logger.info(f"  关键词: {request.keyword}")
            self.logger.info(f"  数量: {request.count}")
            self.logger.info(f"  类型: {request.doc_type}")
            self.logger.info(f"  目录: {request.save_dir}")

            # 确保目录存在
            ensure_directory(request.save_dir)

            # 执行下载
            summary = await self.downloader.download_from_request(request)

            # 返回报告
            report = self._format_result_report(summary)
            return report

        except ValueError as e:
            # 输入解析错误
            error_msg = f"❌ 输入解析失败: {e}\n"
            error_msg += self._get_usage_help()
            return error_msg

        except Exception as e:
            # 其他错误
            self.logger.error(f"❌ 下载失败: {e}", exc_info=True)
            return f"❌ 下载失败: {e}"

    def _format_result_report(self, summary) -> str:
        """
        格式化结果报告

        Args:
            summary: DownloadSummary对象

        Returns:
            格式化的报告文本
        """
        lines = []
        lines.append("=" * 60)

        if summary.success_count > 0:
            lines.append("✅ 下载完成！\n")
        else:
            lines.append("⚠️ 下载完成（未成功下载任何论文）\n")

        lines.append("📊 下载统计:")
        lines.append(f"   总计: {summary.total}篇")
        lines.append(f"   成功: {summary.success_count}篇")
        lines.append(f"   跳过: {summary.skipped_count}篇")
        lines.append(f"   失败: {summary.failed_count}篇")

        if summary.files:
            lines.append(f"\n📁 保存位置: {summary.request.save_dir}")
            lines.append(f"\n📄 下载文件列表 ({len(summary.files)}篇):")
            for i, file_path in enumerate(summary.files, 1):
                lines.append(f"   ✅ {file_path.name}")

        if summary.skipped_count > 0 or summary.failed_count > 0:
            lines.append(f"\n⚠️ 未成功下载 ({summary.skipped_count + summary.failed_count}篇):")
            for result in summary.results:
                if not result.is_success():
                    paper_info = result.paper.title[:50] + "..." if len(result.paper.title) > 50 else result.paper.title
                    if result.error_message:
                        lines.append(f"   ⚠️ {paper_info} - 原因: {result.error_message}")

        elapsed = summary.get_elapsed_time()
        if elapsed:
            from src.utils import format_duration
            lines.append(f"\n⏱️  耗时: {format_duration(elapsed)}")

            speed = summary.get_speed()
            if speed:
                lines.append(f"🚀 平均速度: {speed:.1f}篇/分钟")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _get_usage_help(self) -> str:
        """
        获取使用帮助

        Returns:
            帮助文本
        """
        help_text = """
📘 使用说明：

标准格式：
  帮我下载5篇跟'人工智能'相关的学位论文到 D:\\papers\\

示例：
  ✓ 下载10篇关于机器学习的期刊文章到 C:\\docs\\
  ✓ 帮我下20个会议论文，主题是深度学习，保存到 ~/papers/
  ✓ 下载5篇专利，关键词是区块链，到 D:\\patents\\

支持的文献类型：
  • 学术期刊（期刊、期刊文章、journal）
  • 学位论文（学位、硕博论文、thesis、dissertation）
  • 会议（会议论文、conference）
  • 报纸、年鉴、专利、标准、成果、学术辑刊、图书、文库

注意事项：
  • 确保保存目录存在且有写入权限
  • 下载速度取决于网络和CNKI服务器
  • 部分论文可能需要付费权限
"""
        return help_text

    async def download(
        self,
        keyword: str,
        count: int,
        doc_type: str = "学术期刊",
        save_dir: str = "."
    ) -> str:
        """
        下载论文（简化接口）

        Args:
            keyword: 检索关键词
            count: 下载数量
            doc_type: 文献类型
            save_dir: 保存目录

        Returns:
            下载结果报告
        """
        # 构造用户输入
        user_input = f"下载{count}篇跟'{keyword}'相关的{doc_type}到 {save_dir}"

        # 调用主接口
        return await self.download_papers(user_input)


# 创建全局实例
_skill_instance = None


def get_skill() -> CNKIPaperDownloaderSkill:
    """获取Skill实例（单例模式）"""
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = CNKIPaperDownloaderSkill()
    return _skill_instance


# 同步包装器（供外部调用）
def download_papers_sync(user_input: str) -> str:
    """
    下载论文（同步版本）

    Args:
        user_input: 用户输入文本

    Returns:
        下载结果报告
    """
    skill = get_skill()
    return asyncio.run(skill.download_papers(user_input))


# 测试代码
if __name__ == "__main__":
    # 测试用例
    test_input = "帮我下载3篇跟'人工智能'相关的学位论文到 D:\\test_papers\\"

    print("测试CNKI论文下载器")
    print(f"输入: {test_input}")
    print()

    # 执行下载
    skill = get_skill()
    result = asyncio.run(skill.download_papers(test_input))

    print("\n结果:")
    print(result)

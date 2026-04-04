"""
CNKI论文下载器 - 并发下载器
管理并发下载任务和整体流程
"""

import asyncio
from pathlib import Path
from typing import List
from datetime import datetime

from src.models import (
    DownloadRequest, DownloadSummary, DownloadResult,
    Paper, ErrorLog, DownloadStatus
)
from src.cnki_browser import CNKIBrowser
from src.utils import (
    ensure_directory, is_valid_download_directory,
    save_error_log, generate_download_report, setup_logging
)


class ConcurrentDownloader:
    """并发下载器"""

    def __init__(
        self,
        max_concurrent: int = 3,
        config = None,
        logger = None
    ):
        """
        初始化并发下载器

        Args:
            max_concurrent: 最大并发数
            config: 配置对象
            logger: 日志对象
        """
        self.max_concurrent = max_concurrent
        self.config = config
        self.logger = logger or setup_logging(Path.home() / "cnki_downloader_logs")

        # 信号量控制并发数
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download(self, request: DownloadRequest) -> DownloadSummary:
        """
        执行批量下载

        Args:
            request: 下载请求对象

        Returns:
            DownloadSummary: 下载汇总结果
        """
        # 创建汇总对象
        summary = DownloadSummary(request=request)
        summary.start_time = datetime.now()

        self.logger.info("=" * 60)
        self.logger.info("开始批量下载任务")
        self.logger.info(f"关键词: {request.keyword}")
        self.logger.info(f"文献类型: {request.doc_type}")
        self.logger.info(f"下载数量: {request.count}")
        self.logger.info(f"保存目录: {request.save_dir}")
        self.logger.info("=" * 60)

        # 验证下载目录
        is_valid, error_msg = is_valid_download_directory(request.save_dir)
        if not is_valid:
            self.logger.error(f"❌ 下载目录验证失败: {error_msg}")
            raise Exception(f"下载目录无效: {error_msg}")

        try:
            # 启动浏览器（使用反检测配置）
            browser = CNKIBrowser(
                download_dir=request.save_dir,
                headless=self.config.browser.headless if self.config else False,
                slow_mo=self.config.browser.slow_mo if self.config else 500,
                timeout=self.config.download.timeout if self.config else 30000,
                viewport_width=self.config.browser.viewport_width if self.config else 1366,
                viewport_height=self.config.browser.viewport_height if self.config else 768,
                locale=self.config.browser.locale if self.config else "zh-CN",
                timezone=self.config.browser.timezone if self.config else "Asia/Shanghai",
                browser_args=self.config.browser.args if self.config else None,
                user_agent=self.config.browser.user_agent if self.config else None,
                logger=self.logger,
                # PDF下载策略（核心配置）
                pdf_preferred=self.config.download.pdf_preferred if self.config else True,
                pdf_only=self.config.download.pdf_only if self.config else False,
            )

            await browser.start()

            try:
                # 步骤1: 导航到CNKI首页
                await browser.goto_homepage()

                # 步骤2: 选择文献类型
                await browser.select_document_type(request.doc_type)

                # 步骤3: 执行检索
                await browser.search(request.keyword)

                # 步骤4: 获取论文列表
                papers = await browser.get_paper_list(request.count)

                if not papers:
                    self.logger.warning("未找到任何论文")
                    summary.end_time = datetime.now()
                    return summary

                self.logger.info(f"✓ 共找到 {len(papers)} 篇论文")

                # 步骤5: 分批次并发下载
                self.logger.info(f"正在分批次下载（每批 {self.max_concurrent} 篇）...")

                results = await self._download_all_in_batches(papers, browser)

                # 汇总结果
                for result in results:
                    summary.add_result(result)

                summary.end_time = datetime.now()

                # 生成报告
                report = generate_download_report(summary)
                self.logger.info("\n" + report)

                return summary

            finally:
                # 关闭浏览器
                await browser.close()

        except Exception as e:
            self.logger.error(f"❌ 下载过程出错: {e}")
            summary.end_time = datetime.now()

            # 保存错误日志
            error_log = ErrorLog(
                error_code="E002",
                error_message=str(e),
                stack_trace=str(e.__traceback__) if e.__traceback__ else None,
                context={"request": request.__dict__}
            )
            save_error_log(error_log, self.config.logging.log_dir if self.config else Path.home() / "cnki_downloader_logs")

            raise

    async def _download_all(
        self,
        papers: List[Paper],
        browser: CNKIBrowser
    ) -> List[DownloadResult]:
        """
        并发下载所有论文

        Args:
            papers: 论文列表
            browser: 浏览器对象

        Returns:
            下载结果列表
        """
        # 创建下载任务
        tasks = [
            self._download_single(paper, browser, i + 1, len(papers))
            for i, paper in enumerate(papers)
        ]

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 创建失败结果
                final_results.append(DownloadResult(
                    paper=papers[i],
                    status=DownloadStatus.FAILED,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def _download_all_in_batches(
        self,
        papers: List[Paper],
        browser: CNKIBrowser
    ) -> List[DownloadResult]:
        """
        分批次并发下载所有论文

        Args:
            papers: 论文列表
            browser: 浏览器对象

        Returns:
            下载结果列表
        """
        all_results = []
        total_papers = len(papers)
        batch_size = self.max_concurrent
        total_batches = (total_papers + batch_size - 1) // batch_size  # 向上取整

        # 分批处理
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_papers)
            batch_papers = papers[start_idx:end_idx]

            current_batch = batch_num + 1
            self.logger.info(f"\n--- 开始处理第 {current_batch}/{total_batches} 批 (论文 {start_idx + 1}-{end_idx}) ---")

            # 创建当前批次的下载任务
            tasks = [
                self._download_single(paper, browser, start_idx + i + 1, total_papers)
                for i, paper in enumerate(batch_papers)
            ]

            # 并发执行当前批次的任务
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理当前批次的结果
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # 创建失败结果
                    all_results.append(DownloadResult(
                        paper=batch_papers[i],
                        status=DownloadStatus.FAILED,
                        error_message=str(result)
                    ))
                else:
                    all_results.append(result)

            # 如果不是最后一批，等待一段时间再处理下一批
            if current_batch < total_batches:
                delay = 3  # 批次之间延迟3秒
                self.logger.info(f"✓ 第 {current_batch} 批完成，等待 {delay} 秒后处理下一批...")
                await asyncio.sleep(delay)

        self.logger.info(f"\n✓ 所有批次处理完成")
        return all_results

    async def _download_single(
        self,
        paper: Paper,
        browser: CNKIBrowser,
        index: int,
        total: int
    ) -> DownloadResult:
        """
        下载单篇论文（带并发控制）

        Args:
            paper: 论文对象
            browser: 浏览器对象
            index: 当前是第几篇
            total: 总篇数

        Returns:
            DownloadResult对象
        """
        async with self.semaphore:
            try:
                self.logger.info(f"[{index}/{total}] 准备下载: {paper.title[:50]}...")

                # 执行下载
                result = await browser.download_paper(paper)

                # 记录结果
                if result.is_success():
                    self.logger.info(f"[{index}/{total}] ✅ {result.file_path.name}")
                elif result.status == DownloadStatus.SKIPPED:
                    self.logger.warning(f"[{index}/{total}] ⚠️ 跳过: {result.error_message}")
                else:
                    self.logger.error(f"[{index}/{total}] ❌ 失败: {result.error_message}")

                return result

            except Exception as e:
                self.logger.error(f"[{index}/{total}] ❌ 异常: {e}")

                # 创建失败结果
                return DownloadResult(
                    paper=paper,
                    status=DownloadStatus.FAILED,
                    error_message=str(e)
                )


class CNKIDownloader:
    """CNKI论文下载器（高层接口）"""

    def __init__(self, config=None):
        """
        初始化下载器

        Args:
            config: 配置对象（可选）
        """
        self.config = config
        self.logger = setup_logging(
            config.logging.log_dir if config else Path.home() / "cnki_downloader_logs",
            config.logging.level if config else "INFO"
        )

    async def download(
        self,
        keyword: str,
        count: int,
        doc_type: str,
        save_dir: Path,
        **kwargs
    ) -> DownloadSummary:
        """
        下载论文（高层接口）

        Args:
            keyword: 检索关键词
            count: 下载数量
            doc_type: 文献类型
            save_dir: 保存目录
            **kwargs: 其他参数

        Returns:
            DownloadSummary: 下载汇总结果
        """
        # 创建下载请求
        request = DownloadRequest(
            keyword=keyword,
            count=count,
            doc_type=doc_type,
            save_dir=save_dir,
            **kwargs
        )

        # 创建并发下载器
        downloader = ConcurrentDownloader(
            max_concurrent=self.config.download.max_concurrent if self.config else 3,
            config=self.config,
            logger=self.logger
        )

        # 执行下载
        return await downloader.download(request)

    async def download_from_request(self, request: DownloadRequest) -> DownloadSummary:
        """
        从请求对象下载论文

        Args:
            request: 下载请求对象

        Returns:
            DownloadSummary: 下载汇总结果
        """
        # 创建并发下载器
        downloader = ConcurrentDownloader(
            max_concurrent=self.config.download.max_concurrent if self.config else 3,
            config=self.config,
            logger=self.logger
        )

        # 执行下载
        return await downloader.download(request)

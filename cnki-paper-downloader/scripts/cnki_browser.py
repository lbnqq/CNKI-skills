"""
CNKI论文下载器 - CNKI浏览器操作
封装所有与CNKI网站的交互操作
"""

import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Download

from src.models import Paper, DownloadResult, DownloadStatus, ErrorLog
from src.utils import sanitize_filename, generate_unique_filename, setup_logging


async def safe_wait(page: Page, wait_time: int = 8000) -> None:
    """
    安全等待函数：先固定等待，避免超时问题

    Args:
        page: Page对象
        wait_time: 等待时间（毫秒）
    """
    await asyncio.sleep(wait_time)


async def wait_and_confirm(
    page: Page,
    selector: Optional[str] = None,
    timeout: int = 15000,
    confirm_url: bool = False,
    expected_url: Optional[str] = None
) -> bool:
    """
    等待并确认操作成功

    Args:
        page: Page对象
        selector: 要等待的选择器（可选）
        timeout: 超时时间
        confirm_url: 是否确认URL
        expected_url: 期望的URL

    Returns:
        是否成功
    """
    # 先固定等待
    await safe_wait(page, 8000)

    # 确认URL
    if confirm_url and expected_url:
        if page.url() != expected_url:
            return False

    # 等待选择器
    if selector:
        try:
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except:
            return False

    return True


class CNKIBrowser:
    """CNKI浏览器操作封装"""

    # CNKI URL
    CNKI_HOME = "https://www.cnki.net/"

    # 文献类型选择器（基于页面视图分析）
    # 使用text-is进行精确文本匹配，避免匹配到包含相同文字的其他元素
    DOC_TYPE_SELECTORS = {
        "学术期刊": "a:text-is('学术期刊')",
        "学位论文": "a:text-is('学位论文')",
        "会议": "a:text-is('会议')",
        "报纸": "a:text-is('报纸')",
        "年鉴": "a:text-is('年鉴')",
        "专利": "a:text-is('专利')",
        "标准": "a:text-is('标准')",
        "成果": "a:text-is('成果')",
        "学术辑刊": "a:text-is('学术辑刊')",
        "图书": "a:text-is('图书')",
        "文库": "a:text-is('文库')",
    }

    # 检索框选择器（多种策略）
    SEARCH_INPUT_SELECTORS = [
        "input[placeholder*='文献']",
        "input[type='text'].search-input",
        "input[class*='search']",
    ]

    # 检索按钮选择器
    SEARCH_BUTTON_SELECTORS = [
        "button:has-text('检索')",
        "input[type='submit'][value*='检索']",
        ".search-btn",
    ]

    # 论文列表项选择器
    PAPER_ITEM_SELECTOR = ".result-table-list tr"
    # 备用选择器
    PAPER_ITEM_SELECTOR_ALT = ".grid-list-item"

    # 下载按钮选择器
    PDF_DOWNLOAD_SELECTOR = "a:has-text('PDF下载')"
    CAJ_DOWNLOAD_SELECTOR = "a:has-text('CAJ下载')"

    def __init__(
        self,
        download_dir: Path,
        headless: bool = False,
        slow_mo: int = 500,
        timeout: int = 45000,  # 增加到45秒，适应CNKI慢速页面
        viewport_width: int = 1366,
        viewport_height: int = 768,
        locale: str = "zh-CN",
        timezone: str = "Asia/Shanghai",
        browser_args: list = None,
        user_agent: str = None,
        logger = None
    ):
        """
        初始化浏览器

        Args:
            download_dir: 下载保存目录
            headless: 是否无头模式
            slow_mo: 操作延迟（毫秒）
            timeout: 超时时间（毫秒）
            viewport_width: 视口宽度
            viewport_height: 视口高度
            locale: 语言设置
            timezone: 时区
            browser_args: 浏览器启动参数
            user_agent: 用户代理字符串
            logger: 日志对象
        """
        self.download_dir = download_dir
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.locale = locale
        self.timezone = timezone
        self.browser_args = browser_args or []
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.logger = logger or setup_logging(download_dir / "logs")

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """启动浏览器"""
        try:
            self.logger.info("正在启动浏览器（使用反检测配置）...")
            self.playwright = await async_playwright().start()

            # 使用反检测参数启动浏览器
            launch_options = {
                "headless": self.headless,
                "slow_mo": self.slow_mo,
            }

            # 添加浏览器启动参数
            if self.browser_args:
                launch_options["args"] = self.browser_args

            self.logger.debug(f"浏览器启动参数: {launch_options}")
            self.browser = await self.playwright.chromium.launch(**launch_options)

            # 创建浏览器上下文，使用更真实的配置
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': self.viewport_width, 'height': self.viewport_height},
                locale=self.locale,
                timezone_id=self.timezone,
                user_agent=self.user_agent,
                # 添加额外的权限和特性
                permissions=["geolocation", "notifications"],
                color_scheme="light",  # 使用浅色模式
                # 添加更多真实用户的HTTP头
                extra_http_headers={
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )

            # 创建新页面
            self.page = await self.context.new_page()

            # 在页面中添加一些初始化脚本，进一步隐藏自动化特征
            await self.page.add_init_script("""
                // 覆盖navigator.webdriver属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 覆盖chrome对象
                window.chrome = {
                    runtime: {},
                };

                // 覆盖permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // 覆盖plugins长度
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // 覆盖languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
            """)

            self.logger.info("✓ 浏览器启动成功（已应用反检测配置）")

        except Exception as e:
            self.logger.error(f"❌ 启动浏览器失败: {e}")
            raise

    async def close(self) -> None:
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.logger.info("✓ 浏览器已关闭")
        except Exception as e:
            self.logger.error(f"❌ 关闭浏览器时出错: {e}")

    async def goto_homepage(self) -> Page:
        """
        导航到CNKI首页

        Returns:
            Page对象
        """
        try:
            self.logger.info(f"正在访问CNKI首页: {self.CNKI_HOME}")

            await self.page.goto(
                self.CNKI_HOME,
                timeout=45000
            )

            # 等待并确认页面加载
            await safe_wait(self.page, 10000)

            # 确认已到达CNKI首页
            if "cnki.net" not in self.page.url():
                self.logger.warning(f"⚠️ 页面URL可能不正确: {self.page.url()}")
            else:
                self.logger.info("✓ 已访问CNKI首页")

            return self.page

        except Exception as e:
            self.logger.error(f"❌ 访问CNKI首页失败: {e}")
            raise

    async def select_document_type(self, doc_type: str) -> Page:
        """
        选择文献类型

        Args:
            doc_type: 文献类型（中文）

        Returns:
            Page对象
        """
        try:
            self.logger.info(f"正在选择文献类型: {doc_type}")

            # 获取选择器
            selector = self.DOC_TYPE_SELECTORS.get(doc_type)
            if not selector:
                raise ValueError(f"未知的文献类型: {doc_type}")

            # 等待链接出现（增加超时，先固定等待）
            await asyncio.sleep(8000)  # 先固定等待8秒
            await self.page.wait_for_selector(
                selector,
                timeout=30000  # 单独超时30秒
            )

            # 点击链接
            await self.page.click(selector)
            self.logger.info(f"✓ 已点击'{doc_type}'链接")

            # 等待页面加载（使用domcontentloaded代替networkidle）
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(5000)  # 额外等待5秒确保页面完全加载

            # 可能会打开新标签页，切换到新标签页
            if len(self.context.pages) > 1:
                self.page = self.context.pages[-1]
                # 使用domcontentloaded代替networkidle，避免超时
                await self.page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(8000)  # 额外等待确保页面完全加载

            self.logger.info(f"✓ 已进入{doc_type}库页面")

            return self.page

        except Exception as e:
            self.logger.error(f"❌ 选择文献类型失败: {e}")
            raise

    async def search(self, keyword: str) -> Page:
        """
        执行检索

        Args:
            keyword: 检索关键词

        Returns:
            Page对象
        """
        try:
            self.logger.info(f"正在执行检索: {keyword}")

            # 尝试多个选择器定位搜索框（增加等待时间）
            await asyncio.sleep(8000)  # 先固定等待
            search_input = None
            for selector in self.SEARCH_INPUT_SELECTORS:
                try:
                    search_input = await self.page.wait_for_selector(
                        selector,
                        timeout=15000  # 增加到15秒
                    )
                    if search_input:
                        break
                except:
                    continue

            if not search_input:
                raise Exception("无法定位搜索框")

            # 清空并输入关键词（增加等待）
            await search_input.fill("")
            await search_input.fill(keyword)
            await asyncio.sleep(2000)  # 等待输入完成
            await search_input.press("Enter")
            self.logger.info(f"✓ 已输入关键词: {keyword}")

            # 等待结果页加载（使用load代替networkidle）
            await asyncio.sleep(10000)  # 先固定等待10秒
            try:
                await self.page.wait_for_load_state("load", timeout=15000)
            except:
                pass  # 忽略超时，继续执行

            # 等待结果列表出现（增加超时）
            await asyncio.sleep(8000)  # 额外等待
            try:
                await self.page.wait_for_selector(
                    self.PAPER_ITEM_SELECTOR,
                    timeout=45000  # 增加到45秒
                )
            except:
                # 尝试备用选择器
                await self.page.wait_for_selector(
                    self.PAPER_ITEM_SELECTOR_ALT,
                    timeout=45000
                )

            if not search_input:
                raise Exception("无法定位搜索框")

            # 清空并输入关键词
            await search_input.fill("")
            await search_input.fill(keyword)
            await search_input.press("Enter")  # 按回车也可以触发检索
            self.logger.info(f"✓ 已输入关键词: {keyword}")

            # 等待结果页加载（使用load代替networkidle，避免超时）
            try:
                await self.page.wait_for_load_state("load", timeout=10000)
            except:
                pass  # 忽略超时，继续执行

            # 等待结果列表出现
            try:
                await self.page.wait_for_selector(
                    self.PAPER_ITEM_SELECTOR,
                    timeout=self.timeout
                )
            except:
                # 尝试备用选择器
                await self.page.wait_for_selector(
                    self.PAPER_ITEM_SELECTOR_ALT,
                    timeout=self.timeout
                )

            self.logger.info("✓ 检索完成，结果页已加载")

            return self.page

        except Exception as e:
            self.logger.error(f"❌ 执行检索失败: {e}")
            raise

    async def get_paper_list(self, count: int) -> List[Paper]:
        """
        获取论文列表

        Args:
            count: 需要获取的论文数量

        Returns:
            论文列表
        """
        try:
            self.logger.info(f"正在获取前 {count} 篇论文信息...")

            papers = []
            page_num = 1

            while len(papers) < count:
                self.logger.info(f"正在获取第 {page_num} 页...")

                # 获取当前页的论文列表
                page_papers = await self._get_papers_from_current_page()

                if not page_papers:
                    self.logger.warning("当前页没有找到论文，停止获取")
                    break

                papers.extend(page_papers)
                self.logger.info(f"✓ 已获取 {len(page_papers)} 篇论文")

                # 如果已获取足够的论文，停止
                if len(papers) >= count:
                    papers = papers[:count]  # 截取需要的数量
                    break

                # 尝试翻页
                try:
                    # 查找"下一页"按钮
                    next_button = self.page.locator("a:has-text('下一页'), a.next").first
                    if await next_button.is_visible():
                        await next_button.click()
                        # 使用domcontentloaded代替networkidle，避免超时
                        await self.page.wait_for_load_state("domcontentloaded")
                        await asyncio.sleep(8000)  # 额外等待确保页面完全加载
                        page_num += 1
                    else:
                        self.logger.info("没有更多页面了")
                        break
                except:
                    self.logger.info("无法找到下一页按钮")
                    break

            self.logger.info(f"✓ 共获取 {len(papers)} 篇论文信息")

            return papers

        except Exception as e:
            self.logger.error(f"❌ 获取论文列表失败: {e}")
            raise

    async def _get_papers_from_current_page(self) -> List[Paper]:
        """
        从当前页提取论文信息

        Returns:
            当前页的论文列表
        """
        papers = []

        try:
            # 尝试主选择器
            items = await self.page.query_selector_all(self.PAPER_ITEM_SELECTOR)

            # 如果主选择器失败，尝试备用选择器
            if not items:
                items = await self.page.query_selector_all(self.PAPER_ITEM_SELECTOR_ALT)

            for item in items:
                try:
                    # 提取标题
                    title_elem = await item.query_selector("a.title")
                    if not title_elem:
                        title_elem = await item.query_selector(".name a")

                    if title_elem:
                        title = await title_elem.inner_text()
                        title = title.strip()

                        if not title:
                            continue

                        # 创建论文对象
                        paper = Paper(title=title)

                        # 提取作者（可选）
                        author_elem = await item.query_selector(".author")
                        if author_elem:
                            paper.authors = (await author_elem.inner_text()).strip()

                        # 提取来源（可选）
                        source_elem = await item.query_selector(".source")
                        if source_elem:
                            paper.source = (await source_elem.inner_text()).strip()

                        # 提取年份（可选）
                        date_elem = await item.query_selector(".date")
                        if date_elem:
                            paper.year = (await date_elem.inner_text()).strip()

                        # 提取详情页URL（可选）
                        if title_elem:
                            paper.url = await title_elem.get_attribute("href")

                        papers.append(paper)

                except Exception as e:
                    self.logger.warning(f"提取论文信息时出错: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"解析论文列表时出错: {e}")

        return papers

    async def download_paper(self, paper: Paper) -> DownloadResult:
        """
        下载单篇论文

        Args:
            paper: 论文对象

        Returns:
            DownloadResult对象
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"正在下载: {paper.title[:50]}...")

            # 如果没有详情页URL，从列表页直接下载
            if not paper.url:
                # 尝试在当前页找到对应的下载按钮
                return await self._download_from_list_page(paper)

            # 如果有详情页URL，先进入详情页
            else:
                return await self._download_from_detail_page(paper)

        except Exception as e:
            # 下载失败
            elapsed = (datetime.now() - start_time).total_seconds()

            error_log = ErrorLog(
                error_code="E005",
                error_message=str(e),
                paper_title=paper.title
            )

            return DownloadResult(
                paper=paper,
                status=DownloadStatus.FAILED,
                error_message=str(e),
                download_time=elapsed
            )

    async def _download_from_list_page(self, paper: Paper) -> DownloadResult:
        """
        从列表页直接下载（未进入详情页）

        Args:
            paper: 论文对象

        Returns:
            DownloadResult对象
        """
        start_time = datetime.now()

        try:
            # 在列表页查找该论文的行
            # 由于我们在列表页，需要找到对应论文的下载按钮

            # 这里简化处理：实际需要更复杂的逻辑来定位具体是哪一行
            # 对于MVP版本，我们假设已经点击到详情页

            self.logger.warning("从列表页下载功能需要进入详情页")
            raise Exception("需要先进入论文详情页")

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return DownloadResult(
                paper=paper,
                status=DownloadStatus.FAILED,
                error_message=str(e),
                download_time=elapsed
            )

    async def _download_from_detail_page(self, paper: Paper) -> DownloadResult:
        """
        从详情页下载论文

        Args:
            paper: 论文对象（包含URL）

        Returns:
            DownloadResult对象
        """
        start_time = datetime.now()

        try:
            # 导航到详情页
            self.logger.info(f"正在进入详情页: {paper.title[:50]}...")

            # 处理相对URL
            if paper.url and not paper.url.startswith('http'):
                paper.url = "https://kns.cnki.net" + paper.url

            await self.page.goto(paper.url, timeout=45000)
            await self.page.wait_for_load_state("domcontentloaded")
            await safe_wait(self.page, 8000)  # 统一的等待函数

            # 确认已到达详情页
            if "kns.cnki.net" not in self.page.url():
                self.logger.warning(f"⚠️ 详情页URL可能不正确: {self.page.url()}")
            else:
                self.logger.info(f"✓ 已进入详情页")

            # 查找PDF下载按钮（增加超时和等待）
            download_button = None

            # 先固定等待页面稳定
            await asyncio.sleep(5000)

            # 尝试PDF下载
            try:
                download_button = await self.page.wait_for_selector(
                    self.PDF_DOWNLOAD_SELECTOR,
                    timeout=15000  # 增加到15秒
                )
                self.logger.info("✓ 找到PDF下载按钮")
            except:
                self.logger.info("未找到PDF下载按钮，尝试CAJ格式")
                # 尝试CAJ下载
                try:
                    await asyncio.sleep(5000)  # 额外等待
                    download_button = await self.page.wait_for_selector(
                        self.CAJ_DOWNLOAD_SELECTOR,
                        timeout=15000
                    )
                    self.logger.info("✓ 找到CAJ下载按钮")
                except:
                    raise Exception("未找到下载按钮")

            # 点击下载
            self.logger.info("正在点击下载按钮...")

            async with self.page.expect_download(timeout=self.timeout) as download_info:
                await download_button.click()

            download: Download = await download_info.value

            # 确定保存文件名
            suggested_filename = download.suggested_filename
            # 转换为PDF格式（如果是CAJ）
            if suggested_filename.endswith('.caj'):
                suggested_filename = suggested_filename[:-4] + '.pdf'

            # 清理文件名
            clean_filename = sanitize_filename(
                suggested_filename.replace('.pdf', '')
            ) + '.pdf'

            # 检查文件是否已存在
            existing_files = list(self.download_dir.glob("*.pdf"))
            final_filename = generate_unique_filename(clean_filename, existing_files)

            # 保存文件
            save_path = self.download_dir / final_filename
            await download.save_as(save_path)

            elapsed = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"✓ 下载成功: {final_filename}")

            return DownloadResult(
                paper=paper,
                status=DownloadStatus.SUCCESS,
                file_path=save_path,
                download_time=elapsed
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()

            # 检查是否是付费论文
            error_msg = str(e)
            if any(keyword in error_msg for keyword in ["付费", "购买", "权限", "登录"]):
                self.logger.warning(f"⚠️ 论文需要付费或权限: {paper.title[:50]}...")
                return DownloadResult(
                    paper=paper,
                    status=DownloadStatus.SKIPPED,
                    error_message="需要付费权限",
                    download_time=elapsed
                )
            else:
                raise

    def __enter__(self):
        """上下文管理器入口"""
        # 对于异步上下文管理器，需要使用 async with
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # 关闭浏览器（同步版本，实际应该用async）
        pass

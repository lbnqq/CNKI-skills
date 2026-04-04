"""
CNKI论文下载器 - 用户输入解析器
从自然语言中提取结构化参数
"""

import re
from pathlib import Path
from typing import Optional, Tuple
from src.models import DownloadRequest, DocumentType


class InputParser:
    """用户输入解析器"""

    # 文献类型映射表（包含别名）
    DOC_TYPE_MAPPING = {
        # 标准名称 -> 别名列表
        DocumentType.ACADEMIC_JOURNAL.value: [
            "学术期刊", "期刊", "期刊文章", "期刊论文", "journal", "magazine",
            "核心期刊", "cssci", "核心"
        ],
        DocumentType.DISSERTATION.value: [
            "学位论文", "学位", "硕博论文", "硕士论文", "博士论文",
            "thesis", "dissertation", "学位论文"
        ],
        DocumentType.CONFERENCE.value: [
            "会议", "会议论文", "会议文章", "conference", "proceedings",
            "学术会议"
        ],
        DocumentType.NEWSPAPER.value: [
            "报纸", "报纸文章", "newspaper", "报刊"
        ],
        DocumentType.YEARBOOK.value: [
            "年鉴", "统计年鉴", "yearbook", "almanac"
        ],
        DocumentType.PATENT.value: [
            "专利", "patent", "专利文献", "发明专利"
        ],
        DocumentType.STANDARD.value: [
            "标准", "standard", "标准文献", "规范", "行业标准"
        ],
        DocumentType.ACHIEVEMENT.value: [
            "成果", "科技成果", "achievements", "科技成果"
        ],
        DocumentType.JOURNAL_COLLECTION.value: [
            "学术辑刊", "辑刊"
        ],
        DocumentType.BOOK.value: [
            "图书", "图书章节", "book", "图书文献"
        ],
        DocumentType.WENKU.value: [
            "文库", "知网文库", "wenku", "wenki"
        ],
    }

    # 中文数字映射
    CHINESE_NUMBERS = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        "廿": 20, "卅": 30,
        "两": 2
    }

    def __init__(self, default_doc_type: str = DocumentType.ACADEMIC_JOURNAL.value):
        """
        初始化解析器

        Args:
            default_doc_type: 默认文献类型
        """
        self.default_doc_type = default_doc_type

        # 构建反向映射表（别名 -> 标准名称）
        self.alias_to_standard = {}
        for standard_name, aliases in self.DOC_TYPE_MAPPING.items():
            for alias in aliases:
                self.alias_to_standard[alias.lower()] = standard_name

    def parse(self, text: str) -> DownloadRequest:
        """
        解析用户输入

        Args:
            text: 用户输入文本

        Returns:
            DownloadRequest: 解析结果

        Raises:
            ValueError: 当无法解析必需参数时
        """
        # 提取各个参数
        keyword = self._extract_keyword(text)
        count = self._extract_count(text)
        doc_type = self._extract_doc_type(text)
        save_dir = self._extract_save_dir(text)

        # 验证必需参数
        if not keyword:
            raise ValueError("无法识别检索关键词，请使用类似'帮我下载5篇关于'人工智能'的论文'的格式")

        if count is None or count <= 0:
            raise ValueError("无法识别下载数量，请明确指定要下载的论文数量")

        if not save_dir:
            raise ValueError("无法识别保存目录，请指定下载路径（如：'到 D:\\papers\\'）")

        # 创建下载请求对象
        return DownloadRequest(
            keyword=keyword,
            count=count,
            doc_type=doc_type,
            save_dir=save_dir
        )

    def _extract_keyword(self, text: str) -> Optional[str]:
        """
        提取关键词

        支持格式：
        - "关于'人工智能'的论文"
        - "跟'机器学习'相关"
        - "关键词是深度学习"
        - "下载5篇 AI 论文" (AI作为关键词)
        """
        # 策略1: 提取引号内的内容
        quoted_pattern = r'["\'](.+?)["\']'
        match = re.search(quoted_pattern, text)
        if match:
            return match.group(1).strip()

        # 策略2: 匹配"关于/跟/是...的论文"模式
        about_pattern = r'(?:关于|跟|是)\s*["\']?([^\s，。、"'']+?)["\']?\s*(?:的|相关)'
        match = re.search(about_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 策略3: 匹配"下载N篇 XXX 论文"模式（XXX作为关键词）
        count_paper_pattern = r'下载\s*\d+\s*篇\s*["\']?([^\s，。、"'']+?)["\']?\s*论文'
        match = re.search(count_paper_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 策略4: 匹配"下载XXX的论文"模式
        simple_pattern = r'下载\s*(?:\d+\s*篇\s*)?["\']?([^\s，。、"'']+?)["\']?\s*的\s*论文'
        match = re.search(simple_pattern, text, re.IGNORECASE)
        if match:
            keyword = match.group(1).strip()
            # 排除文献类型词汇
            if keyword.lower() not in self.alias_to_standard:
                return keyword

        return None

    def _extract_count(self, text: str) -> Optional[int]:
        """
        提取下载数量

        支持格式：
        - "下载5篇"
        - "下10个"
        - "下载二十篇"
        - "100篇"
        """
        # 策略1: 阿拉伯数字
        arabic_pattern = r'下载\s*(\d+)\s*篇'
        match = re.search(arabic_pattern, text)
        if match:
            return int(match.group(1))

        # 策略2: 中文数字
        chinese_pattern = r'下载\s*([一二三四五六七八九十廿卅两]+)\s*篇'
        match = re.search(chinese_pattern, text)
        if match:
            chinese_num = match.group(1)
            return self._chinese_to_number(chinese_num)

        # 策略3: "下/个"模式
        generic_pattern = r'(?:下载|下)\s*(\d+|[一二三四五六七八九十廿卅两]+)\s*个'
        match = re.search(generic_pattern, text)
        if match:
            count_str = match.group(1)
            if count_str.isdigit():
                return int(count_str)
            else:
                return self._chinese_to_number(count_str)

        return None

    def _extract_doc_type(self, text: str) -> str:
        """
        提取并映射文献类型

        支持格式：
        - "学位论文"
        - "期刊文章"
        - "会议论文"
        - "硕博论文" (别名)
        """
        # 移除常见的干扰词汇
        text_lower = text.lower().replace("的", " ").replace("相关", " ")

        # 遍历所有可能的文献类型词汇
        for alias, standard_name in self.alias_to_standard.items():
            # 使用正则边界匹配，避免误匹配
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                return standard_name

        # 未找到，使用默认值
        return self.default_doc_type

    def _extract_save_dir(self, text: str) -> Optional[Path]:
        """
        提取保存目录

        支持格式：
        - "到 D:\\papers\\"
        - "保存到 ~/documents/"
        - "到 C:\\docs"
        - "保存路径为 /home/user/papers"
        """
        # 策略1: 匹配"到/保存到/保存路径为/路径"模式
        dir_pattern = r'(?:到|保存到|保存路径为|路径)\s*["\']?([a-zA-Z]:\\[^，。、"'']+|~/[^，。、"'']+|/[^\s，。、"'']+|\\\\[^，。、"'']+)["\']?'
        match = re.search(dir_pattern, text)
        if match:
            dir_path = match.group(1).strip()
            # 清理可能的末尾标点
            dir_path = dir_path.rstrip('。，、""\'')
            return Path(dir_path)

        # 策略2: 匹配Windows路径（带盘符）
        windows_pattern = r'([a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*)'
        match = re.search(windows_pattern, text)
        if match:
            return Path(match.group(1))

        # 策略3: 匹配Unix路径
        unix_pattern = r'((?:/[\w\-\.]+)*)'
        match = re.search(unix_pattern, text)
        if match:
            path_str = match.group(1)
            if len(path_str) > 1:  # 至少两层路径
                return Path(path_str)

        return None

    def _chinese_to_number(self, chinese_num: str) -> int:
        """
        中文数字转阿拉伯数字

        支持格式：
        - 一 -> 1
        - 十 -> 10
        - 二十 -> 20
        - 三十五 -> 35
        """
        chinese_num = chinese_num.replace("两", "二")

        # 处理简单情况
        if len(chinese_num) == 1:
            return self.CHINESE_NUMBERS.get(chinese_num, 0)

        # 处理"十几"
        if chinese_num.startswith("十"):
            if len(chinese_num) == 1:
                return 10
            else:
                return 10 + self.CHINESE_NUMBERS.get(chinese_num[1], 0)

        # 处理"几十"
        if len(chinese_num) == 2:
            tens = self.CHINESE_NUMBERS.get(chinese_num[0], 0)
            units = self.CHINESE_NUMBERS.get(chinese_num[1], 0)
            return tens * 10 + units

        # 处理"几十几"
        if len(chinese_num) == 3 and chinese_num[1] == "十":
            hundreds = self.CHINESE_NUMBERS.get(chinese_num[0], 0)
            units = self.CHINESE_NUMBERS.get(chinese_num[2], 0)
            return hundreds * 10 + units

        # 默认：逐字转换
        result = 0
        for char in chinese_num:
            result = result * 10 + self.CHINESE_NUMBERS.get(char, 0)
        return result


# 测试代码
if __name__ == "__main__":
    parser = InputParser()

    # 测试用例
    test_cases = [
        "帮我下载5篇跟'人工智能'相关的学位论文到 D:\\papers\\",
        "下载10篇关于机器学习的期刊文章到 C:\\docs",
        "帮我下20个会议论文，主题是深度学习，保存到 ~/papers/",
        "下载5篇专利，关键词是区块链，到 D:\\patents\\",
        "下载十篇硕博论文到 D:\\test\\",
        "下载100篇AI的学术期刊到 D:\\AI\\",
    ]

    for text in test_cases:
        print(f"\n输入: {text}")
        try:
            request = parser.parse(text)
            print(f"  关键词: {request.keyword}")
            print(f"  数量: {request.count}")
            print(f"  类型: {request.doc_type}")
            print(f"  目录: {request.save_dir}")
        except ValueError as e:
            print(f"  错误: {e}")

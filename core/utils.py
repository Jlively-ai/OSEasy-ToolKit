"""
工具类和数据模型
"""

from dataclasses import dataclass


class Color:
    """控制台颜色管理"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def print(text: str, color: str = '', end: str = '\n'):
        """带颜色的打印"""
        print(f"{color}{text}{Color.END}", end=end)


@dataclass
class ServiceInfo:
    """服务信息数据类"""
    name: str
    description: str


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    name: str
    description: str


@dataclass
class Config:
    """配置信息"""
    version: str = "2.0.0"
    author: str = "Jlively"
    title: str = "OsEasy-ToolKit"
    width: int = 50

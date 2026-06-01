"""
兼容入口：支持在项目根目录直接运行 `python -m polyinsight.cli`。

实际源码保存在 src/polyinsight，根目录包只负责把模块路径接上。
"""

from pathlib import Path


SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "polyinsight"
__path__.append(str(SRC_PACKAGE))

__version__ = "1.0.0"

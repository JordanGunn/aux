"""Kernel functions for aux commands.

Kernels are pure functions that operate on data structures.
CLI commands are thin wrappers around kernels.
Composition happens at the kernel level for in-process pipelines.
"""

from aux.kernels.curl import CurlResponse, CurlResult, curl_kernel
from aux.kernels.find import FindEntry, find_kernel
from aux.kernels.grep import GrepMatch, grep_kernel
from aux.kernels.query import AstCapture, AstMatch, QueryResult, query_kernel
from aux.kernels.sed import SedChange, SedFileResult, SedResult, sed_kernel

__all__ = [
    "grep_kernel",
    "GrepMatch",
    "find_kernel",
    "FindEntry",
    "query_kernel",
    "AstCapture",
    "AstMatch",
    "QueryResult",
    "sed_kernel",
    "SedChange",
    "SedFileResult",
    "SedResult",
    "curl_kernel",
    "CurlResponse",
    "CurlResult",
]

"""
DXY Guardian Module
Monitors Dollar Index and its correlation with Gold
"""

from .tracker import DXYTracker
from .correlation import DXYCorrelationAnalyzer

__all__ = ['DXYTracker', 'DXYCorrelationAnalyzer']

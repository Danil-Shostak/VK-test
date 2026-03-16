# VK Identity Checker - Core Package
# Основные модули запуска и управления приложением

from .main import main
from .run import run_analysis
from .identity_checker import IdentityChecker

__all__ = ['main', 'run_analysis', 'IdentityChecker']

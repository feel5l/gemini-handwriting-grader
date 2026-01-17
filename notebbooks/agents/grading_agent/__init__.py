"""Grading agent module."""

from .agent import (
    GradingResult,
    grade_answer_with_ai,
    grade_answer_with_ocr_and_ai
)

__all__ = [
    'GradingResult',
    'grade_answer_with_ai',
    'grade_answer_with_ocr_and_ai'
]

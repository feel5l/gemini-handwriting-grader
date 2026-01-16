"""Grading agent module."""

from .agent import (
    GradingResult,
    grading_agent,
    ocr_grading_agent,
    grade_answer_with_ai,
    grade_answer_with_ocr_and_ai
)

__all__ = [
    'GradingResult',
    'grading_agent',
    'ocr_grading_agent',
    'grade_answer_with_ai',
    'grade_answer_with_ocr_and_ai'
]

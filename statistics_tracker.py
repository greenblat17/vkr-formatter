from typing import Dict, Any
from document_state import DocumentState


class StatisticsTracker:
    """Отслеживает статистику обработки"""

    def __init__(self):
        self.stats = {
            'total_paragraphs': 0,
            'skipped_paragraphs': 0,
            'h1_formatted': 0,
            'h2_formatted': 0,
            'h3_formatted': 0,
            'h4_formatted': 0,
            'lists_formatted': 0,
            'regular_formatted': 0,
            'references_headers_formatted': 0,
            'bibliography_entries_formatted': 0,
            'bibliography_continuations_formatted': 0,
            'references_text_formatted': 0,
            'special_abstract_formatted': 0,
            'special_annotation_formatted': 0,
            'special_introduction_formatted': 0,
            'special_conclusion_formatted': 0,
            'table_captions_formatted': 0,
            'table_content_formatted': 0,
            'tables_formatted': 0,
            'figure_images_formatted': 0,
            'figure_captions_formatted': 0,
            'formulas_formatted': 0,
            'errors': 0
        }

    def increment(self, stat_name: str):
        """Увеличивает счетчик"""
        if stat_name in self.stats:
            self.stats[stat_name] += 1
        else:
            # Для динамических счетчиков (например, special_*_formatted)
            self.stats[stat_name] = self.stats.get(stat_name, 0) + 1

    def get_statistics(self, state: DocumentState) -> Dict[str, Any]:
        """Возвращает полную статистику"""
        stats = self.stats.copy()
        stats.update({
            'title_pages_detected': 1 if state.found_main_content else 0,
            'main_content_found': state.found_main_content,
            'contents_section_detected': not state.in_contents_section and state.found_main_content,
            'references_section_detected': state.in_references_section
        })
        return stats

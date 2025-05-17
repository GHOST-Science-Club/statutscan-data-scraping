"""
Metrics module

This module is responsible for calculating metrics of scraped document.
Metrics are later used in dashboards or NLP analysis.
"""
from .config_manager import ConfigManager

import textstat
import spacy
import re


class Analyzer():
    CAMEL_CASE_PATTERN = re.compile(
        r"\b[a-ząęćłńóśżź]+[A-ZĄĘĆŁŃÓŚŻŹ]+[a-ząęćłńóśżź]+[a-ząęćłńóśżźA-ZĄĘĆŁŃÓŚŻŹ]*\b")

    def __init__(self, config: ConfigManager):
        textstat.set_lang(config.language)
        self.nlp = spacy.load("pl_core_news_sm")

    def get_metrics(self, text: str) -> dict[str, any]:
        """
        This function returns all metrics used in dashboard.

        Returns:
            int: Characters count (with white characters).
            int: Word count.
            int: Sentences count.
            int: Verbs count.
            int: Nouns count.
            int: Adjectives count.
            float: Average word length in text.
            float: Average length of sentence.
            float: Lexical density (Ratio of unique word to all words)
            float: Gunning Fog - Weighted average of the number of words per sentence, and the number of long words per word. An interpretation is that the text can be understood by someone who left full-time education at a later age than the index.
        """
        doc = self.nlp(text)

        # Basic metrics
        words = 0
        sentences = 0
        verbs = 0
        nouns = 0
        adjectives = 0
        unique_words = set()

        # Averages
        avg_word_length = 0
        avg_sentence_length = 0

        # More metrics
        lexical_density = 0
        camel_case = 0
        capitalized_words = 0

        for token in doc:
            if not token.is_punct and not token.is_space:
                words += 1
                unique_words.add(token.lemma_)
                avg_word_length += len(token)

                if token.pos_ == "NOUN":
                    nouns += 1
                elif token.pos_ == "VERB":
                    verbs += 1
                elif token.pos_ == "ADJ":
                    adjectives += 1

                if re.match(self.CAMEL_CASE_PATTERN, token.text):
                    camel_case += 1
                if token.text.isupper():
                    capitalized_words += 1

        for sentence in doc.sents:
            sentences += 1
            avg_sentence_length += len(sentence)

        avg_word_length = avg_word_length / words if words else 0
        avg_sentence_length = avg_sentence_length / sentences if sentences else 0
        lexical_density = len(unique_words) / words if words else 0
        gunning_fog = textstat.gunning_fog(text) if words > 0 else 0

        metrics = {
            "characters": len(text),
            "words": words,
            "sentences": sentences,
            "nouns": nouns,
            "verbs": verbs,
            "adjectives": adjectives,
            "avg_word_length": round(avg_word_length, 4),
            "avg_sentence_length": round(avg_sentence_length, 4),
            "lexical_density": round(lexical_density, 4),
            "gunning_fog": round(gunning_fog, 4),
        }

        return metrics

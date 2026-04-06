"""
Plagiarism Agent — Internal plagiarism detection using TF-IDF and pattern analysis.
Returns list of issues.
"""

import re
import sys
import os
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue

nltk.download("punkt", quiet=True)


MIN_TEXT_LENGTH = 300
SIMILARITY_THRESHOLD = 0.8


def _clean_sentences(text: str):
    sentences = sent_tokenize(text)
    return [s.strip() for s in sentences if len(s.split()) > 6]


def _check_sentence_similarity(sentences):
    issues = []

    if len(sentences) < 2:
        return issues

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix)

        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                score = similarity_matrix[i][j]

                if score >= SIMILARITY_THRESHOLD:
                    issues.append(create_issue(
                        "Plagiarism",
                        f"High similarity between sentences ({int(score * 100)}%)",
                        "HIGH",
                        "Low originality and potential duplication",
                        f"Sentence 1: \"{sentences[i][:100]}...\"\nSentence 2: \"{sentences[j][:100]}...\"",
                        "Rewrite one of the sentences to improve uniqueness",
                        confidence="HIGH"
                    ))

    except Exception:
        pass

    return issues


def _detect_exact_repetition(sentences):
    seen = set()
    repeated = set()

    for s in sentences:
        key = re.sub(r'\s+', '', s).lower()
        if key in seen:
            repeated.add(s)
        else:
            seen.add(key)

    issues = []
    for s in repeated:
        issues.append(create_issue(
            "Plagiarism",
            "Repeated sentence detected",
            "MEDIUM",
            "Content redundancy",
            f"Repeated sentence: \"{s[:120]}...\"",
            "Remove or rewrite duplicate sentences",
            confidence="MEDIUM"
        ))

    return issues


def _detect_ngram_repetition(text, n=3):
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < n:
        return []

    ngrams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]

    freq = {}
    for ng in ngrams:
        freq[ng] = freq.get(ng, 0) + 1

    repeated = [ng for ng, count in freq.items() if count > 3]

    if repeated:
        return [create_issue(
            "Plagiarism",
            "Repeated phrase patterns detected",
            "MEDIUM",
            "Low originality due to repeated phrasing",
            f"Repeated phrases: {', '.join(repeated[:5])}",
            "Use varied wording to improve content diversity",
            confidence="MEDIUM"
        )]

    return []


def _detect_low_vocab_diversity(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return []

    unique_ratio = len(set(words)) / len(words)

    if unique_ratio < 0.3:
        return [create_issue(
            "Plagiarism",
            "Low vocabulary diversity",
            "LOW",
            "Content may appear repetitive or low quality",
            f"Vocabulary diversity ratio: {unique_ratio:.2f}",
            "Use a wider range of vocabulary",
            confidence="MEDIUM"
        )]

    return []


def _deduplicate_issues(issues):
    unique = []
    seen = set()

    for i in issues:
        key = (i.get("title"), i.get("description"))
        if key not in seen:
            seen.add(key)
            unique.append(i)

    return unique


def run_plagiarism_agent(text: str) -> list:
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise Exception(f"Plagiarism Agent → Text too small ({len(text or '')} chars)")

    sentences = _clean_sentences(text)
    if not sentences:
        raise Exception("Plagiarism Agent → No meaningful sentences found")

    issues = []

    # Core checks
    issues.extend(_check_sentence_similarity(sentences))
    issues.extend(_detect_exact_repetition(sentences))
    issues.extend(_detect_ngram_repetition(text))
    issues.extend(_detect_low_vocab_diversity(text))

    return _deduplicate_issues(issues)
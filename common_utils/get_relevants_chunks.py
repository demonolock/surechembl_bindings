import re


def get_relevant_chunks(
    text: str,
    metric_regex_pattern: str,
    chunk_context_size: int,
    logger,
    negative_keywords_regex: str | None = None,
) -> list[str]:
    """
    Finds relevant chunks of text based on metric keywords and filters out negative keywords.
    """
    try:
        # 1. Find all metric positions
        metric_positions = [
            m.start() for m in re.finditer(metric_regex_pattern, text, re.IGNORECASE)
        ]
        if not metric_positions:
            return []

        # 2. Create intervals
        intervals = []
        for pos in metric_positions:
            start = max(0, pos - chunk_context_size)
            end = min(len(text), pos + chunk_context_size)
            intervals.append((start, end))
        # 3. Merge overlapping intervals
        if not intervals:
            return []

        intervals.sort(key=lambda x: x[0])
        merged_intervals = [intervals[0]]
        for current_start, current_end in intervals[1:]:
            last_start, last_end = merged_intervals[-1]
            if current_start < last_end:
                merged_intervals[-1] = (last_start, max(last_end, current_end))
            else:
                merged_intervals.append((current_start, current_end))

        # 4. Extract text and 5. Apply negative filter
        final_chunks = []
        for start, end in merged_intervals:
            chunk = text[start:end]
            if not negative_keywords_regex or not re.search(
                negative_keywords_regex, chunk, re.IGNORECASE
            ):
                final_chunks.append(chunk)

        return final_chunks
    except Exception as e:
        logger.error(f"Get ex when split file to chunks {e}")
        return []

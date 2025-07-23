from common_utils.call_llm import LLM
from common_utils.config_llm import ConfigLLM
from common_utils.get_relevants_chunks import get_relevant_chunks


def get_alias_list(patent_data, measures):
    content = patent_data["content"]
    annotations = patent_data["annotations"]
    chemicals = []
    for a in annotations:
        if a["category"] == "chemical" or a["category"] == "target":
            chemicals.append(a["name"].lower().strip())
    aliases = set()
    for measure in measures:
        molecule_name = measure["molecule_name"].lower().strip()
        if molecule_name not in chemicals:
            aliases.add(measure["molecule_name"])
    return content, list(aliases)


def parse_llm_output(llm_output: str, logger) -> dict[str, str]:
    alias_value = {}
    for line in llm_output.splitlines():
        term = line.split(";; ")
        if len(term) == 2 and "Not found" not in term[1]:
            alias_value[term[0]] = term[1]
        else:
            logger.debug(f"Skip inconsistent llm out {line}\n")
    return alias_value


def process_patent(content, aliases, config, logger):
    full_output = ""
    alias_value_ans = {}
    aliases_regex = "\\b(" + "|".join(aliases) + ")\\b"
    llm = LLM(
        config.API_RETRY_ATTEMPTS,
        config.API_KEY,
        config.API_BASE_URL,
        config.TEMPERATURE,
        config.MAX_TOKENS_RESPONSE,
        config.MODEL_NAME,
        config.API_RETRY_DELAY,
        logger,
    )
    for chunk_text in get_relevant_chunks(content, aliases_regex, 1500):
        # Filter aliases present in this chunk
        aliases_in_chunk = [alias for alias in aliases if alias in chunk_text]
        if not aliases_in_chunk:
            continue
        user_prompt = config.USER_PROMPT.format(
            alias_list=", ".join(aliases_in_chunk), patent_text=chunk_text
        )
        output = llm.call_llm(user_prompt, config.SYSTEM_PROMPT)
        full_output += output + "\n"
        alias_value = parse_llm_output(output, logger)
        for alias, value in alias_value.items():
            if alias in aliases:
                alias_value_ans[alias] = value
                aliases.remove(alias)
    return full_output, alias_value_ans


def filter_and_convert_molecula_alias_to_name(
    patent_data: dict, measures_list: list, config: ConfigLLM, logger
) -> dict:
    filtered_measures = [
        measure
        for measure in measures_list
        if isinstance(measure, dict)
        and isinstance(measure["molecule_name"], str)
        and isinstance(measure["protein_target_name"], str)
        and isinstance(measure["binding_metric"], str)
    ]
    if not filtered_measures:
        return {}
    content, aliases = get_alias_list(patent_data, filtered_measures)

    logger.debug(f"Aliases: {aliases}")
    alias_value_ans = {}
    if aliases:
        result, alias_value_ans = process_patent(content, aliases, config, logger)
    replaced_measured = []
    for measure in filtered_measures:
        if alias_value_ans.get(measure["molecule_name"], None) is not None:
            measure["molecule_name"] = alias_value_ans.get(measure["molecule_name"])
        replaced_measured.append(measure)
    return replaced_measured

import argparse

from bindingdb.enrich_data.add_inchi_key_and_sequence import add_inchi_key_and_sequence
from bindingdb.enrich_data.json_to_bindingdb import json_to_bindingdb
from data_normalization.normalize_data import normalize_data
from get_final_output import collect_final_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Пайплайн для нормализации и записи данных из патентов."
    )
    parser.add_argument(
        "input_dir",
        type=str,
        default="",
        help="Путь к папке с собранными связями",
    )
    parser.add_argument(
        "output_file",
        type=str,
        default="",
        help="Путь к итоговой таблице.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Количество параллельных потоков для поиска в интернете inchi key.",
    )

    args = parser.parse_args()
    bindings = collect_final_output(args.input_dir)
    normalize_bindings = normalize_data(bindings)
    updated_bindings = add_inchi_key_and_sequence(normalize_bindings)
    json_to_bindingdb(updated_bindings, args.output_file)
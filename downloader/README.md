## Patent Downloader

### Overview

Patent Downloader is a utility for downloading full patent texts for further processing. Due to the instability of the SureChEMBL service and its inability to handle high load, we cache patent texts locally.

### Output Files
To avoid redundant downloads, the tool manages lists of processed patent numbers for different purposes.
- `./out/patent_ids_error.txt` - Patents that could not be downloaded due to errors (e.g., network issues, unavailable content). You can reprocess these later.
- `./out/patent_ids_filtered.txt` - Patents successfully downloaded and that match the required criteria.
- `./out/patent_ids_unfiltered.txt` - Patents that do not meet the filtering criteria (e.g., irrelevant topic, missing content). These are skipped—no download attempted.

### File Descriptions
- `patent_filter.py` - Defines the patent filtering logic. Update this file to adjust which patents are considered relevant for download.
- `__main__.py` - The main entry point. Run this script to start downloading and filtering patents.

### Command Line Arguments
| Argument       | Type  | Required | Description                                                                                    |
| -------------- | ----- | -------- | ---------------------------------------------------------------------------------------------- |
| `--input_file` | `str` | Yes      | Path to a text file containing a list of patent IDs to download.                               |
| `--input_dir`  | `str` | No       | Path to a directory with `patent_ids_{type}.txt` files from a previous run. *(Default: empty)* |
| `--output_dir` | `str` | Yes      | Path to the directory where downloaded patents will be saved.                                  |


If you don’t need to use previous result files, you can omit --input_dir.
Update the file and directory paths as needed for your environment.

### Notes
You can re-run failed downloads using the `patent_ids_error.txt` list.
The tool avoids downloading the same patent multiple times.
Make sure to monitor SureChEMBL load and adjust request rate if necessary.
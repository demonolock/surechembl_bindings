## Molecule Name Alias Resolver
This module is designed to find the actual molecule name when an alias is used in the patent text.

### Overview
In many patent documents, molecules are referred to by aliases such as:

```text
The compound
Example 15
Compound No. 23
```

This module helps to resolve such aliases to the correct molecule name by analyzing the patent text.

Input Data Format
The module expects input data in JSON format, for example:

```json
[
  {
    "molecule_name": "Compound No. 23",
    "protein_target_name": "αvβ3",
    "binding_metric": "Ki",
    "value": "72.81",
    "unit": "nM",
    "patent_number": "EP-1546098-B1"
  }
]
```

### How It Works
1. **Annotation Lookup**:
The module first tries to find molecule_name in the patent annotation.

2. **Alias Detection**:
If molecule_name is not found, it is assumed to be an alias.

3. **LLM Resolution**:
The module scans the patent text and uses a Large Language Model (LLM) to determine what the alias refers to.

### File Structure
`config.py` — contains model and environment settings.

`pipeline.py` — main logic for processing and resolving molecule aliases.

`utils.py` — utility functions used throughout the module.

### Known Issues
Some patents only describe molecules in images, for example:
EP-2810938-A1

In these cases, the module needs to perform OCR (optical character recognition) on the image to extract the text and then resolve the alias.
The proposed approach for handling such scenarios is described in `work_with_img.ipynb`.
import json
import os
from get_measures_from_patent.llm_patent_agents.patent_processor import process_patent_text
from get_measures_from_patent import config


def run_single_test(patent_id, patent_file_path):
    """
    Runs the processing for a single patent file.
    """
    print(f"--- Running Test for {patent_id} ---")

    # 1. Read the full patent text
    try:
        with open(patent_file_path, "r", encoding="utf-8") as f:
            patent_text = f.read()
        print(f"Successfully read {len(patent_text)} characters from {patent_file_path}")
    except FileNotFoundError:
        print(f"ERROR: Patent file not found at {patent_file_path}")
        return

    # 2. Call the main processing function
    print("Starting patent processing...")
    # We pass an empty list for associated_molecules as it's not used by the Extractor.
    extracted_data = process_patent_text(
        patent_text=patent_text,
        associated_molecules=[],
        patent_id=patent_id,
        debug=True
    )

    # 3. Print the final result
    print("\n--- Final Extracted Data ---")
    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))
    print(f"\nTotal data points extracted: {len(extracted_data)}")

    # 4. Check for debug files
    debug_dir = os.path.join(config.DEBUG_OUTPUT_DIR, patent_id)
    print(f"\n--- Debug Output ---")
    if os.path.exists(debug_dir):
        print(f"Debug directory created at: {debug_dir}")
        chunk_file = os.path.join(debug_dir, "01_chunks.json")
        if os.path.exists(chunk_file):
            print(f"- Found chunk file: {chunk_file}")
        else:
            print(f"- WARNING: Chunk file not found.")
        
        extractor_file = os.path.join(debug_dir, "02_extractor_outputs.jsonl")
        if os.path.exists(extractor_file):
            print(f"- Found extractor output file: {extractor_file}")
        else:
            print(f"- WARNING: Extractor output file not found.")

        # Save the final JSON output
        final_output_path = os.path.join(debug_dir, "03_final_output.json")
        with open(final_output_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        print(f"- Saved final output to: {final_output_path}")
    else:
        print("WARNING: Debug directory not found.")

    print(f"\n--- Test for {patent_id} Finished ---\n")

def main():
    """
    Main function to find all patent tests and run them.
    """
    patents_dir = os.path.join("get_measures_from_patent", "llm_patent_agents", "tests", "patents")

    if not os.path.isdir(patents_dir):
        print(f"ERROR: Test patents directory not found at '{patents_dir}'")
        return

    patent_files = [f for f in os.listdir(patents_dir) if f.endswith('.txt')]

    if not patent_files:
        print(f"WARNING: No patent test files (.txt) found in '{patents_dir}'")
        return
    
    print(f"Found {len(patent_files)} patent(s) to test.")

    for patent_filename in patent_files:
        patent_id = os.path.splitext(patent_filename)[0]
        patent_file_path = os.path.join(patents_dir, patent_filename)
        run_single_test(patent_id, patent_file_path)

    print("--- All Test Runs Finished ---")

if __name__ == "__main__":
    main()

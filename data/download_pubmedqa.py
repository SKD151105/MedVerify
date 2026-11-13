"""
Script to download and process the official PubMedQA dataset.
Fetches the expert-annotated PubMedQA labeled dataset (ori_pqal.json).
"""

import os
import json
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PUBMEDQA_URL = "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pubmedqa_labeled.json")


def download_pubmedqa(force: bool = False) -> str:
    """Download PubMedQA labeled dataset if not already present."""
    if os.path.exists(OUTPUT_FILE) and not force:
        logger.info(f"PubMedQA dataset already exists at {OUTPUT_FILE}")
        return OUTPUT_FILE

    logger.info(f"Downloading PubMedQA from {PUBMEDQA_URL}...")
    try:
        response = requests.get(PUBMEDQA_URL, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        processed_records = []
        for pmid, item in raw_data.items():
            contexts = item.get("CONTEXTS", [])
            labels = item.get("LABELS", [])
            
            # Combine labeled abstract sections
            formatted_abstract = []
            for lbl, ctx in zip(labels, contexts):
                formatted_abstract.append(f"{lbl}: {ctx}")
            abstract_text = "\n".join(formatted_abstract) if formatted_abstract else " ".join(contexts)

            processed_records.append({
                "id": f"pmid_{pmid}",
                "pmid": str(pmid),
                "question": item.get("QUESTION", ""),
                "abstract": abstract_text,
                "mesh_terms": item.get("MESH_D", []),
                "ground_truth_decision": item.get("final_decision", "maybe"),
                "golden_answer": item.get("LONG_ANSWER", ""),
                "query_type": "clinical_evidence"
            })

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(processed_records, f, indent=2)

        logger.info(f"Successfully processed and saved {len(processed_records)} records to {OUTPUT_FILE}")
        return OUTPUT_FILE

    except Exception as e:
        logger.error(f"Failed to download PubMedQA dataset: {e}")
        logger.info("Falling back to local data/sample_data.json...")
        return os.path.join(OUTPUT_DIR, "sample_data.json")


if __name__ == "__main__":
    download_pubmedqa()

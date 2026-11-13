"""
Data loader module for MedVerify.
Handles loading, parsing, and chunking of PubMedQA records.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PUBMEDQA_FILE, SAMPLE_DATA_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class PubMedDataLoader:
    def __init__(self, data_path: str = None):
        if data_path:
            self.data_path = data_path
        elif PUBMEDQA_FILE.exists():
            self.data_path = str(PUBMEDQA_FILE)
        else:
            self.data_path = str(SAMPLE_DATA_FILE)

    def load_documents(self) -> List[Dict[str, Any]]:
        """Load and normalize PubMed documents for retrieval indexing."""
        if not os.path.exists(self.data_path):
            logger.warning(f"Data file not found at {self.data_path}. Using fallback sample data.")
            self.data_path = str(SAMPLE_DATA_FILE)

        with open(self.data_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        documents = []
        for item in records:
            # Prepare document chunk
            doc = {
                "id": item.get("id", str(item.get("pmid", ""))),
                "pmid": str(item.get("pmid", "N/A")),
                "question": item.get("question", ""),
                "content": item.get("abstract", ""),
                "mesh_terms": item.get("mesh_terms", []),
                "ground_truth_decision": item.get("ground_truth_decision", "maybe"),
                "golden_answer": item.get("golden_answer", ""),
                "query_type": item.get("query_type", "clinical_evidence")
            }
            documents.append(doc)

        logger.info(f"Loaded {len(documents)} clinical records from {self.data_path}")
        return documents


if __name__ == "__main__":
    loader = PubMedDataLoader()
    docs = loader.load_documents()
    print(f"Sample Document Loaded: ID={docs[0]['id']} | PMID={docs[0]['pmid']}")
    print(f"Question: {docs[0]['question']}")

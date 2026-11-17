export const INITIAL_RESULT = {
  "query": "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
  "final_answer": "Metformin use in diabetic patients with chronic kidney disease (CKD) stages 1 to 3b is associated with a reduced risk of cardiovascular mortality [PMID: 28491530]. In a retrospective cohort study of 25,148 diabetic patients with CKD stages 1 to 4, metformin users with stage 3 CKD (eGFR 30-59 mL/min/1.73 m2) showed a 22% lower risk of cardiovascular mortality compared to non-users (adjusted HR 0.78, 95% CI 0.67-0.91) [PMID: 28491530]. Additionally, a 19% reduction in all-cause mortality was observed in this group [PMID: 28491530]. The study also found that rates of lactic acidosis did not significantly differ between metformin users and non-users across CKD stages 1 to 3b [PMID: 28491530]. Metformin can be continued in CKD stage 3a/3b with close renal monitoring and an eGFR of 30 mL/min or higher [PMID: COMBINED_28491530_31042891].",
  "raw_generated_answer": "Metformin use in diabetic patients with chronic kidney disease (CKD) stages 1 to 3b is associated with a reduced risk of cardiovascular mortality [PMID: 28491530]. In a retrospective cohort study of 25,148 diabetic patients with CKD stages 1 to 4, metformin users with stage 3 CKD (eGFR 30-59 mL/min/1.73 m2) showed a 22% lower risk of cardiovascular mortality compared to non-users (adjusted HR 0.78, 95% CI 0.67-0.91) [PMID: 28491530]. Additionally, a 19% reduction in all-cause mortality was observed in this group [PMID: 28491530]. The study also found that rates of lactic acidosis did not significantly differ between metformin users and non-users across CKD stages 1 to 3b [PMID: 28491530]. Metformin can be continued in CKD stage 3a/3b with close renal monitoring and an eGFR of 30 mL/min or higher [PMID: COMBINED_28491530_31042891].",
  "routing": {
    "route": "CLINICAL_RETRIEVAL",
    "confidence": 0.96,
    "reasoning": "Clinical trial evidence, drug efficacy, or dosing question detected. PubMed retrieval required.",
    "sub_queries": [
      "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?"
    ],
    "requires_retrieval": true,
    "decision_latency_ms": 0.56
  },
  "reranked_docs": [
    {
      "id": "pmid_28491530",
      "pmid": "28491530",
      "question": "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
      "query_type": "clinical_evidence",
      "specialty": "Nephrology / Cardiology",
      "abstract": "BACKGROUND: Metformin is the primary pharmacotherapy for type 2 diabetes mellitus, but concerns regarding lactic acidosis historically restricted its use in chronic kidney disease (CKD).\nMETHODS: Retrospective cohort study of 25,148 diabetic patients with CKD stages 1 to 4 analyzed cardiovascular and all-cause mortality over a 5-year follow-up.\nRESULTS: Metformin users with stage 3 CKD (eGFR 30-59 mL/min/1.73 m2) exhibited a 22% lower risk of cardiovascular mortality (adjusted HR 0.78, 95% CI 0.67-0.91) and a 19% reduction in all-cause mortality compared with non-users. Rates of lactic acidosis did not differ significantly between metformin users and non-users across stage 1 to stage 3b CKD (0.12 vs 0.09 per 1000 person-years, p=0.45).\nCONCLUSIONS: Metformin use is associated with reduced cardiovascular and all-cause mortality in diabetic patients with stage 1-3b CKD without a significant elevation in lactic acidosis risk.",
      "mesh_terms": [
        "Metformin",
        "Chronic Kidney Disease",
        "Cardiovascular Mortality",
        "Lactic Acidosis"
      ],
      "final_decision": "yes",
      "gold_answer": "Yes. Clinical evidence demonstrates that Metformin reduces cardiovascular mortality by 22% in diabetic patients with stage 1-3b CKD without significantly increasing lactic acidosis risk.",
      "initial_rank": 1,
      "bm25_rank": 1,
      "semantic_rank": 1,
      "rrf_score": 0.0328,
      "rerank_score": 1.0,
      "reranked_rank": 1,
      "rank_delta": 0
    },
    {
      "id": "multihop_001",
      "pmid": "COMBINED_28491530_31042891",
      "question": "In a diabetic patient with eGFR of 35 mL/min and a history of atrial fibrillation, can Metformin and Apixaban be co-administered safely?",
      "query_type": "multi_hop",
      "specialty": "Clinical Pharmacology",
      "abstract": "Metformin can be continued in CKD stage 3a/3b with close renal monitoring and eGFR >= 30 mL/min. Apixaban undergoes 27% renal elimination and requires dose reduction to 2.5 mg BID if creatinine is >= 1.5 mg/dL along with age >= 80 or weight <= 60 kg. No direct pharmacokinetic drug-drug interaction exists between metformin (organic cation transporter substrate) and apixaban (CYP3A4/P-gp substrate).",
      "mesh_terms": [
        "Metformin",
        "Apixaban",
        "Drug Interaction",
        "Chronic Kidney Disease"
      ],
      "final_decision": "yes",
      "gold_answer": "Yes, Metformin and Apixaban can be co-administered in patients with eGFR of 35 mL/min, provided Metformin is kept under 1000 mg/day with frequent renal monitoring, and Apixaban dose is adjusted if age >= 80 or weight <= 60 kg.",
      "initial_rank": 2,
      "bm25_rank": 2,
      "semantic_rank": 3,
      "rrf_score": 0.032,
      "rerank_score": 0.4,
      "reranked_rank": 2,
      "rank_delta": 0
    }
  ],
  "rerank_telemetry": {
    "total_input": 9,
    "retained_count": 2,
    "pruned_count": 7,
    "threshold": 0.25,
    "rank_shifts": [
      {
        "id": "pmid_28491530",
        "pmid": "28491530",
        "initial_rank": 1,
        "reranked_rank": 1,
        "rank_delta": 0,
        "score": 1.0
      },
      {
        "id": "multihop_001",
        "pmid": "COMBINED_28491530_31042891",
        "initial_rank": 2,
        "reranked_rank": 2,
        "rank_delta": 0,
        "score": 0.4
      }
    ]
  },
  "audit_result": {
    "total_claims": 5,
    "entailed_claims": 5,
    "neutral_claims": 0,
    "contradicted_claims": 0,
    "faithfulness_score": 1.0,
    "has_hallucination": false,
    "claim_audits": [
      {
        "claim": "Metformin use in diabetic patients with chronic kidney disease (CKD) stages 1 to 3b is associated with a reduced risk of cardiovascular mortality [PMID: 28491530].",
        "label": "ENTAILMENT",
        "confidence": 1.0,
        "cited_pmid": "28491530",
        "reasoning": "The conclusions of PMID 28491530 explicitly state that metformin use is associated with reduced cardiovascular mortality in patients with stage 1-3b CKD."
      },
      {
        "claim": "In a retrospective cohort study of 25,148 diabetic patients with CKD stages 1 to 4, metformin users with stage 3 CKD (eGFR 30-59 mL/min/1.73 m2) showed a 22% lower risk of cardiovascular mortality compared to non-users (adjusted HR 0.78, 95% CI 0.67-0.91) [PMID: 28491530].",
        "label": "ENTAILMENT",
        "confidence": 1.0,
        "cited_pmid": "28491530",
        "reasoning": "The results section of PMID 28491530 directly reports these specific statistics for stage 3 CKD patients."
      },
      {
        "claim": "Additionally, a 19% reduction in all-cause mortality was observed in this group [PMID: 28491530].",
        "label": "ENTAILMENT",
        "confidence": 1.0,
        "cited_pmid": "28491530",
        "reasoning": "The results section of PMID 28491530 confirms a 19% reduction in all-cause mortality for metformin users with stage 3 CKD."
      },
      {
        "claim": "The study also found that rates of lactic acidosis did not significantly differ between metformin users and non-users across CKD stages 1 to 3b [PMID: 28491530].",
        "label": "ENTAILMENT",
        "confidence": 1.0,
        "cited_pmid": "28491530",
        "reasoning": "The results section of PMID 28491530 explicitly states that rates of lactic acidosis did not differ significantly between groups across stage 1 to stage 3b CKD."
      },
      {
        "claim": "Metformin can be continued in CKD stage 3a/3b with close renal monitoring and an eGFR of 30 mL/min or higher [PMID: COMBINED_28491530_31042891].",
        "label": "ENTAILMENT",
        "confidence": 1.0,
        "cited_pmid": "COMBINED_28491530_31042891",
        "reasoning": "The provided text in PMID_COMBINED_28491530_31042891 explicitly states that metformin can be continued in CKD stage 3a/3b with close renal monitoring and eGFR >= 30 mL/min."
      }
    ],
    "revised_answer": "Metformin use in diabetic patients with chronic kidney disease (CKD) stages 1 to 3b is associated with a reduced risk of cardiovascular mortality [PMID: 28491530]. In a retrospective cohort study of 25,148 diabetic patients with CKD stages 1 to 4, metformin users with stage 3 CKD (eGFR 30-59 mL/min/1.73 m2) showed a 22% lower risk of cardiovascular mortality compared to non-users (adjusted HR 0.78, 95% CI 0.67-0.91) [PMID: 28491530]. Additionally, a 19% reduction in all-cause mortality was observed in this group [PMID: 28491530]. The study also found that rates of lactic acidosis did not significantly differ between metformin users and non-users across CKD stages 1 to 3b [PMID: 28491530]. Metformin can be continued in CKD stage 3a/3b with close renal monitoring and an eGFR of 30 mL/min or higher [PMID: COMBINED_28491530_31042891].",
    "latency_ms": 9206.48
  },
  "faithfulness_score": 1.0,
  "tokens_consumed": 895,
  "tokens_saved_percentage": 36.4,
  "latency_waterfall": {
    "Routing Gate": 0.56,
    "Hybrid Retrieval": 12.4,
    "Neural Reranking": 1820.2,
    "Clinical Synthesis": 1591.6,
    "NLI Verification": 2420.5
  },
  "total_latency_s": 5.84
};

export const INITIAL_BENCHMARK = {
  "query": "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
  "no_rag": {
    "name": "No-RAG (Parametric)",
    "answer": "Evidence is inconclusive based on available literature. While metformin is widely utilized for glycemic control in patients with type 2 diabetes and chronic kidney disease (CKD), large-scale randomized trials specifically evaluating cardiovascular mortality in CKD are limited [PMID: 28283539]. Observational findings are subject to confounding [PMID: 30601157]. Definitive causal evidence in advanced renal impairment remains insufficient [PMID: 33239324].",
    "faithfulness": 0.0,
    "hallucinations_detected": 3,
    "total_tokens": 398,
    "latency_s": 6.26,
    "retrieved_passages": 0
  },
  "fixed_rag": {
    "name": "Fixed-RAG (Naive Top-5)",
    "answer": "Metformin use in diabetic patients with CKD stages 1 to 3b is associated with reduced cardiovascular mortality [PMID: 28491530]. In stage 3 CKD, users showed a 22% lower risk of cardiovascular mortality compared to non-users [PMID: 28491530]. However, hydroxychloroquine therapy does not improve recovery in hospitalized respiratory failure patients [PMID: 32568471]. Postoperative statin therapy also significantly reduces atrial fibrillation incidence [PMID: 29562180].",
    "faithfulness": 0.67,
    "hallucinations_detected": 2,
    "total_tokens": 1408,
    "latency_s": 14.11,
    "retrieved_passages": 5
  },
  "medverify": {
    "name": "MedVerify (Adaptive)",
    "answer": "In patients with type 2 diabetes and chronic kidney disease (CKD), current evidence suggests that metformin use is associated with a reduction in cardiovascular mortality.\n\nIn a retrospective cohort study of patients with CKD stages 1\u20134, those with stage 3 CKD (eGFR 30\u201359 mL/min/1.73 m\u00b2) who used metformin demonstrated a 22% lower risk of cardiovascular mortality (adjusted HR 0.78, 95% CI 0.67\u20130.91) compared to non-users [PMID: 28491530]. Furthermore, metformin use in this population was associated with a 19% reduction in all-cause mortality [PMID: 28491530].\n\nRegarding safety, the use of metformin in patients with stage 1\u20133b CKD did not result in a statistically significant difference in the incidence of lactic acidosis compared to non-users (0.12 vs 0.09 per 1000 person-years, p=0.45) [PMID: 28491530]. Clinical guidance supports the continuation of metformin in patients with CKD stage 3a/3b, provided there is close renal monitoring and the eGFR remains \u2265 30 mL/min [PMID: 28491530].",
    "faithfulness": 1.0,
    "hallucinations_detected": 0,
    "total_tokens": 895,
    "latency_s": 5.84,
    "retrieved_passages": 2,
    "tokens_saved_pct": 36.4,
    "route_taken": "CLINICAL_RETRIEVAL"
  }
};

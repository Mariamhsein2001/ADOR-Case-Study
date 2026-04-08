# Global Methodology Document (GMD) — LLM-Based Entity Extraction


## 1. Objective

This document describes the methodology for building an LLM-based entity extraction pipeline combining prompt engineering and Retrieval-Augmented Generation (RAG) to extract financial entities from PDF term sheets.



## 2. Why an LLM for PDFs?

Rule-based parsers fail when layout varies across issuers. Token-classification NER models lack the contextual reasoning required to resolve entities scattered across multiple sections of a legal document. An LLM addresses both limitations — it generalises across document formats without issuer-specific templates and reasons over long multi-section documents to resolve cross-references.



## 3. Pipeline Architecture

```
         PDF Document
              |
              v
   +----------------------+
   |  Step 1: Read PDF    |
   |  Extract raw text    |
   +----------+-----------+
              |
              v
   +----------------------+
   |  Step 2: Check       |
   |  Entities to Extract |
   +----------+-----------+
              |
              v
   +----------------------+
   |  Step 3: Check       |
   |  PDF Length          |
   +----------+-----------+
              |
       -------+-------
       |               |
  Short doc         Long doc
  < context         > context
  window            window
       |               |
       v               v
  Zero-Shot          RAG
  Prompt             Chunk -> Embed
                     -> Retrieve
                     -> Prompt
       |               |
       +-------+-------+
               |
               v
        LLM Inference
               |
               v
        Structured JSON
```



## 4. Step-by-Step Description

### Step 1 — Read the PDF

Text is extracted page by page using pdfplumber for native PDFs. 



### Step 2 — Check Entities to Extract

The target entity schema is defined upfront and remains fixed across all documents processed by the pipeline,an example could be:

| Entity | Description |
|---|---|
| Counterparty | Name of Party A / the client |
| Initial Valuation Date | Trade start date |
| Notional | Face value of the trade |
| Valuation Date | Final observation date |
| Maturity | Termination date |
| Underlying | Asset the product is linked to |
| Coupon | Interest rate or payment |
| Barrier | Price threshold as % of initial price |
| Calendar | Business day calendar code |



### Step 3 — Check PDF Length

The extracted text word count is compared against the model's effective context window. If within the limit, a one-shot prompt is used. If the document exceeds it, the RAG pipeline is activated.

- **Short document** (< context window) → one-shot prompting
- **Long document** (> context window) → RAG



### Step 4a — One-Shot Prompt (short documents)

The full document text and the entity schema are passed in a single prompt. One-shot prompting is used — a worked example is included in the prompt to anchor the output format and reduce JSON parsing failures.

**Prompt structure:**

```
SYSTEM:
You are a financial NER extraction system. Extract the entities below
from the provided document. Return only valid JSON. Return null for
any entity not explicitly present in the text. Do not infer values.

DOCUMENT:
"""
[full PDF text]
"""

Example input:
"Party A: BANK ABC ... Notional Amount (N): EUR 5 million ...
 Termination Date: 15 March 2027 ... Barrier (B): 70.00% of Shareini"

Example output:
{
  "Counterparty":           "BANK ABC",
  "Notional":               "EUR 5 million",
  "Maturity":               "15 March 2027",
  "Barrier":                "70.00% of Shareini",
  "Initial Valuation Date": null,
  "Valuation Date":         null,
  "Underlying":             null,
  "Coupon":                 null,
  "Calendar":               null
}

Now extract from the document above and return only JSON:
{
  "Counterparty":           "<value or null>",
  "Initial Valuation Date": "<DD Month YYYY or null>",
  "Notional":               "<CCY amount or null>",
  "Valuation Date":         "<DD Month YYYY or null>",
  "Maturity":               "<DD Month YYYY or null>",
  "Underlying":             "<name and ISIN or null>",
  "Coupon":                 "<% or null>",
  "Barrier":                "<% of Shareini or null>",
  "Calendar":               "<calendar code or null>"
}
```



### Step 4b — RAG Pipeline (long documents)

**Chunking:** The document is split using a recursive character text splitter with a chunk size of 512 tokens and an overlap of 64 tokens[for example]. 

**Embedding:** Each chunk is encoded into a dense vector using a sentence embedding model (e.g. `all-MiniLM-L6-v2`). The embedding captures the semantic meaning of the chunk as a fixed-size numerical representation. Chunks discussing the same concept will have high cosine similarity regardless of exact wording.

**Storage:** All chunk vectors are stored in a **vector database** (e.g. FAISS, ChromaDB), which enables fast approximate nearest-neighbour search over the entire document at query time.

**Retrieval:** For each target entity, a natural-language query is embedded using the same model. The top-k chunks (k=3) with the highest cosine similarity to the query vector are retrieved from the vector store. Depending on retrieval accuracy, additional strategies can be layered on such as using hybrid retrieval.


**Example queries per entity:**

| Entity | Retrieval Query |
|---|---|
| Counterparty | "Who is the counterparty or Party A in this trade?" |
| Notional | "What is the notional amount or face value?" |
| Barrier | "What is the barrier level expressed as a percentage?" |
| Calendar | "What is the business day calendar used?" |

**RAG prompt (per entity):**

```
SYSTEM:
You are a financial NER extraction system. Answer using only the
context below. Return the exact value as it appears in the text.
If not present, return null. No explanation.

CONTEXT:
"""
[top-3 retrieved chunks]
"""

One-shot example:
Context: "Notional Amount (N): EUR 1 million payable on the Effective Date"
Question: "What is the notional amount or face value?"
Answer: "EUR 1 million"

Question: [entity-specific query]
Answer:
```



### Step 5 — LLM Inference

The constructed prompt is submitted to the LLM.For the RAG the outputs are mapped to the required json format.
- A Pydantic schema  is applied at inference time where the model supports it to enforce structured output and eliminate post-hoc parsing failures. 
- Temperature is set to 0 for deterministic, reproducible extractions. 
- For confidential documents, inference must run on-premises using an open-source model (Mistral-7B, LLaMA-3).


### Step 6 — Output and Validation

The LLM response is parsed and validated against the entity schema:
- Required fields returning null are flagged as missing
- Date fields are regex-checked against `DD Month YYYY`


## 6. Evaluation

### Retrieval Quality (RAG only)

| Metric | Definition | Target |
|---|---|---|
| Context Precision | Of the chunks retrieved, how many are actually relevant — measures noise | ≥ 0.80 |
| Context Recall | Of all relevant chunks in the document, how many were retrieved — measures coverage | ≥ 0.85 |


### Generation Quality

| Metric | Definition | Target |
|---|---|---|
| Exact Match | Extracted value matches ground truth after normalisation | ≥ 80% |
| Fuzzy Match | Extracted value within Levenshtein distance of 2 | ≥ 90% |
| Null Hallucination Rate | Absent fields incorrectly returned as non-null | < 5% |
| Faithfulness | Extracted value traceable to the source context | ≥ 95% |

---

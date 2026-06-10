# The Unofficial Guide — Project 1:
## Ask the Trojans: A Grounded QA System for USC CS Professor Reviews

---

## Domain

This system covers student reviews of Computer Science professors at the University of Southern California (USC). The knowledge is valuable because USC's official course catalog and department pages provide almost no qualitative information about teaching style, exam difficulty, grading curves, or how accessible a professor is outside of class. Students making scheduling decisions rely entirely on peer knowledge, which is scattered across multiple platforms (RateMyProfessors, Coursicle, Koofers) with no unified interface. This system aggregates those informal reviews into a grounded question-answering interface so students can ask natural-language questions and get sourced answers from real peer feedback.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors – Bill Cheng | RMP GraphQL reviews | https://www.ratemyprofessors.com/professor/913088 |
| 2 | RateMyProfessors – Mark Redekopp | RMP GraphQL reviews | https://www.ratemyprofessors.com/professor/860888 |
| 3 | RateMyProfessors – Andrew Goodney | RMP GraphQL reviews | https://www.ratemyprofessors.com/professor/2163737 |
| 4 | RateMyProfessors – Saty Raghavachary | RMP GraphQL reviews | https://www.ratemyprofessors.com/professor/798241 |
| 5 | RateMyProfessors – Chi So | RMP GraphQL reviews | https://www.ratemyprofessors.com/professor/1746653 |
| 6 | Coursicle – CSCI 104 | HTML course reviews | https://www.coursicle.com/usc/courses/CSCI/104/ |
| 7 | Coursicle – CSCI 102 | HTML course reviews | https://www.coursicle.com/usc/courses/CSCI/102/ |
| 8 | Coursicle – All CSCI courses | HTML course index | https://www.coursicle.com/usc/courses/CSCI/ |
| 9 | Koofers – USC professors | HTML professor ratings | https://www.koofers.com/university-of-southern-california-usc/professors |
| 10 | documents/ | Local .txt files | documents/rmp_bill_cheng.txt, rmp_mark_redekopp.txt, rmp_andrew_goodney.txt, rmp_saty_raghavachary.txt, rmp_chi_so.txt, coursicle_csci104.txt, coursicle_csci102.txt, coursicle_csci.txt, koofers_usc_cs.txt |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Why these choices fit your documents:** Individual RateMyProfessors reviews average 80–200 characters each. A 500-character window captures 2–4 complete reviews per chunk while keeping enough context for the embedding model to identify the professor and course being discussed. Going much larger (1000+ chars) would risk mixing reviews of different professors into one chunk — especially on Coursicle pages that list multiple instructors for the same course. The 100-character overlap prevents a single review from being silently split across two chunk boundaries, ensuring no review loses its opening sentence. Before chunking, HTML tags and navigation boilerplate are stripped with BeautifulSoup. Every review line is also prefixed with a `[Professor: name]` tag during ingestion, so the professor identity is encoded into the embedding even when the chunk boundary falls mid-review. Chunks shorter than 80 characters (bare metadata headers, stray punctuation) are discarded.

The splitter uses separators ordered from coarsest to finest (`"\n\n"`, `"\n"`, `". "`, `" "`, `""`) so paragraph breaks are preferred over mid-sentence cuts.

**Final chunk count:** 726 chunks across 9 source files.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (local inference, 384-dimensional embeddings). Vectors are stored in a persistent ChromaDB collection and retrieved using cosine similarity at top-k = 5.

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is fast (22M parameters), free to run locally, and handles general English well — a solid baseline for a class project. For a real deployment serving thousands of USC students, three tradeoffs would dominate the decision. First, **context length**: MiniLM truncates at 256 tokens, which silently cuts longer Koofers or Coursicle entries; models like `bge-large-en-v1.5` (512-token limit) or OpenAI's `text-embedding-3-large` (8,191-token limit) handle that without loss. Second, **domain accuracy**: review corpora contain informal language, abbreviations ("HW", "OH", "curve"), and USC-specific course codes (CSCI 402) that a general-purpose model may under-weight relative to a model fine-tuned on educational or review text. Third, **latency vs. quality**: API-hosted models like `text-embedding-3-large` deliver better retrieval quality in benchmarks but add network round-trip latency and per-token cost — acceptable for low-traffic use but expensive at scale. A production system would benchmark `bge-large-en-v1.5` locally against the OpenAI model on 50 domain-specific queries to decide whether the quality gain justifies the infrastructure cost.

---

## Grounded Generation

**System prompt grounding instruction:** The LLM (Llama 3.3 70B via Groq) receives a strict system prompt with five rules: (1) answer ONLY from the text in the "Retrieved context" block; (2) use no training-data knowledge or assumptions; (3) if the context is insufficient, respond with exactly "I don't have enough information on that" and nothing else; (4) do not speculate or hedge with words like "typically" or "generally" unless those exact words appear in the retrieved text; (5) do not fabricate professor names, course numbers, or review sentiment. The full system prompt is in `generate.py` lines 38–48.

**How source attribution is surfaced in the response:** Attribution works at two levels. At the LLM level, each chunk header in the context block includes the source filename, professor name, course, and URL (e.g., `[1] Source: rmp_bill_cheng.txt | Professor: Bill Cheng | URL: ...`), and the system prompt instructs the model to cite the filename inline after each factual claim. At the pipeline level, source labels are also collected programmatically from the retrieved chunk metadata *before* the LLM call and appended to the response object as a guaranteed `sources` list — so attribution is never lost even if the model omits an inline citation.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Bill Cheng's grading in CSCI 402 (Operating Systems)? | Exams are difficult and unforgiving; Cheng applies a curve; transparent about expectations; start projects early. | Grading is "fair," "aggressive, complex, but fair," and grading guidelines are "damn clear." Coursework is designed to surface "how and why" understanding. (rmp_bill_cheng.txt) | Relevant | Partially accurate |
| 2 | Is Mark Redekopp a good professor for students who are new to programming? | Yes — patient, engaging, explains fundamentals well; reviews recommend him specifically for beginners. | Praises him as an "amazing lecturer" who makes concepts "super clear," but also notes the course is challenging, homework is demanding, and he "firmly bans any cooperation." | Relevant | Partially accurate |
| 3 | How much homework does Andrew Goodney typically assign in his CS courses? | Heavy workload; tagged "Lots of Homework" on RMP; frequent problem sets; students recommend starting early and going to office hours. | "I don't have enough information on that." | Relevant | Inaccurate |
| 4 | What is the general student opinion of Saty Raghavachary's teaching style in CSCI 585 (Database Systems)? | Mixed: half praise storytelling and passion; half find lectures hard to follow and exam material unclear; attendance essential. | Mixed reviews: praised as "knowledgeable, passionate, and humorous," "brilliant," "inspirational," but criticized for covering many topics at a surface level. | Relevant | Partially accurate |
| 5 | Which USC CS professors are most praised for being available and helpful outside of class? | Redekopp and Goodney most frequently praised; Chi So also positive; Cheng mixed. | Redekopp praised for many office hours and email/Piazza responsiveness. Cheng mentioned for being "very organized" (off-target). Goodney and Chi So absent. | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "How much homework does Andrew Goodney typically assign in his CS courses?" (Q3)

**What the system returned:** "I don't have enough information on that." — despite returning five chunks from `rmp_andrew_goodney.txt`, including chunks that mention homework explicitly (e.g., "The homework had advanced coding problems that need a lot of practice to be good at" and "Homeworks are vague but if you put in the effort and START EARLY it will pay off").

**Root cause (tied to a specific pipeline stage):** The failure has two compounding causes, one at the ingestion stage and one at the generation stage.

*Ingestion gap:* The RMP scraper fetched review text via the GraphQL API's `comment` field, which captures the freeform paragraph a student writes. It did not fetch the structured "tags" that RMP aggregates separately on a professor's profile page (labels like "Lots of Homework," "Tough Grader," "Accessible Outside Class"). The expected answer specifically referenced those tags. Because they were never scraped, they were never chunked, embedded, or available for retrieval — the information simply does not exist in the vector store.

*Generation over-refusal:* The chunks that were retrieved (e.g., chunk 2: "homework had advanced coding problems that need a lot of practice") do contain qualitative homework evidence. However, the question asks "how much" — a quantitative framing — and the strict system prompt rule 4 bars the model from generalizing or saying "typically" unless that word appears verbatim in the retrieved text. The model interpreted the mismatch between the quantitative question and the qualitative evidence as insufficient context, triggering the "I don't have enough information on that" fallback.

**What you would change to fix it:** At the ingestion stage, augment the RMP GraphQL query to fetch `teacherRatingTags` (the aggregate tag counts exposed by the same API) and include them as a structured block at the top of each professor's document — e.g., `[Tags: Lots of Homework x47, Tough Grader x31, Amazing Lectures x28]`. This would give the retriever a compact, high-signal token that directly matches workload queries. As a secondary fix, soften rule 4 in the system prompt so the model can synthesize qualitative evidence into a descriptive answer rather than refusing when the question uses the word "typically."

---

## Spec Reflection

**One way the spec helped you during implementation:** The Chunking Strategy section in `planning.md` was precise enough to serve as a direct code specification. It specified chunk size (500 chars), overlap (100 chars), minimum chunk length (80 chars), the separator ordering preference (paragraph breaks over sentence breaks), and the `[Professor: name]` prefix requirement on every review line. When generating `chunk.py`, those numbers were passed directly as constants (`CHUNK_SIZE = 500`, `CHUNK_OVERLAP = 100`, `MIN_CHUNK_LEN = 80`) with no iteration needed. The `[Professor:]` tag convention also propagated naturally into `extract_chunk_metadata()` — the function that re-reads those tags from each chunk to populate the ChromaDB metadata fields — which would have been much harder to design without the upfront decision documented in the spec.

**One way your implementation diverged from the spec, and why:** The spec's Architecture diagram specified the Anthropic API with `claude-haiku-4-5` as the generation model. The implementation instead uses the Groq API with `llama-3.3-70b-versatile`. The change was made during the generation milestone because Groq's free tier provides fast inference (sub-second for most responses) without requiring any billing setup, which made the development and testing loop substantially faster. The system prompt and grounding rules were designed for Claude's instruction-following behavior but translated cleanly to Llama 3.3 — the refusal behavior ("I don't have enough information on that") works as intended in both models.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The RMP source list from `planning.md` (five professor URLs with numeric IDs), the scraping architecture note (GraphQL API, no JS rendering needed), and the Anticipated Challenges section describing cross-professor contamination in chunks — specifically the need to prefix every review line with `[Professor: name]` so chunk boundaries never strip attribution.
- *What it produced:* A complete `scrape.py` with a `fetch_rmp_professor()` function that uses RMP's public GraphQL endpoint (`https://www.ratemyprofessors.com/graphql`) with HTTP Basic auth, paginates through reviews using `endCursor`, and writes every review line prefixed by a structured tag block including professor name, class code, quality rating, difficulty rating, and would-take-again flag.
- *What I changed or overrode:* The AI initially generated a scraper that fetched the RMP HTML page with Selenium to handle JavaScript rendering. I overrode this approach by directing it to use the GraphQL API instead — which the planning notes had already identified as available (the endpoint is used by RMP's own React frontend). This eliminated the Selenium dependency entirely and made the scraper faster and more reliable. I also directed it to include `[Quality:]`, `[Difficulty:]`, and `[Would Take Again:]` structured tags on every review line, beyond what the spec described, so that retrieval chunks carry richer metadata.

**Instance 2**

- *What I gave the AI:* The Generation block from the Architecture diagram (grounding requirement, inline citation format, refusal behavior for off-domain questions), the system prompt rules I had drafted by hand, and the `retrieve.py` interface (`query(question: str, k: int) -> list[dict]`) from the previous milestone.
- *What it produced:* A `generate.py` module with the `ask()` function that calls `retrieve.py`, formats a numbered context block with per-chunk headers, calls the LLM with the system prompt, and returns a dict containing the answer and a programmatically collected sources list. It also produced a `main()` CLI block that runs all five evaluation queries in sequence.
- *What I changed or overrode:* The AI wrote the LLM call using the Anthropic SDK (`import anthropic`), matching the spec. I overrode this to use the Groq SDK instead (`from groq import Groq`) and the `llama-3.3-70b-versatile` model, keeping the system prompt and context formatting identical. I also added the two-level attribution mechanism — the AI initially only relied on the LLM to include inline citations, which the strict grounding rules sometimes suppressed. I directed it to also collect sources programmatically from chunk metadata before the LLM call and include them unconditionally in the returned `sources` list.

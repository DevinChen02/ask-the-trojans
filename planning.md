# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

This project focuses on student reviews of Computer Science professors at the University of Southern California (USC). This knowledge is valuable because USC's official course catalog and department pages offer almost no qualitative insight into teaching style, grading fairness, workload expectations, or how a professor handles office hours. Aggregating this peer knowledge through a retrieval system gives students a more complete picture than any single official channel provides.


---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessors – USC school page | Aggregate student ratings and written reviews for all USC professors across departments; good for broad coverage and sorting by department | https://www.ratemyprofessors.com/school/1381 |
| 2 | RateMyProfessors – Bill Cheng | 188+ student reviews of the CSCI 402 (Operating Systems) professor; covers grading, workload, and lecture quality for a core upper-div course | https://www.ratemyprofessors.com/professor/913088 |
| 3 | RateMyProfessors – Mark Redekopp | 250+ reviews covering CSCI 102/104; highly rated professor of intro and data structures courses — useful contrast against more divisive professors | https://www.ratemyprofessors.com/professor/860888 |
| 4 | RateMyProfessors – Andrew Goodney | 196+ reviews for intro CS and systems courses; tags like "lots of homework" and "accessible outside class" show dimension beyond star rating | https://www.ratemyprofessors.com/professor/2163737 |
| 5 | RateMyProfessors – Saty Raghavachary | 244+ reviews for CSCI 585 (Database Systems); one of the most-reviewed CS professors at USC, good source for upper-div perspective | https://www.ratemyprofessors.com/professor/798241 |
| 6 | RateMyProfessors – Chi So | Reviews for a highly-rated professor known for engaging lectures; provides positive-end signal to contrast with more mixed reviews | https://www.ratemyprofessors.com/professor/1746653 |
| 7 | Coursicle – CSCI 104 (Data Structures & OOP) | 196 student reviews tied to specific professor sections (Redekopp, Goodney, Raghothaman, etc.); course-level view lets users compare instructors teaching the same class | https://www.coursicle.com/usc/courses/CSCI/104/ |
| 8 | Coursicle – CSCI 102 (Intro to Programming) | 64 reviews for USC's introductory CS course with professor breakdowns; covers the entry point most CS students share | https://www.coursicle.com/usc/courses/CSCI/102/ |
| 9 | Coursicle – All CSCI courses at USC | Index of student reviews across every CSCI-prefixed course; useful for discovering which upper-division courses have notable feedback | https://www.coursicle.com/usc/courses/CSCI/ |
| 10 | Koofers – USC CS professor ratings | Alternative review platform with USC professor ratings and student-uploaded course materials; covers professors who may have fewer RMP reviews | https://www.koofers.com/university-of-southern-california-usc/professors |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Reasoning:** Individual RateMyProfessors and Coursicle reviews average 80–200 characters each. A 500-character window captures 2–4 complete reviews per chunk while keeping enough context for the embedding model to identify the professor and course being discussed. Going much larger (e.g., 1000+ chars) risks mixing reviews of different professors into one chunk — especially on Coursicle pages that list multiple instructors for the same course — which would confuse retrieval. The 100-character overlap prevents a single review from being silently split across two chunk boundaries, ensuring no review loses its opening or closing sentence. Before chunking, HTML tags, rating numbers, and navigation boilerplate are stripped with BeautifulSoup so only review text and professor/course metadata remain.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is a fast (22M parameters), free to run locally, and produces 384-dimensional embeddings that handle general English well. For a real deployment serving thousands of USC students, I would weigh three tradeoffs. First, **context length**: MiniLM truncates input at 256 tokens, which is fine for short reviews but would silently cut longer Koofers entries; a model like `bge-large-en-v1.5` (512-token limit) or OpenAI's `text-embedding-3-large` (8191-token limit) handles that without loss. Second, **domain accuracy**: review corpora contain informal language, abbreviations ("HW", "OH", "curve"), and USC-specific course codes (CSCI 402) that a general model may under-weight; a model fine-tuned on educational or review text would improve semantic matching. Third, **latency vs. quality**: API-hosted models like `text-embedding-3-large` give better retrieval quality in benchmarks but add network latency and cost per token — acceptable for a low-traffic deployment but costly at scale. For a production system I would benchmark `bge-large-en-v1.5` locally against OpenAI's API model on a sample of 50 domain-specific queries to decide whether the quality gain justifies the cost.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Bill Cheng's grading in CSCI 402 (Operating Systems)? | Reviews indicate exams are very difficult and unforgiving, but Cheng applies a curve and is transparent about expectations. Students consistently warn to start projects early and attend all lectures. The overall sentiment is that the class is hard but learnable. |
| 2 | Is Mark Redekopp a good professor for students who are new to programming? | Yes — reviews on RMP and Coursicle consistently praise Redekopp as patient, engaging, and skilled at explaining fundamentals from scratch. Tags like "Amazing lectures" and "Caring" appear frequently. Most reviewers recommend him specifically for beginners. |
| 3 | How much homework does Andrew Goodney typically assign in his CS courses? | Reviews tag him with "Lots of Homework" — he assigns frequent problem sets and multi-week projects. Students note the workload is heavy but the assignments reinforce concepts. Several reviews recommend starting early and going to office hours. |
| 4 | What is the general student opinion of Saty Raghavachary's teaching style in CSCI 585 (Database Systems)? | Mixed. About half of reviews praise his storytelling, real-world examples, and passion for the subject. The other half find his lectures hard to follow and say the exam material is not clearly telegraphed in class. Students agree attendance and slide review are essential. |
| 5 | Which USC CS professors are most praised for being available and helpful outside of class? | Retrieval should surface Redekopp and Goodney as most frequently praised for office-hour responsiveness and replying to emails. Chi So also appears with positive accessibility tags. Cheng gets mixed marks — present but office hours can be crowded during exam season. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Cross-professor contamination in chunks**: Coursicle course pages (e.g., CSCI 104) list reviews for multiple instructors on the same page, often without a strong separator between sections. After scraping and chunking at 500 characters, a chunk could contain the tail of a Redekopp review immediately followed by the start of a Goodney review. If a user asks "What do students think of Goodney?", the retriever might return that mixed chunk, and the LLM could accidentally attribute Redekopp's praise to Goodney. Mitigation: prepend each review or section with an explicit `[Professor: <name>]` tag during ingestion so the embedding encodes the professor identity, and filter retrieved chunks by detected professor name before passing to generation.

2. **Sparse or degenerate chunks from short reviews**: RMP allows one-sentence reviews (e.g., "Great prof, would take again.") that are only 30–40 characters. When the splitter windows over these, a 500-character chunk might be padded with 8–10 back-to-back micro-reviews, each about a different aspect of the same professor. The resulting embedding is a noisy average of many signals, which makes it harder for cosine similarity to surface that chunk for a specific query like "How hard are Cheng's exams?" The fix is to set a minimum chunk length (e.g., discard chunks under 80 characters) and, during ingestion, group consecutive micro-reviews for the same professor into a single logical block before the splitter runs.

---

## Architecture

```
┌──────────────────────────────┐
│      Document Ingestion      │
│  requests + BeautifulSoup    │
│  Sources: RMP, Coursicle,    │
│  Koofers (10 URLs)           │
│  Output: raw text files with │
│  [Professor:] metadata tags  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Chunking           │
│  LangChain                   │
│  RecursiveCharacterSplitter  │
│  chunk_size=500 chars        │
│  overlap=100 chars           │
│  Output: ~N chunks with      │
│  professor/course metadata   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Embedding + Vector Store   │
│  sentence-transformers       │
│  model: all-MiniLM-L6-v2     │
│  Vector store: ChromaDB      │
│  (persistent local store)    │
│  Output: 384-dim embeddings  │
│  indexed by chunk id         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Retrieval           │
│  ChromaDB cosine similarity  │
│  top-k = 5 chunks            │
│  Input: user query string    │
│  Output: 5 ranked chunks     │
│  with source metadata        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Generation          │
│  Anthropic API               │
│  model: claude-haiku-4-5     │
│  System prompt enforces      │
│  grounding: answer only from │
│  retrieved context, cite     │
│  professor name + source URL │
│  Output: grounded response   │
│  with inline citations       │
└──────────────────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

- **Tool:** Claude (claude-sonnet-4-6 via Claude Code)
- **Input:** The Documents table (10 sources with URLs), the Chunking Strategy section (500-char chunks, 100-char overlap, strip HTML), and the Anticipated Challenges section (cross-professor contamination, micro-review noise).
- **Expected output:** A `scrape.py` script using `requests` + `BeautifulSoup` that fetches each URL, strips navigation/rating boilerplate, prepends `[Professor: <name>]` tags to each review block, and writes raw `.txt` files to `documents/`. A `chunk.py` script that uses `LangChain`'s `RecursiveCharacterTextSplitter` with `chunk_size=500`, `chunk_overlap=100`, filters out chunks under 80 characters, and outputs a list of `(chunk_text, metadata)` tuples where metadata includes professor name, course code, and source URL.
- **Verification:** Manually inspect 3–5 output chunks from each source file to confirm: (1) no HTML tags remain, (2) every chunk includes a `[Professor:]` tag, (3) no chunk spans two different professors, (4) chunks are within the 80–500 character range. Run a quick word-frequency check to confirm "Professor" metadata appears in expected proportion.

**Milestone 4 — Embedding and retrieval:**

- **Tool:** Claude (claude-sonnet-4-6 via Claude Code)
- **Input:** The Retrieval Approach section (model: `all-MiniLM-L6-v2`, top-k=5, ChromaDB persistent store), the chunk output format from Milestone 3, and the Architecture diagram showing 384-dim embeddings indexed by chunk id.
- **Expected output:** An `embed.py` script that loads chunks from Milestone 3, instantiates `sentence-transformers` with `all-MiniLM-L6-v2`, encodes each chunk, and upserts vectors + metadata into a persistent ChromaDB collection. A `retrieve.py` module exposing a `query(question: str, k: int = 5) -> list[dict]` function that embeds the question and returns the top-k chunks with their source metadata.
- **Verification:** Run the 5 Evaluation Plan questions through `retrieve.py` and manually check that at least 3 of the 5 returned chunks per question are topically relevant (mention the right professor and a keyword from the expected answer). Also verify that the ChromaDB store persists across process restarts by re-running retrieval after a fresh Python process.

**Milestone 5 — Generation and interface:**

- **Tool:** Claude (claude-sonnet-4-6 via Claude Code)
- **Input:** The Generation block from the Architecture diagram (Anthropic API, `claude-haiku-4-5`, grounding system prompt requiring inline citations), the `retrieve.py` interface from Milestone 4, and the Evaluation Plan's 5 question/expected-answer pairs.
- **Expected output:** A `generate.py` module with a `answer(question: str) -> str` function that (1) calls `retrieve.py` for top-5 chunks, (2) formats them into a context block, (3) calls the Anthropic API with a system prompt that instructs the model to answer only from context and cite professor name + source URL inline, and (4) returns the grounded response. A minimal CLI (`main.py`) that reads a question from stdin and prints the response.
- **Verification:** Run all 5 Evaluation Plan questions and compare responses against the expected answers row by row. Check that every response contains at least one inline citation with a professor name. Confirm refusal behavior by asking an off-domain question (e.g., "Who won the Super Bowl?") and verifying the model says it cannot answer from the provided context.

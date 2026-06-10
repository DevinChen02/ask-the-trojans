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

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

# Content Repurposer & Multi-Channel Distribution Role Pack

The **Content Repurposer Agent** is Varistha's autonomous growth employee that ingests long-form intellectual property (podcast recordings, webinar transcripts, technical whitepapers, engineering deep dives, or strategic memos) and systematically transforms it into 5 high-converting, channel-optimized distribution assets.

Modeled on modern repurposing workflows pioneered by tools like **Castmagic**, **Taplio**, and **Jasper**, this agent eliminates the friction of manual multi-channel marketing while maintaining rigorous adherence to brand voice, formatting constraints, and character limits.

---

## 1. Multi-Channel 5-Asset Transformation Architecture

```
                 [Long-Form Source Ingestion]
        (Transcripts / Whitepapers / Technical Blogs)
                             │
                             ▼
              [Adversarial Quarantine & Clean]
          (Filters prompt injections & raw tokens)
                             │
                             ▼
         [Core Thesis & Insight Extraction Engine]
    ┌────────────────────────┼────────────────────────┐
    ▼                        ▼                        ▼
[Executive X Thread]   [LinkedIn Carousel Post]  [2x Standalone Posts]
(5-7 punchy tweets,    (High-retention hook,     (Metric & contrarian
 under 280 chars)      framework, discussion Q)   standalone posts)
    │                        │                        │
    └────────────────────────┼────────────────────────┘
                             ▼
    ┌────────────────────────┴────────────────────────┐
    ▼                                                 ▼
[Newsletter Feature Segment]               [5-Slide Narrative Deck]
(Subject options, TL;DR,                   (Problem, Shift, Solution,
 pull quote, editorial body)                Metrics, Visual prompts)
                             │
                             ▼
               [Human Approval Gate (L1)]
        (Operator reviews before outbound publish)
```

---

## 2. Channel-Native Transformation Rules

1. **Executive X/Twitter Thread**:
   - 5 to 7 tweets total.
   - Tweet 1: High-curiosity hook.
   - Tweets 2-5: Standalone, numbered insights strictly under 280 characters.
   - Tweet 6-7: Takeaway summary and call to action.
2. **High-Engagement LinkedIn Carousel / Long-Form Post**:
   - Line 1-2: Provocative observation above the "see more" cutoff.
   - Clean spacing with zero wall-of-text formatting.
   - Open-ended conversation starter in closing to spur comments.
3. **Standalone X Snippets**:
   - Snippet A: Surprising data/metric callout.
   - Snippet B: Contrarian insight comparing common belief vs operational reality.
4. **Newsletter Feature Block**:
   - Multiple punchy subject lines (< 45 chars).
   - 3-bullet executive TL;DR for scanners.
   - 120-180 word editorial narrative with highlighted pull quote.
5. **Executive 5-Slide Narrative**:
   - Structured 5-slide progression (Problem -> Inflection -> Solution -> Metrics -> Action).
   - Each slide provides title, key message, 3 crisp bullets, and visual design prompt.

---

## 3. Governance, Autonomy & Safety

- **Autonomy Level**: `L1` (Drafts and transforms autonomously; publishing pauses for human review).
- **Plugins Bound**:
  - `web-fetch`: Ingests source articles and transcripts directly from URLs.
  - `email-draft`: Drafts newsletter segments.
  - `x-post`: Formats and stages social thread drafts (**requires approval for dispatch**).
  - `linkedin-post`: Formats and stages LinkedIn post drafts (**requires approval for dispatch**).
- **Security Quarantine**: Raw input text is strictly quarantined against prompt injection attacks.
- **Evaluation Benchmark**: Validated against `evals/suite.yaml` across 5 real-world content types (podcasts, whitepapers, founder blogs, keynotes, postmortems) with an 85% minimum pass rate.

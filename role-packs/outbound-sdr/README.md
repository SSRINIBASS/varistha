# Outbound SDR & Multi-Channel Copywriting Role Pack

The **Outbound SDR & Multi-Channel Copywriting Agent** is Varistha's autonomous sales employee built for generating hyper-personalized, high-converting outbound sequences across Cold Email and LinkedIn.

Modeled on modern outbound intelligence engines like **Lavender**, **Regie.ai**, and **Instantly**, this agent eliminates generic marketing copy by enforcing strict behavioral copywriting principles: **short 2-4 word subject lines**, **punchy 50-110 word bodies**, **single low-friction CTAs**, and **character-capped LinkedIn notes (< 300 chars)**.

---

## 1. Multi-Channel 3-Touch Framework

```
[Target Prospect Intelligence]
             │
             ▼
      [Touch 1: Cold Email]          ──> 50-110 words, Lavender 90+ Score, Low-friction CTA
             │
             ▼
   [Touch 2: LinkedIn Note]          ──> Strictly < 300 characters, warm observation
             │
             ▼
  [Touch 3: Follow-Up Email]         ──> Threaded reply, < 60 words, concrete proof point
             │
             ▼
 [Objection Anticipation Rebuttal]   ──> Tailored 1-sentence objection pre-emption
             │
             ▼
   [Mandatory Approval Gate]         ──> Pauses for human review before any outbound send
```

---

## 2. Copywriting Rules (Lavender-Optimized)

1. **Subject Lines**: 2 to 4 words, natural casing, zero clickbait or spam words.
2. **Body Length**: 50 to 110 words total. Mobile-friendly single-sentence paragraphs.
3. **The 4-Part Structure**:
   - *Observation / Hook*: Reference a verified trigger (funding, article, tech stack).
   - *Problem Statement*: Highlight the friction peers face with unmonitored agents.
   - *Proof Point*: Explain how Varistha solves it.
   - *Call to Action*: Ask for interest or feedback ("Open to a quick look at the docs?").
4. **LinkedIn Connection Limit**: Hard enforced at under 300 characters.

---

## 3. Governance, Autonomy & Safety

- **Autonomy Level**: `L1` (Human in the Loop for Outbound).
- **Plugins Bound**:
  - `email-draft`: Contextual email composer.
  - `email-send`: Outbound sender (**requires approval**).
  - `linkedin-post`: Outbound social poster (**requires approval**).
- **Enforcement**: Under Autonomy L1, proposed dispatch actions pause execution, generate an `Approval` record in governance, and await operator confirmation.
- **Evaluation Benchmark**: Validated against `evals/suite.yaml` ensuring compliance with sequence formatting, word counts, and operator review flags.

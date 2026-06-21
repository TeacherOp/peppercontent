# PRD — Atlas Report Builder

**Owner:** Customer Success / Product · **Status:** Prototype · **Last updated:** 2025-11

---

## 1. Problem

Every CS manager on Pepper's team spends **4+ hours/week** building recurring
client reports. The work is manual and repetitive: pull data from ~7 sources
(GSC, GA4, Semrush, Semrush AI/GEO, WordPress, Webflow, Contentful), stitch it
into spreadsheets and decks, calculate period-over-period changes, write the
"what happened and why" narrative, format, and email it on a cadence.

The slowest part isn't the charts — it's the **analysis and narrative**: working
out what moved, why, and what to recommend. That's also the part that should
play to an AI-native platform's strengths.

## 2. Goal & success metric

Cut the time to produce a client-ready report from **4+ hours/week to under 30
minutes/week per manager**, with no loss of quality, by automating data
collection, delta computation, narrative drafting, and formatting — leaving the
manager to **review, edit, and approve**.

**North-star metric:** median minutes-to-send per report.
**Guardrail:** edit distance / approval rate (quality must not drop — see §7).

## 3. Users & the experience

| Who | When | What they see |
|---|---|---|
| **CS manager** | On the reporting cadence | Picks a client + period + cadence → reviews a fully drafted report → edits the narrative → approves & sends. |
| **Client** | On receipt | A clean, branded report (HTML/PDF) leading with AI search visibility, then organic, traffic, competitive, and content. |
| **CS lead** | Ongoing | Consistency across the team; a shared definition of what a "good report" contains. |

**Flow:** `Select client + period + cadence` → `Atlas pulls all sources` →
`computes period-over-period deltas` → `Claude drafts the narrative &
recommendations` → `manager reviews/edits` → `Approve & send`.

The prototype is the clickable artifact of this flow: the request form
(`/`) and the rendered, print-to-PDF report (`/report`), with a draft tag and an
Approve & send action.

## 4. What the product does

1. **Connects the sources.** Treated as black-box APIs. The prototype ships a
   mock layer (`atlas/mock_api/`) returning realistic data shapes for 3 demo
   clients; in production each module is swapped for the real client.
2. **Computes period-over-period deltas** for every metric (current vs previous
   period, with direction and whether it's an improvement).
3. **Generates the narrative with Claude** (`claude-sonnet-4-5`): an executive
   summary, per-section insights, highlights, and prioritised recommendations —
   grounded only in the supplied numbers.
4. **Renders a client-ready report**: an HTML page with charts, exportable to
   PDF, leading with **AI search visibility** (Pepper's differentiator).
5. **Review → approve → send** (mocked send in the prototype).

## 5. Report contents (sections)

| Section | Sources | Key fields |
|---|---|---|
| **AI search visibility** *(lead)* | Semrush AI / GEO | visibility score, share of voice, mention rate, avg position, per-engine breakdown, sentiment, cited pages, sample prompts |
| Organic search | GSC | clicks, impressions, CTR, position; top queries; biggest movers |
| Traffic & conversions | GA4 | sessions, users, engagement, conversions, revenue by channel |
| Competitive | Semrush | keywords, est. traffic, authority score, backlinks; competitor visibility table |
| Content health | WordPress / Webflow / Contentful | inventory, recently published, stale count, refresh candidates |
| Executive summary & recommendations | Claude over all of the above | narrative + prioritised actions |

## 6. Data sources used (and why)

From the documented endpoints we use what a recurring report actually needs:

- **GSC `searchanalytics.query`** — single source of truth for organic clicks /
  impressions / CTR / position, by query and page.
- **GA4 `properties.runReport`** — sessions, conversions, revenue by channel;
  ties search to business outcomes.
- **Semrush `domain_organic`, `domain_organic_pages`, `backlinks_overview`,
  competitor visibility** — rankings, authority, competitive context.
- **Semrush AI `ai_visibility_overview`, `ai_prompt_mentions`,
  `ai_citation_tracking`** — the AI-visibility story.
- **WordPress / Webflow / Contentful list endpoints** — content inventory and
  `modified` dates for the refresh program.

**Endpoints intentionally skipped:** GSC URL Inspection / sitemaps / mobile test
(diagnostics, not recurring-report material). **What we'd add:** a per-client
**branding/config** record (logo, tone, KPI targets) and a **commentary store**
so manager edits feed back into future drafts (see §8).

## 7. Eval / experiment design — does it actually save the 4 hours?

**Hypothesis:** Atlas reduces median minutes-to-send per report by ≥80% with no
drop in client-perceived quality.

**Design — within-subjects A/B over 4 weeks:**
- **Dataset:** the team's real recurring reports (~N managers × clients/week).
- **Arm A (control):** current manual process.
- **Arm B (treatment):** Atlas draft → review → send.
- Randomise per report-occurrence (each manager does both arms across their book
  to control for individual speed).

**Primary metric:** median **minutes-to-send** (instrumented start→approve).
**Target:** ≥80% reduction (4h → ≤30m/week).

**Quality guardrails (must not regress):**
- **Edit ratio:** % of the drafted narrative changed before approval (proxy for
  draft trust; track trend — should fall over time).
- **Approval rate without major rewrite** (≥ a defined bar).
- **Client quality score:** blind 1–5 rating of Arm A vs Arm B reports by a CS
  lead panel; **factual-error rate** (counts of wrong/unsupported claims) must be
  ≤ control.
- **Client engagement:** report open / reply rate (no decline).

**Success criteria:** Arm B hits the time target **and** clears every quality
guardrail. Decision: ship if both hold; iterate on narrative prompt if quality
lags; revisit scope if time savings fall short.

## 8. Scope

**In scope (prototype):** the flow above, 3 demo clients, mock data layer,
Claude narrative, HTML/PDF report.

**Non-goals (per brief — assume they exist):** auth, billing, dashboard chrome,
real API integration/credentials, scheduling/automated send, multi-tenant
storage.

**Next:** real source connectors; saved per-client branding & KPI targets;
scheduled auto-draft + notify; manager edits captured as feedback to improve
future drafts; alerting on notable swings.

## 9. Assumptions & competitive context

- **AI search visibility is the wedge.** Competitors (e.g. agency reporting
  tools like AgencyAnalytics, Looker Studio templates, Semrush's own reports)
  automate *organic* dashboards well but treat the report as charts, not a
  *written, decision-ready narrative*, and largely don't yet cover **generative
  / AI-search visibility** (ChatGPT, Perplexity, AI Overviews). Atlas leads with
  exactly that, plus an LLM-written narrative — the manual, high-value step those
  tools leave to the human.
- Sources behave as documented and return realistic data.
- Claude (`claude-sonnet-4-5`) drafts the narrative; a human always reviews
  before send (no unattended client-facing generation).

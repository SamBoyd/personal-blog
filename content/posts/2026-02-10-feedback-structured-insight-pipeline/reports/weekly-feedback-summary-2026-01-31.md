# Weekly Feedback Summary

**Week ending**: 2026-01-31
**Report generated**: 2026-02-13 10:09:05

## Summary Stats

- **Feedback this week**: 20
- **Cumulative feedback (all time)**: 50

**Sentiment breakdown** (this week):
- Positive: 6 (30%)
- Neutral: 6 (30%)
- Negative: 8 (40%)

**Urgency distribution** (this week):
- High: 5 (25%)
- Medium: 9 (45%)
- Low: 6 (30%)

## Top Themes

| Theme | Count | % |
|-------|------:|--:|
| feature-request | 6 | 30% |
| praise | 6 | 30% |
| bug | 5 | 25% |
| confusion | 2 | 10% |
| ux | 1 | 5% |

## Repeated Pain Points

**1. Authentication & Session Stability** (1 report, HIGH urgency)
Random logouts persist despite users clearing cache and cookies, pointing to a backend session-management bug. This erodes trust and interrupts workflows — users cannot rely on the app to maintain state.

**2. Mobile App Broken on iOS** (1 report, HIGH urgency)
The main page is non-scrollable on iPhone, rendering the mobile experience unusable. This is a total blocker for mobile users and has been reported repeatedly.

**3. Unsaved Work Lost on Tab Switch** (1 report, HIGH urgency)
Switching tabs still discards unsaved changes — a long-standing bug. Users risk losing work every session, which drives frustration and distrust in the product.

**4. Dashboard Performance at Scale** (2 reports, MEDIUM–HIGH urgency)
Chart rendering lags with large datasets, and users with 500+ items see 20-second load times. Performance improvements helped lighter workloads but haven't addressed power users yet.

**5. Notification Overload & Missing Digest** (1 report, MEDIUM urgency)
Excessive email notifications remain a recurring complaint. Users want a digest option to reduce noise — its absence pushes people toward muting notifications entirely.

**6. Data Recovery / Undo** (1 report, HIGH urgency)
Accidental project deletion with no recycle bin or undo continues to surface. The lack of a safety net makes destructive actions feel irreversible and dangerous.

**7. Permissions & Role Clarity** (1 report, MEDIUM urgency)
The team invite flow improved, but the permissions UI still doesn't explain what each role can actually do, causing confusion during onboarding and team setup.


## Praise of the Week!

> "Keyboard shortcuts were added! Thank you! The Ctrl+K command palette is perfect."

A long-requested power-user feature that landed well. Command palettes signal maturity and reward users who invest in learning the product.

> "Just saw you added Slack integration! Works perfectly. Exactly what I needed."

Integration wins reinforce the product's role in existing workflows. This validates that connecting to tools people already use drives real satisfaction.

> "The recent performance improvements are noticeable. App feels much faster this week."

Users notice when things get faster. This praise shows that backend/performance work — often invisible — directly impacts user sentiment.


## Notable Quotes

> **[bug]** "Tab switching still loses my unsaved work. This bug has been open for months."

A trust-breaking bug with sustained urgency. The phrase "open for months" signals growing frustration and potential churn risk.

> **[feature-request]** "Please add a bulk edit feature. Updating 50 tasks one by one is painful."

Highlights a scaling gap: the product works for small workloads but becomes tedious as users grow. This is a retention risk for power users.

> **[confusion]** "The team invite flow worked this time. But the permissions UI is unclear about what each role can do."

A partial fix that reveals a deeper UX problem. Users can complete the flow but don't understand the consequences of their choices.


## Resolved vs. Unresolved

**Ongoing** (seen this week and in prior weeks):
- `accessibility`, `api`, `archive`, `auth`, `calendar`, `color-coding`, `customization`, `dashboard`, `data-loss`, `data-recovery`, `deletion`, `developer-experience`, `digest`, `drag-and-drop`, `email`, `file-upload`, `firefox`, `frequency`, `integration`, `invite`, `keyboard-shortcuts`, `logout`, `mobile`, `notifications`, `performance`, `planning`, `productivity`, `projects`, `session`, `simplicity`, `slack`, `tabs`, `tasks`, `team`, `trash`, `ui`, `undo`, `unresolved`, `unsaved-changes`, `workflow`

**New this week** (not seen before):
- `backend`, `broken`, `bug-fix`, `bulk-edit`, `charts`, `colorblind`, `command-palette`, `complexity`, `error-messages`, `feature-creep`, `filters`, `improvement`, `ios`, `permissions`, `quota`, `rendering`, `roles`, `scale`, `scrolling`, `size-limit`, `speed`, `sprints`, `storage`, `usability`, `webhooks`, `workaround`

**Potentially resolved** (seen in prior 4 weeks but absent this week):
- `account`, `browser`, `browser-compat`, `buttons`, `clean-design`, `collaboration`, `crash`, `csv`, `custom-fields`, `dark-mode`, `data`, `deadlines`, `desktop-app`, `discoverability`, `documentation`, `error-handling`, `export`, `fuzzy-search`, `gallery`, `getting-started`, `latency`, `layout`, `link-expiry`, `loading`, `native`, `onboarding`, `organization`, `password`, `pdf`, `priorities`, `recurring`, `recurring-tasks`, `regression`, `reporting`, `responsive`, `scheduling`, `search`, `settings`, `silent-failure`, `stability`, `state`, `task-list`, `templates`, `tutorial`, `typo-tolerance`, `view`, `visual`

## Action Candidates

1. **Fix the tab-switch data loss bug.** HIGH urgency, repeated across multiple weeks, tagged `unsaved-changes` and `data-loss`. This is the single biggest trust destroyer in the current feedback set — prioritize above new features.

2. **Investigate and resolve random logout issues.** HIGH urgency, repeated, tagged `auth`, `session`, `backend`. Users have already ruled out client-side causes. A backend audit of session handling and token expiry is warranted.

3. **Ship a recycle bin or soft-delete for projects.** HIGH urgency, repeated request tagged `undo`, `trash`, `data-recovery`. Relatively bounded in scope and directly addresses accidental deletion anxiety — a quick win for user confidence.

4. **Optimize dashboard rendering for large datasets (500+ items).** 2 reports this week spanning MEDIUM and HIGH urgency, tagged `dashboard`, `performance`, `rendering`, `scale`. Consider virtualized lists or pagination to address power-user load times.

5. **Add an email digest option for notifications.** MEDIUM urgency, repeated, tagged `notifications`, `email`, `digest`. A digest toggle is a low-complexity change that could meaningfully reduce notification fatigue and prevent users from disabling notifications entirely.

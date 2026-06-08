# Fork Translations (seed)

Reusable plain-language translations for common technical forks. Each entry is a starting point, not a script: adapt to the user's scale, constraints, and repo. Use “often” and “for this scale,” not universal claims.

## Realtime vs request-response
- **Keeps asking (polling / REST):** the page asks the server every few seconds, “anything new?” Simple and works almost everywhere; updates arrive a little late and it still asks when nothing changed.
- **One-way server updates (Server-Sent Events / SSE):** the browser keeps one line open and the server streams updates. Feels live for server-to-browser updates; not for two-way chat-like traffic.
- **Two-way live connection (WebSocket):** browser and server keep one open conversation. Feels truly live and supports two-way events; more moving parts, reconnect logic, and operational complexity.
- **Hosted realtime:** a managed service handles live fan-out. Fast to launch; adds vendor cost/lock-in.
- **Scale default:** tiny or non-live → polling. Server-to-client live feed → SSE or hosted realtime. Two-way interactions or very live collaboration → WebSocket/hosted realtime.

## Local-only vs cloud
- **Local (on-device storage):** simple, cheap, private; data is tied to one device and can be lost without backup.
- **Cloud (hosted backend):** works across devices and survives device loss; adds cost, accounts/auth, and data-handling responsibility.
- **Local-first + backup/sync:** keeps the app usable locally while syncing or backing up later; attractive but conflict resolution can become real complexity if multiple devices edit the same thing.
- **Scale default:** one user/one device → local with explicit backup. Multiple devices/people or loss is unacceptable → cloud or carefully scoped local-first sync.

## On-device model vs API model
- **On-device model:** works offline, private, no per-call API bill; heavier to ship and usually constrained by device speed/model size.
- **API model:** often higher quality and faster to iterate because model hosting is external; needs network, costs per call, and data leaves the device/service boundary.
- **Hybrid:** on-device for cheap/private/simple cases, API for high-quality or fallback cases; more branching to design.
- **Scale default:** privacy/offline/cost-control → on-device or hybrid. Best quality and fast iteration with acceptable network/data tradeoff → API.

## Single app vs separate services
- **One program (monolith):** easiest to build, run, test, and reason about; can still be well-structured internally.
- **Separate services:** parts scale/deploy independently; adds network calls, contracts, monitoring, and more failure modes.
- **Scale default:** solo/early → monolith. Split only when independent scaling, ownership, or deployment needs are already real.

## Relational vs document store
- **Relational (SQL):** strong default when data has relationships, reporting, constraints, or transactions; schema changes are managed rather than avoided.
- **Document (NoSQL/document store):** flexible for self-contained records and rapid shape changes; cross-record queries, consistency, and migrations can get harder later.
- **Modern caveat:** many SQL databases can store JSON, and many document stores add query features. Decide from access patterns, consistency needs, team familiarity, and migration risk, not fashion.
- **Scale default:** structured relationships/reporting/transactions → SQL. Mostly independent evolving documents → document store may fit.

# AI-Chess
2D Chess with AI Opponents

Project Proposal & Project Plan 
A local two-player and player-vs-AI chess application with benchmarked, tiered AI opponents Team Project — Five Members  |  Estimated duration: ~4.5 months to checkpoint, 6 months to final delivery 

# Project Overview 
 This project is a playable chess application supporting local two-player games and player-versus-AI games. Its defining feature is a set of AI opponents built at increasing levels of sophistication, from simple random move selection up through alpha-beta search with a tuned evaluation function. Because the AI tiers are designed to be directly comparable, the project doubles as its own evaluation study: the team can run AI-vs-AI tournaments between tiers and use the results as the analytical backbone of the final report. 

 This structure gives the team two things that are often hard to get simultaneously in a course project: a clear, demo-able product at every milestone, and a built-in research question — how much does each layer of AI sophistication actually improve play — that doesn't require external data or additional scope to answer.

# Design Rationale
Why tiered AI, specifically?

Rather than building one "best" AI, the team builds a ladder of opponents (Tier 1 through Tier 4) that share the same interface and can be swapped in and out against the same engine. This has a few practical benefits: 
    Early demo-ability — an easy opponent from very early in development, so the game is playable end-to-end long before the strong AI is finished.
    Natural scope control — each tier is a self-contained, gradable unit of work. If Tier 3 slips, Tiers 1 and 2 are still complete and shippable. 
    Built-in benchmarking — playing tiers against each other produces win-rate and move-quality data for the final report without needing an external            dataset.
    Difficulty selection — a weaker player can practice against Tier 1 or Tier 2, and a stronger player can be challenged by Tier 3, without any                 separate difficulty system. 

Why a strict engine-first sequencing?
Every AI tier and the UI both depend on one thing: a chess engine that correctly generates legal moves and detects check, checkmate, stalemate, and draws. Bugs here: illegal castling through check, missed en passant and incorrect promotion handling are the single biggest risk to the whole project, because they silently corrupt everything built on top. The team treats engine correctness as the Month 1 priority above all else, and holds a scripted test suite against known chess positions as a first-class deliverable, not an afterthought. 


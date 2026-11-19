# Hackathon submission

**Challenge chosen:** 03, The Quantum Trading Edge (role: quantitative investment researcher)

## Phase 1: Investigate (written before any experiment was run)

**The commercial decision.** Whether our firm should put $3M into the startup at a $25M
pre-money valuation. The committee's question is narrower than "is the physics real": does an
82% success rate in this game turn into a service a trading firm would pay for and a
competitor could not copy.

**How I read the protocol.** It is the CHSH game. Two parties who cannot talk win with
probability at most 75% using any classical strategy, and at most cos²(π/8) ≈ 85.4% using
shared entanglement. Both of the startup's numbers sit where they should if the demo is
honest: 74% is about the classical ceiling, and 82% is below the quantum ceiling.

**Initial hypothesis.** Do not invest on these terms. I expect the physics claim to hold up
and the business claim to fail, for three reasons I can test:

1. The game forbids communication, but the customer's two desks already share a private
   low-latency line. If one desk can send its bit to the other, a classical strategy wins
   100% of rounds at $0.001. "Better than any classical strategy" is only true inside the
   no-communication rule.
2. Entanglement cannot carry information. Each desk's answer on its own is a coin flip, so
   the service cannot replace the line.
3. The result was measured on 40 km of fibre. New York to London is about 5,570 km, and
   fibre loss is exponential in distance.

**The uncertainty that matters most.** Whether any real trading decision has the game's
shape: two desks that must each commit to a binary action faster than a message can cross
between them, with a payoff that rewards agreeing except when both private signals are 1.
If that situation does not occur, the rest is irrelevant.

**Evidence that would change my mind.**

- A named trading workflow where both desks must act inside the one-way latency of their
  line (tens of milliseconds for New York to London) and the payoff has the CHSH structure.
- Entanglement delivered between the two actual cities with enough quality to beat 75%, at
  a useful rate.
- A cost per round that stays far below the edge per round at that distance.

**Experiment plan.** Compare three alternatives on the startup's own game and payoff:
(A) best classical strategy without communication, (B) the entangled strategy at the
measured quality, (C) classical strategy using the line the desks already have.

1. Enumerate all 16 deterministic classical strategies to get the classical ceiling exactly.
2. Simulate the quantum protocol in Qiskit, ideal and with noise tuned to 82%, for 1,000
   rounds, and check that neither desk's answers reveal the other's input.
3. Test whether 820/1,000 and 740/1,000 are statistically distinguishable from 75%.
4. Convert each alternative to dollars per round, and find how many rounds the $50M claim needs.
5. Stress the two things the pitch depends on: distance (40 km to 5,570 km) and the
   decision deadline relative to the line's latency.
6. Vary the input statistics to see how fragile the edge is when the trading problem is not
   exactly the textbook game.

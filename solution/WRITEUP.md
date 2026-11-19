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

## Phase 2: Experiment

Code: `solution/chsh_experiment.py`. Outputs: `solution/results/chsh_decision.png`,
`results.md`, `results.json`. Checks: `tests/test_chsh.py`. Seed 20261119.

![Result figure](results/chsh_decision.png)

### Three alternatives on the startup's own game

| Alternative | Win rate | Net $ per round | Source |
| --- | --- | --- | --- |
| A. Classical, no communication | 75.0% | 50.00 | exact: all 16 strategies enumerated |
| B. Entangled, no communication, measured quality | 82.0% | 63.92 | startup's figure; reproduced in Qiskit Aer |
| B'. Entangled, perfect hardware | 85.4% | 70.63 | exact statevector; the physical ceiling |
| C. Classical over the desks' existing line | 100.0% | 100.00 | one desk sends its bit, the other picks the winning answer |

**The result a reviewer can verify in a minute:** there are only 16 deterministic classical
strategies. Eight win 75% of rounds, eight win 25%, none do better. The entangled circuit
gives cos²(π/8) = 85.36% for every input pair. Both are asserted in `tests/test_chsh.py`.

### Is the startup's measurement believable?

- **Quantum, 820/1,000.** 95% interval 79.5% to 84.3%. The chance a classical strategy
  scores this well by luck is 7 in 100 million. The physics claim holds.
- **Classical demo, 740/1,000.** 95% interval 71.2% to 76.7%, consistent with the 75%
  ceiling (p = 0.47). The startup did not sandbag its classical baseline.
- **82% is below the 85.4% ceiling**, so it is physically possible. It implies a pair
  quality (visibility) of 0.905; anything above 0.707 beats classical.
- **1,000 trials is noisy.** My seeded 1,000-round simulations returned 76.4% (classical),
  84.8% (ideal) and 80.5% (measured quality). Over 200,000 rounds the noisy simulation
  settles at 82.1%.
- **No information is transmitted.** Over 200,000 simulated rounds, desk A answered "1"
  between 49.9% and 50.1% of the time whatever desk B's input was.

### Unit economics

Reading chosen: the "$50M annual financial opportunity" is the trading firm's gross gain
from playing with the quantum protocol, not the startup's revenue. The payoff lands at the
desks; the startup can only charge a share of the value it adds.

- $50M at $64 gross per round is **781,250 rounds a year** (about 3,100 per trading day).
  A classical strategy needs 1,000,000 rounds for the same $50M.
- At the same 781,250 rounds, a free classical strategy earns $39.06M. The quantum protocol
  therefore adds **$10.9M a year, $13.92 per round**. That is the ceiling on what the firm
  would pay.
- The existing line would earn $78.1M on the same rounds.

| Take rate (share of $50M) | Fee to startup | Firm profit | Firm $ per trade | Startup profit per trade | Startup profit |
| --- | --- | --- | --- | --- | --- |
| 10% | $5.0M | $45.0M | 57.60 | 6.32 | $4.94M |
| 20% | $10.0M | $40.0M | 51.20 | 12.72 | $9.94M |
| 30% | $15.0M | $35.0M | 44.80 | 19.12 | $14.94M |
| Classical, no fee, same trades | 0 | $39.06M | 50.00 | | |

The firm is better off with free classical once the take rate passes 21.9%. If the firm can
simply run more rounds, it reaches $50M classically for $1,000 and pays the startup nothing.

### What is the line's delay worth?

The quantum protocol competes with the line only on time: it lets both desks act now
instead of waiting about 29 ms for a message to cross.

- Waiting for the line nets $100 minus whatever the delay costs. The entangled strategy
  nets $63.92. So **the delay must cost more than $36.08 per round**, 36% of the
  opportunity, before quantum wins.
- If the opportunity fades exponentially, that means a **half-life under 46 ms**, or about
  1.5 times the line's delay whatever the distance.
- **Line delay, checked against published data.** The fastest transatlantic cable, Hibernia
  Express, was tested at under 58.95 ms between New York and London [1]. I read that as a
  round trip, so 29.5 ms one way. My estimate from distance was 29.4 ms.
- **Block order, from published data.** In an NBER study of institutional algorithmic orders
  (2012 to 2016), the average order was about $287,000 worked over about 84 minutes [2].
  If the desk is chasing 20 basis points (my assumption), that is a $574 opportunity. Reading
  84 minutes as the half-life, a 29 ms wait costs **a quarter of a cent**: 0.0004% of the
  opportunity against the 36% needed. The order's half-life is about 110,000 times too long.
- The random price move over 29 ms on that order is about $5 (one standard deviation, at
  25% annual volatility), but it is as likely to help as to hurt, so it is risk, not cost.

### Do any trades fade that fast? Would this work for high-frequency trading?

**Yes, some trades fade that fast.** They are high-frequency arbitrage, not block orders.

- Arbitrage between S&P 500 futures in Chicago and the SPY fund in New York lasted a median
  of 97 ms in 2005 and 7 ms in 2011, with about a thousand opportunities a day [3].
- On the London Stock Exchange, races to trade on stale quotes last 5 to 10 millionths of a
  second and happen about once a minute per FTSE 100 stock. The sums at stake are about
  $5 billion a year across global equity markets [4].

**So high-frequency trading passes the time test.** At a 7 ms half-life, waiting 29 ms for
the line nets $5.43 a round against $63.92 for quantum.

**It also fixes the distance problem, which I had not expected.** For edges this short, a
short link is enough. The NYSE data centre in Mahwah and the Secaucus trading hub are 118
microseconds apart by the fastest wireless line [5], which is about 35 km and inside the
startup's 40 km test range. Between those two sites quantum would beat the line for any
opportunity with a half-life under 0.18 ms.

**It still fails on three other counts:**

- **Those trades are about moving information.** The futures price jumps in one place and
  the other venue has to find out. Entanglement carries no information, so it cannot win
  that race. The protocol only helps when each site has its own independent signal and
  neither needs to know the other's.
- **The pairs arrive too slowly.** 1,000 pairs a second is one pair per millisecond. A race
  decided in 5 to 10 microseconds is over 100 to 200 times faster than that. The desks would
  need a pair already waiting, which means quantum memory, and the case file mentions none.
- **The stakes are small.** The published work describes the average race as worth a small
  amount [4]. With a $0.08 running cost and a 7-point win-rate gain, quantum only pays for
  itself when the stake is above **$0.56 a round**, and the value added is 14% of the stake
  less 8 cents. The $100 stake in the case file is the startup's number.

High-frequency trading is therefore the one place the time condition holds, and it is a
different product from the block-order service in the pitch. Nothing in the case file shows
it passes the other conditions.

### Can the link reach?

- New York to London is 1,114 dB of fibre loss against 8 dB on the test link. The pair rate
  falls from 1,000 per second to about 10⁻¹⁰⁸ per second.
- With any noise floor in the range I swept, the win rate drops below 75% between 113 km
  and 312 km (panel 3). Even with no noise, the link delivers one pair an hour at 368 km.
- At 40 km, where the link works, a message takes 0.13 to 0.2 ms. That is far too fast
  for the line to lose on a block order, though not on a microsecond-scale trade (see the
  high-frequency section above).

### How robust is the edge to the game's shape?

If each desk's signal is 1 with a probability other than 50%, the edge shrinks fast. At the
measured quality it exists only when that probability is between 42% and 58% (panel 4).
Outside that range the desks do as well by ignoring the pair.

### Assumptions

| Assumption | Value | Why |
| --- | --- | --- |
| Win rates and costs | as in the case file | taken as the startup's claims; 82% and 74% checked against theory |
| Cost of using the existing line | $0 per round | the line is already paid for; the case file gives no figure. Quantum only wins if this exceeds $36.08 |
| "Classical $0.001" | cost of the no-communication demo | it is listed beside the quantum cost for the same protocol |
| Who bears $0.08 | the startup | it is selling a service on its own link |
| $50M | firm's gross gain with quantum | the payoff accrues to the desks |
| One round | one coordinated block-order decision | the startup's proposed first service |
| New York to London | 5,570 km great circle; 6,000 km fibre route; 29 ms one-way | geography and light speed in glass (index 1.47); matches the published 58.95 ms, read as round trip [1] |
| Fibre loss | 0.2 dB/km | standard telecom fibre |
| Noise | constant floor of 0.001 to 10 false pairs per second, white noise | swept over four orders of magnitude; the conclusion does not move |
| "1,000 pairs per second" | delivered rate at 40 km | the more favourable reading |
| Block order size and duration | $287,000 over 84 minutes | published average institutional order [2]; I read the working time as the opportunity's half-life |
| Block order edge and volatility | 20 bp; 25% a year | mine; the 46 ms break-even does not depend on either |
| Blocks need information exchanged | size, price and timing are shared between desks | my understanding of block trading, not a case fact |
| Block signals are not independent | both desks work the same order | my understanding, not a case fact |
| Blocks are infrequent | far fewer than 3,100 a day per pair of desks | my judgement; blocks of 10,000 shares or more are about 0.03% of S&P 500 trades [6] |
| Fast trades exist | 7 ms median (2011) for index arbitrage; 5 to 10 microseconds for equity races | published [3][4] |
| Exchange data centres | 118 microseconds apart one way, about 35 km | published latency [5]; distance is my conversion at light speed |
| Take rates | 10%, 20%, 30% | illustrative |

## Phase 3: Recommendation

**To:** Investment Committee. **Re:** $3M at $25M pre-money in the entangled-coordination startup.

**Recommendation: do not invest on these terms.** The physics is real. It does not create a
defensible business in the market the startup has chosen.

**What we found**

1. **The measurement is sound.** 82% over 1,000 trials cannot be explained by a classical
   strategy (odds of 7 in 100 million), and the startup's 74% classical baseline is fair.
2. **The comparison is the wrong one.** "Better than any classical strategy" holds only if
   the desks cannot talk. The customer's desks share a private line, which wins every round.
   Per round: line $100, quantum $63.92, silent classical $50.
3. **Time is the only thing the product can sell, and block orders do not need it.** Quantum
   beats the line only when a 29 ms wait destroys more than 36% of a trade's value, which
   means a half-life under 46 ms. The average institutional order is worked over 84 minutes;
   for it, the same wait costs a quarter of a cent on a $574 opportunity. Trades that do
   fade that fast exist in high-frequency arbitrage (7 ms, down to microseconds), but those
   are races to move information, which entanglement cannot do.
4. **The $50M is mostly not theirs.** Read as the customer's gain, it needs 781,250 rounds a
   year, and $39M of it is available from a free classical strategy. The value added is at
   most $10.9M a year, the startup keeps a fraction of that, and only where the line cannot
   be used.
5. **The link does not reach.** The result is from 40 km. Extending the same fibre link loses
   the edge within roughly 110 to 310 km; New York to London is 5,570 km. The $0.08 per round
   excludes the cost of a transatlantic quantum link, which the startup has not shown it can
   build.
6. **The edge is fragile.** It needs the trading problem to match the game exactly,
   including near-50/50 independent signals.

**Conditions for profitability.** All five must hold at once. `D` is what a trade loses
while the desks wait for the line.

| # | Condition | Threshold | Block orders | High-frequency arbitrage |
| --- | --- | --- | --- | --- |
| 1 | Waiting for the line costs more than quantum's shortfall | `D` over $36.08 a round; half-life under 1.5 times the line delay (46 ms New York to London) | Fails: 84 minutes, `D` is $0.002 | Passes: 7 ms down to microseconds |
| 2 | Each desk can act without knowing what the other saw | entanglement carries no message | Fails: desks share size, price, timing (my assumption) | Fails: the trade is the news from the other venue |
| 3 | The payoff has the game's shape | independent signals, each 42% to 58% likely, "match unless both are 1" | Fails: same order at both desks (my assumption) | Not shown |
| 4 | Pairs arrive in time and good enough | win rate over 75.04% at the real distance; a pair ready when needed | Fails: 5,570 km against a limit of about 110 to 310 km | Distance passes at about 35 km; timing fails, one pair per ms against races of 5 to 10 microseconds |
| 5 | The fee covers costs and leaves the firm better off | fee between $0.08 and the value added, which is $63.92 minus the larger of $50 and $100 minus `D`, so at most $13.92; stake above $0.56 | Fails: nothing added | Unclear: stakes per race are small |

Startup profit is rounds times (fee minus $0.08), less the cost of the link.

**Did the initial hypothesis survive?** Yes, with two corrections. I expected the line to
make the quantum protocol pointless in every case. The experiment shows a regime where that
is wrong: trades that fade within milliseconds, which published data confirms exist in
high-frequency arbitrage. I also expected distance to rule the link out everywhere, and it
does not: exchange data centres about 35 km apart are within its tested range. Neither
correction rescues the pitch. The proposed service is block orders, which fail the time
test by a factor of about 110,000, and high-frequency arbitrage fails on information, pair
timing and stake size. The experiment also changed how I read the $50M, from "implausible"
to "mostly attributable to something free".

**What would change the recommendation**

- A named customer workflow that passes all five conditions above: in particular a
  half-life under 1.5 times the line delay, and two independent local signals.
- Evidence of quantum memory, or a pair rate high enough to have a pair ready within the
  life of the trade.
- Entanglement delivered between two real trading venues with pair quality above 0.71.
- The raw trial data, including whether rounds with a lost photon were counted. If they
  were dropped, 82% overstates what a desk that must answer every round would get.

**Under what circumstances this could work.** The same five conditions, turned into a
description of the customer the startup would need:

- **Two sites that each see their own signal.** Neither site needs the other's news; they
  only need their actions to line up. This rules out arbitrage between venues, where the
  whole trade is the news from the other side.
- **A decision that expires faster than the line can deliver.** The opportunity's half-life
  must be under 1.5 times the line delay. Between exchange data centres 118 microseconds
  apart, that is under 0.18 ms.
- **Sites within the link's proven range.** That is tens of kilometres, such as the New
  Jersey exchange data centres at about 35 km, and not across an ocean.
- **A pair already waiting when the signal arrives.** For decisions made in 5 to 10
  microseconds that means stored pairs, or more than 100,000 pairs a second against today's
  1,000.
- **A payoff with the game's shape and enough at stake.** Signals close to 50/50, "match
  unless both are 1", more than $0.56 at stake per round, and enough rounds to pay for the
  link.

I could not find a trading workflow that meets all five. The startup would need to name one.

**How the startup should change the pitch**

| Current pitch | What it should say instead |
| --- | --- |
| "Better than any classical strategy" | "Better than any strategy where the desks cannot communicate in time", with the customer's own line as the comparison |
| Block orders between New York and London | Microsecond decisions between data centres tens of kilometres apart, where the link has been shown to work |
| $50M annual opportunity | Value added per round over the customer's best alternative: 14% of the stake less $0.08, multiplied by a volume the customer confirms |
| 82% against 74% over 1,000 trials | A larger sample, with rounds where a photon was lost counted as answered classically |
| 1,000 pairs a second on a test link | A pair ready within the life of the trade, by storage or a much higher rate |
| A trading service at a $25M valuation | A fee set as a share of value added (the firm walks away above about 22% of its gross gain), and a raise tied to signing one customer whose workflow passes the five conditions |

If no such customer exists, the more honest pitch is the hardware: a working 40 km
entanglement link, sold into uses where proving the absence of communication is the product.

**What I would do next**

- Send the startup those requests before any further diligence spend.
- Ask what the three patents cover. If they cover the source or the link hardware, the asset
  may be worth more in markets where the absence of communication is the point and a
  certified violation is the product: secure key exchange and certified randomness. That is
  my suggestion, not something in the case file, and it would be a different investment
  at a different valuation.

## Sources

1. Hibernia Express latency: https://www.submarinenetworks.com/en/systems/trans-atlantic/project-express/hibernia-express-connects-new-york-to-london-in-under-58-95ms
2. Average institutional parent order (NBER conference paper): https://conference.nber.org/conf_papers/f145256/f145256.pdf
3. Budish, Cramton and Shim, "The High-Frequency Trading Arms Race", QJE 2015: https://conference.nber.org/conf_papers/f69665.pdf ; summary: https://www.richmondfed.org/publications/research/econ_focus/2015/q3/research_spotlight
4. Aquilina, Budish and O'Neill, "Quantifying the High-Frequency Trading Arms Race", QJE 2022: https://www.nber.org/system/files/working_papers/w29011/w29011.pdf
5. ICE wireless latency, New Jersey metro: https://www.ice.com/market-data/connectivity-and-feeds/wireless/new-jersey-metro
6. Liquidnet, "Defining a Block in the 21st Century": https://www.liquidnet.com/expert-insights/defining-a-block-in-the-21st-century

## How to run

```
uv sync
uv run python solution/chsh_experiment.py
uv run python -m pytest tests/test_chsh.py
```

Runs in under a minute on a laptop. The quantum circuits are simulated on Qiskit Aer.

## Author's note

I do a lot of investment work, and most of it comes down to quantifying a business. That
is why I approached this challenge through unit economics before the physics. I did not
want to judge the startup on whether 82% beats 74%. I wanted to know what one round is
worth, to whom, and who pays for it.

That habit set the questions I asked. How many rounds does $50M imply? What does each
strategy earn per round? If the startup takes a fee, what is left for the trading firm, and
at what fee does the firm walk away? Who bears the running cost?

The part that interested me most was putting a number on time and on edge. The startup's
product only competes with the desks' existing line on speed, so its value should equal
what a trade loses while waiting for that line. Once that was written as dollars per round,
the answer was clear. An edge has to fade within milliseconds for the product to matter,
and the investing it was pitched for does not work on that clock. Working that through is
what convinced me the claim would not be valid in an investing setting.

## How AI was used

Claude Code (Claude Fable 5.2) was used throughout, with me directing the analysis.

- **AI did:** recognised the protocol as the CHSH game, wrote the simulation, statistics,
  distance model and figure, and drafted this write-up.
- **I directed:** the unit-economics framing. I asked for the rounds implied by $50M, the
  profit per round for each strategy, the firm-versus-startup split under a take rate, who
  bears the operating cost, a dollar value for the line's delay, the conditions for
  profitability, and published data to replace the AI's placeholder assumptions.
- **Where I corrected the AI:** it had applied the $0.001 classical cost to the existing
  line. That figure belongs to the no-communication demo; the line's cost is now a stated
  assumption with a break-even.
- **Where the AI corrected me:** my first equation for the rounds applied the win rate to
  the number of wins a second time.
- **Checks on the AI's output:** exact enumeration and exact statevector as baselines for
  the simulation; the simulation was not reproducible at first because the sampler ignored
  the seed, which was caught by running it twice and fixed; a sensitivity curve that went
  negative was corrected, since desks can always ignore a bad pair.

## Limitations and next steps

- The distance model is a simple one (constant noise floor, direct fibre). Satellites or
  quantum repeaters would change it, and the case file gives no evidence of either.
- The value-of-time result assumes exponential decay of the opportunity. The 36% threshold
  does not depend on that; the 46 ms half-life does.
- The take rates, the 20 bp edge and the reading of 84 minutes as a half-life are my
  assumptions. The statements about how block desks coordinate are my understanding.
- The published figures were taken from search summaries of the sources in the time
  available, not from reading each paper in full. The 97 ms and 7 ms figures come from a
  Richmond Fed summary of [3]. The 58.95 ms figure is not labelled one-way or round trip
  in the coverage; round trip fits the cable's length.
- The sensitivity to signal bias covers equal bias at both desks only, not correlated signals.
- Nothing was run on real quantum hardware; the 82% is the startup's number.

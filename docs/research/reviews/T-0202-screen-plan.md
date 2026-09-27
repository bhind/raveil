# T-0202: Candidate screen fixed before new parameter analysis

Date: 2026-09-27; Issue274; ADR-0103 / RFC-0007. Owner broadly approves this
combined source review and candidate selection/rejection. No performance EXP,
new hardware or numerical-contract change. Pre-screen base is PR273 main
`827aa83225e2591be8a0633255daf03b1a332cb9`.

Reuse exactly T-0200 layer0 W512x128/b512 and its eight commissioning vectors.
No layer1/2, seeds2002/2003, activation data, refetch or training. These weights
have already been functionally used in T-0200/0201; this is a prospective plan
for new structural scans, not a claim that nobody has seen their values.

## Fixed candidate set and discriminators

1. Same-column exact coefficient-product sharing. Count distinct raw F16 bit
   patterns per column; preserve signs including zero. Compute each distinct
   c*x_j once and add in the original per-row j order. Functional witness must
   be bitwise equal to T-0200 serial and pass its exact oracle. Report original
   coefficient uses65536, unique products, all65536 add/incidence uses, dictionary
   values, uint16 local IDs, uint32 offsets, bias and temporary products. This
   is a known CSE control even if ordinary clang did not find it.
2. Sign / power-of-two factoring. Count distinct absolute values and distinct
   odd integer significands per column using the independent F16 integer
   decoder. Count required per-use signs/scales. Product-count-only savings
   cannot hide those operations or claim shift wiring is free on a CPU. Treat
   as MCM/CMVM overlap; only structural counts, not an implemented optimized kernel.
3. Common input linear forms / CSE. Count exact repeated coefficient pairs for
   fixed adjacent column pairs (0,1),(2,3),..., and zero coefficients. This scan
   is deliberately bounded; absence of adjacent repeats cannot rule out other
   pairings, proportional forms, deeper DAGs or a better CSE search. Prior-art
   algorithms and new objectives must be distinguished, not equated just because
   both can be expressed as DAGs.
4. Exact dense low-rank bottleneck W=UV. Compute modular rank with independently
   checked primes65521/65519. Full column rank in either field proves rational
   rank128 for this dyadic matrix, rejecting r<128. It does not rule out sparse
   full-rank factorizations or other circuits. Dense factor cost640r multiplies;
   below65536 requires r<=102. No approximate SVD or weight replacement.
5. Preselected Walsh-Hadamard input basis T=H, W'=WH/128. Compute WH in integers;
   count exact zeros and whether each transformed coefficient is exactly F32
   representable. Add896 transform additions before any matvec costs. Do not
   round W' into a different function. One rejected basis says nothing about all
   possible bases. No basis tuning after results.
6. Bit decomposition / DA/LUT. Analyze exact integer-grid input width, table
   exponent/partition growth, storage and shift/add costs; do not build a huge
   LUT. Classic DA and da4ml are direct prior-art screens. The F16 domain can
   embed exactly into a fixed-point grid, but evaluating a finer/dense domain,
   wider accumulators and decoding all cost work. Different host/hardware cost
   models do not create mechanism novelty.
7. Error-certified algebra / symbolic schedule search. Screen Mirage (OSDI2025),
   Prism (2026v1), Daisy and matrix-CSE. A finite-field identity or random float
   testing does not prove gamma258; conversely adding an error checker alone is
   not a new algorithm. No external implementation adoption in this task.

## Decision rule fixed before scan

Select a Raveil mechanism only when its concrete transform/search algorithm
has an identified difference from the closest reviewed methods, preserves the
unchanged real function and roundoff contract, and has a defensible cost path
including representation, fan-out, preparation/replacement and execution.
Otherwise reject **that candidate as a current novelty proposal**, while
retaining useful known controls and explicitly inconclusive search questions.
No arbitrary percentage cutoff, forced winner, performance inference or
universal impossibility claim. A representation family match is evidence of
known ingredients, not proof that every algorithm in the family is already known.

The screen may select known CSE as a baseline without selecting a novel
mechanism. Product counts are analytical, not timings/energy/area/traffic.
Compiler failure in four T-0201 variants is never proof of an algorithmic lower
bound. Even a real frontend reduction applies to conventional backends too;
it does not establish a Groq-specific weakness or hardware contribution.

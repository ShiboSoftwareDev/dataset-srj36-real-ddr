# Real DDR memory reproductions

![Source boards for the captured DDR memory workloads](../previews/samples.png)

The screenshot shows unrouted source inputs. H3 is sample001; A64 is sample002.

`a64-ddr-cmn142-resized-search.json.gz` is the exact Pipeline 9 constructor
checkpoint from A64 region `cmn_142`: 38 terminals, 19 local route requests, and
2,133 contextual obstacles. Its provenance records the source, router revision
and decompressed SHA-256. It is not itself an SRJ board sample.

`h3-ddr-displaced-port-pair.json` captures the physical shared-edge geometry
hidden by displaced duplicate ports in the H3 input.

The executable reproductions live in the autorouter stack:

```sh
# In tscircuit-autorouter, on the repro or fix branch:
timeout 120s bun scripts/repro-ddr-resized-search.ts --report /tmp/ddr-memory.json
bun test tests/repro/pipeline9-a64-ddr-resized-search-allocation.test.ts --timeout 9999999
bun test tests/repro/pipeline9-h3-ddr-displaced-port-geometry.test.ts --timeout 9999999
```

The allocation test is expected-failing on [#3331](https://github.com/tscircuit/tscircuit-autorouter/pull/3331)
and an ordinary passing test on [#3332](https://github.com/tscircuit/tscircuit-autorouter/pull/3332).
The guarded CLI stops at its RSS/time limits and exits 2; a resource stop is
never counted as solved. Use identical Bun versions and limits on both revisions.

For full SRJ board comparisons, use the pinned samples and identical benchmark
harness from #3331/#3332. Its `highDensityStage` resource checkpoint records
completion of that stage separately from full-board routing and DRC. Parent-side
Linux RSS sampling remains active if the routing child blocks or reaches a
resource limit.

The [recorded five-board comparison](../README.md#measured-baseline-and-fix) uses
baseline `df79cbbb` and fix `dce08687` on one Blacksmith runner. H3 completes
high-density routing only with the fix (143.4 seconds, 1,700.2 MiB through the
stage), but both full-board runs time out. A64 and STM32MP157 time out in
high-density routing on both revisions. OrangeCrab and A13 finish routing on
both, with relaxed DRC failures. Stage completion therefore rises from 2/5 to
3/5 while full-board completion stays 2/5 and DRC passes stay 0/5. The full-run
H3 peaks of 7,185.1 / 1,700.9 MiB are measurements through different timeout
phases, not two successfully completed boards.

The [measurement JSON](../benchmarks/2026-10-28-srj36.json) includes immutable
input hashes, runtime, limits, per-board outcomes and stage checkpoints;
[log excerpts](../benchmarks/2026-10-28-srj36-log.txt) preserve the printed evidence.

The [H3 force-improvement follow-up](../README.md#h3-force-improvement-follow-up)
captures region `cmn_9` with 23 routes and 2,459 points. Its regression fixtures
are in autorouter #3341 and repair01 #41; the indexed solver preserves the
original 110,746-byte route output after all 20 force steps. The full-board paired
run completes force improvement in 168.4 seconds with the new pin, while the
parent is unfinished after 223.0 seconds in that stage. Both boards still time
out at 360 seconds, with the candidate now in high-density repair. DRC is not
reached. [The evidence JSON](../benchmarks/2026-10-28-h3-force-clearance.json)
records immutable revisions, phase timings, peaks and the 85-board control.

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

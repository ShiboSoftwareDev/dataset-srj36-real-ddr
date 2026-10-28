# dataset-srj36-real-ddr

Five captured routing inputs from real CPU/FPGA + DDR3 boards. These preserve the
placement, pad obstacles, signal nets, passive endpoints, layer restrictions and
routing rules used to investigate the A64/H3 DDR memory problems in
[autorouter #3331](https://github.com/tscircuit/tscircuit-autorouter/pull/3331) and
[#3332](https://github.com/tscircuit/tscircuit-autorouter/pull/3332).

![All five real DDR input samples; colored lines are unrouted connectivity](previews/samples.png)

The screenshot shows **unrouted inputs**, with straight ratsnest lines between
signal endpoints. It does not show completed routing or DDR timing validation.
Individual SVG and PNG previews are in [previews/](previews/).

| Sample | Board | Layers | DDR nets | Terminals | Pad obstacles |
| --- | --- | ---: | ---: | ---: | ---: |
| [001](samples/sample001.json) | Allwinner H3 DDR3 16x1 | 2 | 53 | 108 | 479 |
| [002](samples/sample002.json) | OLIMEX A64-OLinuXino rev H | 6 | 75 | 184 | 2,122 |
| [003](samples/sample003.json) | OLIMEX STMP157-OLinuXino-LIME2 rev B1 | 8 | 72 | 201 | 2,080 |
| [004](samples/sample004.json) | OrangeCrab rev 0.2.1 ECP5 DDR3 | 6 | 50 | 102 | 893 |
| [005](samples/sample005.json) | Allwinner A13 SBC | 4 | 96 | 192 | 895 |

## Install and use

Follow the [dataset conventions](https://github.com/tscircuit/handbook/blob/main/guides/dataset-guidelines.md):
plain `index.js`, lightweight `index.d.ts`, checked-in JSON, no transpilation and
no npm publication. Install from GitHub; pin a commit for reproducible comparisons.

```sh
bun add https://github.com/ShiboSoftwareDev/dataset-srj36-real-ddr
```

```js
import { dataset, sample002 } from "@tscircuit/dataset-srj36-real-ddr"
console.log(Object.keys(dataset), sample002.layerCount)
```

## Benchmark scope

The autorouter integration registers these as `36` / `srj36`, using Pipeline 9.
The first two samples retain the board contexts that exposed the memory bugs;
the remaining three provide related real DDR workloads. Inputs are not filtered
to boards known to finish routing.

```sh
# In the autorouter checkout after SRJ36 integration:
./benchmark.sh --pipeline 9 --dataset 36 --sample-numbers 1,2 \
  --concurrency 1 --sample-timeout 1200s
```

Compare the same inputs and routing rules on baseline and fixed revisions, one
board at a time. Record per-board peak RSS, time, stage reached, completion and
DRC. Run the high-density stage comparison separately from complete-board routing.
Passing high-density routing does not establish complete-board DRC or DDR timing.
The historical A64 stage comparison was still 8.59 GiB after the fix.

The current single-thread benchmark loses progress-timer updates while its
synchronous solve runs. For killed/timed-out samples its last reported RSS may
be stale. Use an external process memory monitor for capped comparisons; do not
interpret startup RSS as peak RSS or a timeout as a successful solve.

The exact local checkpoints and commands are documented in [repro/README.md](repro/README.md).

## Extraction and integrity

Each sample is byte-identical to its captured DDR-assessment input. The manifest
records its SHA-256; each [provenance file](provenance/) identifies the upstream
repository, immutable source commit/path/hash, chip references and transformations.

All named DDR signal nets incident to the selected CPU/FPGA or RAM are retained,
including multi-terminal nets and passive endpoints. Power, VREF, ZQ and
unconnected nets are excluded. Existing traces, vias and zones are removed.
There is no artificial widening, layer-count increase, or reduction to 16 nets.

Board edges use a bounding rectangle. Roundrect, oval and custom pad shapes use
the recorded rectangular approximations. Native KiCad pad primitives remain
separate obstacles, so an obstacle count is not necessarily a physical ball count.
Global clearance uses the maximum selected-net clearance; via dimensions use
existing DDR copper where available. The bus preserves allowed signal layers;
no timing, skew, impedance or differential-pair constraints are invented.

```sh
node scripts/validate.mjs       # no dependencies required; Node 22+ / Bun
bun install                    # development dependencies for preview rendering
bun run snapshots
python3 scripts/fetch-sources.py
python3 scripts/extract-kicad.py # checks regenerated inputs against captured hashes
```

Source licensing is recorded per sample in [LICENSE](LICENSE) and the provenance
files. Upstream notices are preserved in [licenses/](licenses/).

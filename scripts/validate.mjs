import assert from "node:assert/strict"
import { createHash } from "node:crypto"
import { readFileSync, readdirSync } from "node:fs"
import { gunzipSync } from "node:zlib"
import dataset, * as exported from "../index.js"

const root = new URL("../", import.meta.url)
const manifest = JSON.parse(readFileSync(new URL("manifest.json", root)))
const expectedIds = ["sample001", "sample002", "sample003", "sample004", "sample005"]
assert.equal(manifest.sampleCount, 5)
assert.deepEqual(Object.keys(dataset), expectedIds)
assert.deepEqual(manifest.samples.map((sample) => sample.id), expectedIds)
assert.deepEqual(readdirSync(new URL("samples/", root)).sort(), expectedIds.map((id) => `${id}.json`))

for (const sample of manifest.samples) {
  const raw = readFileSync(new URL(sample.file, root))
  const srj = dataset[sample.id]
  const provenance = JSON.parse(readFileSync(new URL(sample.provenance, root)))
  assert.equal(exported[sample.id], srj)
  assert.deepEqual(srj, JSON.parse(raw))
  assert.equal(createHash("sha256").update(raw).digest("hex"), sample.sha256)
  assert.equal(sample.sha256, provenance.sampleSha256)
  assert.match(provenance.commit, /^[0-9a-f]{40}$/)
  assert.match(provenance.sourceSha256, /^[0-9a-f]{64}$/)
  assert.equal(srj.layerCount, sample.layerCount)
  assert.equal(srj.connections.length, sample.connectionCount)
  assert.equal(srj.obstacles.length, sample.obstacleCount)
  assert.equal(new Set(srj.connections.map((connection) => connection.name)).size, srj.connections.length)
  assert.equal(new Set(srj.obstacles.map((obstacle) => obstacle.obstacleId)).size, srj.obstacles.length)
  assert.ok(srj.bounds.minX < srj.bounds.maxX && srj.bounds.minY < srj.bounds.maxY)
  assert.ok(srj.minTraceWidth > 0 && srj.minViaPadDiameter > srj.minViaHoleDiameter)
  assert.equal(srj.traces?.length ?? 0, 0)
  assert.equal(srj.differentialPairs?.length ?? 0, 0)
  assert.equal(srj.allowViaInPad, false)
  const ports = new Set(srj.obstacles.map((obstacle) => obstacle.circuitJsonMetadata?.pcb_port_id).filter(Boolean))
  let terminals = 0
  for (const connection of srj.connections) {
    assert.ok(connection.pointsToConnect.length >= 2)
    assert.ok(connection.nominalTraceWidth > 0)
    terminals += connection.pointsToConnect.length
    for (const point of connection.pointsToConnect) {
      assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y))
      assert.ok(ports.has(point.pcb_port_id), `${sample.id}: missing physical port ${point.pcb_port_id}`)
      assert.ok(point.layer || point.layers?.length)
    }
  }
  assert.equal(terminals, sample.terminalCount)
  for (const bus of srj.buses) {
    assert.deepEqual(bus.connectionNames, srj.connections.map((connection) => connection.name))
    assert.deepEqual(bus.allowedLayers, provenance.signalLayers)
    assert.equal(bus.maxLengthSkew, undefined)
  }
  for (const ref of sample.chipReferences) {
    assert.ok(srj.obstacles.some((obstacle) => obstacle.componentId === ref))
  }
  assert.ok(readFileSync(new URL(`previews/${sample.id}.png`, root)).subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])))
}

const a64 = gunzipSync(readFileSync(new URL("repro/a64-ddr-cmn142-resized-search.json.gz", root)))
assert.equal(createHash("sha256").update(a64).digest("hex"), "4252c7e47c6ef5bb811338b5c9733c56f7b6344ba8a9f39123705e10fde70e4a")
assert.ok(dataset.sample002.connections.some((connection) => connection.pointsToConnect.length > 2))
const readme = readFileSync(new URL("README.md", root), "utf8")
assert.ok(readme.includes("previews/samples.png"))
assert.ok(readFileSync(new URL("previews/samples.png", root)).length > 1000)
console.log("Validated five immutable DDR inputs, physical endpoints, source metadata, checkpoints and previews")

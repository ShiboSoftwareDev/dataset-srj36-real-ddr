import { readFileSync, writeFileSync, mkdirSync } from "node:fs"
import { getSvgFromGraphicsObject } from "graphics-debug"
import { convertSrjToGraphicsObject } from "@tscircuit/capacity-autorouter"
import { Resvg } from "@resvg/resvg-js"
import dataset from "../index.js"

const root = new URL("../", import.meta.url)
const manifest = JSON.parse(readFileSync(new URL("manifest.json", root)))
const cardWidth = 720
const cardHeight = 540
const escape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;")
const cards = []
mkdirSync(new URL("previews/", root), { recursive: true })

for (const [index, entry] of manifest.samples.entries()) {
  const input = dataset[entry.id]
  const graphics = convertSrjToGraphicsObject(input)
  graphics.points = []
  graphics.lines = input.connections.flatMap((connection, connectionIndex) =>
    connection.pointsToConnect.slice(1).map((point) => ({
      points: [connection.pointsToConnect[0], point],
      strokeWidth: input.minTraceWidth,
      strokeColor: ["#2563eb", "#059669", "#9333ea", "#d97706", "#0891b2", "#be185d", "#4f46e5", "#65a30d"][connectionIndex % 8],
      label: `${connection.name} unrouted ratsnest`,
    })),
  )
  graphics.rects.push({
    center: { x: (input.bounds.minX + input.bounds.maxX) / 2, y: (input.bounds.minY + input.bounds.maxY) / 2 },
    width: input.bounds.maxX - input.bounds.minX,
    height: input.bounds.maxY - input.bounds.minY,
    fill: "transparent",
    stroke: "#94a3b8",
  })
  const boardSvg = getSvgFromGraphicsObject(graphics, { backgroundColor: "white", includeTextLabels: false, svgWidth: 680, svgHeight: 410 })
  writeFileSync(new URL(`previews/${entry.id}.svg`, root), boardSvg)
  writeFileSync(new URL(`previews/${entry.id}.png`, root), new Resvg(boardSvg).render().asPng())
  const title = entry.title.replace("OLIMEX ", "").replace("OLinuXino", "OLinuXino")
  const inner = boardSvg.replace(/<\?xml[^>]*>/g, "").replace(/<svg\b/, '<svg x="20" y="106"')
  const card = `<svg xmlns="http://www.w3.org/2000/svg" width="${cardWidth}" height="${cardHeight}" viewBox="0 0 ${cardWidth} ${cardHeight}"><rect x="8" y="8" width="704" height="524" rx="12" fill="white" stroke="#cbd5e1"/><text x="24" y="42" font-family="DejaVu Sans,sans-serif" font-size="17" fill="#475569">${entry.id} · ${escape(entry.boardId.toUpperCase())}</text><text x="24" y="72" font-family="DejaVu Sans,sans-serif" font-size="23" font-weight="bold" fill="#0f172a">${escape(title)}</text><text x="24" y="96" font-family="DejaVu Sans,sans-serif" font-size="16" fill="#475569">${entry.layerCount} layers · ${entry.connectionCount} DDR nets · ${entry.obstacleCount.toLocaleString("en-US")} pad obstacles</text>${inner}</svg>`
  const x = index % 3 * cardWidth
  const y = Math.floor(index / 3) * cardHeight + 104
  cards.push(card.replace(/<svg\b/, `<svg x="${x}" y="${y}"`))
}

const sheet = `<svg xmlns="http://www.w3.org/2000/svg" width="2160" height="1196" viewBox="0 0 2160 1196"><rect width="2160" height="1196" fill="white"/><text x="32" y="46" font-family="DejaVu Sans,sans-serif" font-size="32" font-weight="bold" fill="#0f172a">SRJ36 · Real DDR routing workloads</text><text x="32" y="78" font-family="DejaVu Sans,sans-serif" font-size="20" fill="#475569">Original placement and pad obstacles · colored lines show unrouted DDR connectivity</text>${cards.join("")}<g transform="translate(1468 710)" font-family="DejaVu Sans,sans-serif" fill="#0f172a"><text font-size="27" font-weight="bold">Five captured real boards</text><text y="48" font-size="20">H3: physical shared-edge regression</text><text y="86" font-size="20">A64: enlarged retry allocation regression</text><text y="146" font-size="19" fill="#475569">No pre-routed copper or invented timing rules.</text><text y="184" font-size="19" fill="#475569">Multi-terminal nets and passive endpoints retained.</text><text y="222" font-size="19" fill="#475569">These are input previews, not solved-board results.</text></g></svg>`
writeFileSync(new URL("previews/samples.svg", root), sheet)
writeFileSync(new URL("previews/samples.png", root), new Resvg(sheet).render().asPng())
console.log("Rendered five input SVG/PNG pairs and previews/samples.png")

/** Lightweight routing input types. All additional source fields are preserved. */
export interface SimpleRouteJson {
  layerCount: number
  minTraceWidth: number
  minViaPadDiameter: number
  minViaHoleDiameter: number
  defaultObstacleMargin: number
  bounds: { minX: number; minY: number; maxX: number; maxY: number }
  obstacles: Array<Record<string, unknown>>
  connections: Array<{
    name: string
    pointsToConnect: Array<{
      x: number
      y: number
      layer?: string
      layers?: string[]
      [key: string]: unknown
    }>
    [key: string]: unknown
  }>
  [key: string]: unknown
}
export declare const sample001: SimpleRouteJson
export declare const sample002: SimpleRouteJson
export declare const sample003: SimpleRouteJson
export declare const sample004: SimpleRouteJson
export declare const sample005: SimpleRouteJson
export declare const dataset: Record<"sample001" | "sample002" | "sample003" | "sample004" | "sample005", SimpleRouteJson>
export default dataset

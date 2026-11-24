// 커리어 지도 3D 지구본용 육지 윤곽 생성 → data/geo/globe_land.json (한 번만 실행, 결과를 커밋)
// 준비: npm i topojson-client@3 world-atlas@2   (사이트 빌드에는 필요 없음)
// 사용: node scripts/geo_globe.mjs [출력 경로]
// basemap.json(평면 지도)과 같은 Natural Earth 110m 육지를 투영하지 않은 위경도 다각형으로 저장합니다.
// 지구본은 deck.gl GlobeView 가 그리므로 투영 계수는 필요 없습니다.
import { feature } from 'topojson-client';
import { readFileSync, writeFileSync } from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const land110 = JSON.parse(readFileSync(require.resolve('world-atlas/land-110m.json'), 'utf8'));
const out = process.argv[2] || 'data/geo/globe_land.json';
const r = (v) => Math.round(v * 100) / 100;               // 0.01° ≈ 1 km — 110m 윤곽에는 충분
const f = feature(land110, land110.objects.land);       // FeatureCollection 또는 Feature
const geoms = (f.features || [f]).map((x) => x.geometry);
const polys = geoms.flatMap((g) => (g.type === 'MultiPolygon' ? g.coordinates : [g.coordinates]))
  .map((poly) => poly.map((ring) => ring.map(([x, y]) => [r(x), r(y)])))
  .filter((poly) => !poly[0].every(([, y]) => y < -60));  // 남극 제외 (평면 지도와 같게)
writeFileSync(out, JSON.stringify(polys));
console.log('✔', out, polys.length, 'polygons', Math.round(JSON.stringify(polys).length / 1024) + 'KB');

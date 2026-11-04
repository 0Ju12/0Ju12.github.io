// 커리어 지도 바탕 지도 생성 → data/geo/basemap.json (한 번만 실행, 결과를 커밋)
// 준비: npm i d3-geo@3 topojson-client@3 world-atlas@2   (사이트 빌드에는 필요 없음)
// 사용: node scripts/geo_base.mjs [출력 경로]
// 세계: Equal Earth 투영(남극 제외 영역에 맞춤), 한반도 확대: Mercator. 점 투영 계수(k, tx, ty)도 함께 저장해
// build.py 가 같은 공식으로 위경도 → 화면 좌표를 계산합니다.
import { geoEqualEarth, geoMercator, geoPath } from 'd3-geo';
import { feature, merge } from 'topojson-client';
import { readFileSync, writeFileSync } from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const atlas = (n) => JSON.parse(readFileSync(require.resolve(`world-atlas/${n}`), 'utf8'));
const out = process.argv[2] || 'data/geo/basemap.json';
const r = (v) => Math.round(v * 100) / 100;
const round = (d) => d.replace(/-?\d+\.\d+/g, (m) => String(Math.round(parseFloat(m) * 10) / 10));

// 세계
const land110 = atlas('land-110m.json');
const land = feature(land110, land110.objects.land);
const W = 1000, H = 470;
const frame = { type: 'MultiPoint', coordinates: [] };
for (let lon = -180; lon <= 180; lon += 10) frame.coordinates.push([lon, -56], [lon, 80]);
const pw = geoEqualEarth().fitExtent([[4, 4], [W - 4, H - 4]], frame).clipExtent([[0, 0], [W, H]]);
const pathW = geoPath(pw);
const world = { w: W, h: H, k: r(pw.scale()), tx: r(pw.translate()[0]), ty: r(pw.translate()[1]),
  land: round(pathW(land)) };

// 한반도 확대
const c50 = atlas('countries-50m.json');
const all = feature(c50, c50.objects.countries).features;
const kr = all.filter((f) => f.id === '410');
const ctx = all.filter((f) => ['408', '392', '156', '643'].includes(f.id));
const KW = 300, KH = 340;
const box = { type: 'MultiPoint', coordinates: [[124.6, 33.0], [130.0, 33.0], [124.6, 38.7], [130.0, 38.7]] };
const pk = geoMercator().fitExtent([[10, 10], [KW - 10, KH - 10]], box).clipExtent([[0, 0], [KW, KH]]);
const pathK = geoPath(pk);
const korea = { w: KW, h: KH, k: r(pk.scale()), tx: r(pk.translate()[0]), ty: r(pk.translate()[1]),
  kr: round(pathK({ type: 'FeatureCollection', features: kr })), ctx: round(pathK({ type: 'FeatureCollection', features: ctx })) };

writeFileSync(out, JSON.stringify({ world, korea }));
console.log('✔', out, Math.round(JSON.stringify({ world, korea }).length / 1024) + 'KB');

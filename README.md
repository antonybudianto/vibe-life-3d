# Shibuya Life

A playable third-person exploration prototype, using Blender-authored glTF assets and Three.js. One playable character (Haru), a Shibuya-inspired crossing, a garden map, and motorcycle / kei car travel.

## Run

Node 22.13 or later and pnpm are required.

```sh
pnpm install
pnpm dev
pnpm build
node scripts/verify_game.mjs
pnpm exec tsc --noEmit
```

## Controls

| Action | Desktop | Mobile |
| --- | --- | --- |
| Move | WASD / arrow keys | Left joystick |
| Run | Hold Shift or toggle Run | Toggle Run |
| Jump | Space, on foot | Jump button |
| Rotate third-person camera | Drag scene | Drag scene with right thumb |
| Zoom | Wheel or + / − | Pinch or + / − |
| Recenter | R or circular arrow | Circular arrow |
| Travel mode | 1 walk / 2 motorcycle / 3 car; or dock | Dock |
| Vehicle | W accelerates, S brakes/reverses, A/D steer | Joystick |
| Pause | Escape / pause button | Pause button |
| Change map | Location selector | Location selector |

Settings provide day, evening, night, and live Tokyo time. Live mode uses the current device date converted to Asia/Tokyo; dawn is 05:00–07:00, dusk is 16:00–20:00. This is a clock-driven artistic cycle, not astronomical solar positioning or live weather.

The following camera now dollies from **4.2 to 60 meters**, using proportional wheel/pinch/button increments. Beyond street distance it gradually rises to reveal the neighborhood, with manual orbit, third-person follow, and building/canopy collision still active. Obstacles can shorten the actual camera distance to keep the character visible.

## Crossing concept pass

The fourth art pass opens both traffic lanes through the full map: the DHC/DAM tower now stands beside the northern street, with a distant cross street beyond the playable boundary. Four broader zebra crossings and a diagonal scramble reach chamfered curb corners. Pedestrian gates, signal posts and vehicle stop lines follow the new crossing positions. The road adds large-scale damp patches, worn lane surfaces, drains, manhole covers and repairs; rectangular paving, tactile pads and planted seating break up the foreground plazas.

TSUTAYA has a continuous bowed curtain wall, darker upper glass, furnished lower floors and a curved billboard. Its separate side campaign panel, the full-height cylindrical 109, stacked UNIQLO mark, curved anime screen, restored DAM portrait and Starbucks bar seating distinguish the landmarks. Other buildings vary in width, height, cladding and rooftop services. All changes remain Blender-authored geometry and materials, with the same models used in the game and review renders.

The crossing now has a rounded glazed Tsutaya façade, varied concrete cladding, a cylindrical 109 crown, reference-derived billboards, Japanese signs, modeled café furniture and shelves, rooftop ventilation and railings, individual leaf canopies, bus shelter, vending machines and the station stair entrance. These are real Blender meshes visible from every camera angle.

The scene includes 74 pedestrians with animated limb instances, four moving taxis and a city bus. Pedestrians start across all four districts and independently walk between sidewalk destinations at varied speeds. A shared navigation graph avoids buildings, planters, benches and Hachikō; walkers steer around each other and the player, turn smoothly, and animate footsteps from actual distance travelled. Sixteen walkers occasionally cross between districts; only those waiting at a curb obey the crossing timer, and traffic waits for the last walker to finish. Sidewalk journeys continue through every traffic phase. `scripts/crowd_metadata.py` updates their personalities without rebuilding Blender meshes. Traffic follows left-hand lanes, accelerates, queues, and stops for the player. Collision volumes move with each vehicle. Vehicles recycle beyond the map edge; this is a compact street simulation, not citywide navigation. Haru remains the sole playable character.

Hachikō Square sits southwest of the crossing at (-20, 20), marked in gold on the minimap. Its Blender-authored bronze Akita stands on a granite pedestal inside a planted octagonal border, with benches, trees, dedication plaques and lanterns. The separate Draco asset loads only with the crossing and uses Cycles vertex shading. Blue skies and drifting cumulus clouds use a single 28 KB transparent panorama rendered from Blender cloud meshes. The same cloud bake and sky palette work in Blender; day, evening and night blend continuously in Live mode.

Rebuild the current crossing with Blender 5.2 and the supplied reference image available at the path in `build_crossing_concept.py`:

```sh
blender --background --factory-startup --python-exit-code 1 --python scripts/build_city_life.py
blender --background --factory-startup --python-exit-code 1 --python scripts/build_cloud_sky.py
blender --background --factory-startup --python-exit-code 1 --python scripts/build_hachiko.py
blender --background --factory-startup --python-exit-code 1 --python scripts/build_crossing_concept.py
blender --background --factory-startup --python-exit-code 1 --python scripts/bake_crossing_concept.py
node scripts/crowd_snapshot.mjs
blender --background --factory-startup --python-exit-code 1 --python scripts/render_concept_review.py
blender --background --factory-startup --python-exit-code 1 --python scripts/compact_blender_sources.py
```

`assets/blender/crossing.blend` is the editable environment, with `hachiko.blend` and `cloud-sky.blend` as separate editable assets. The locally generated `crossing-review.blend` assembles the landmark, crowd, traffic and Haru with the starting gameplay camera and Cycles lighting; this duplicate review assembly is excluded from source uploads and can be regenerated with `render_concept_review.py`. The review images use a fixed street-life pose at time zero. Reference billboard images and generated surface textures are packed into the delivered Blender scenes and GLBs.

Detailed architecture and foliage use Cycles AO baked into vertex colors, which avoids atlas holes on small leaves and rails. Central and district street materials share a 4096px planar AO and shop irradiance atlas, plus common world-aligned asphalt weathering. A 512px repeating albedo, normal and roughness set supplies subtle pavement/asphalt grain. Sunlight stays dynamic. The map GLB is approximately 7 MB; the pedestrian model is 61 KB and is downloaded only once for all 74 instances. Crowd and traffic load only for the crossing and their shared GPU resources are disposed on map changes.

Revision 5 adds continuous rear/side terrain, Taiseido Bookstore, MAGNET by SHIBUYA109, Mark City's East and West towers, and a covered station-side pedestrian deck. New architecture uses official exterior/location references documented in [the landmark notes](assets/references/shibuya-landmarks.md). Building dimensions and distances are compressed for the existing concept composition. Revision 6 opens the expanded ground-level roads and sidewalks to all travel modes, extends the minimap, and continues the core road markings and paving details. The elevated deck remains scenery. `public/renders/crossing-district.png` shows the expanded district. Zebra paint has physical clearance and a semantic material flag for depth bias in the browser; MAGNET's ceramic wing and glazed tower meet without overlapping facade planes.

## Character and garden baking

The character and both maps include real Cycles ambient-occlusion atlases and baked procedural surface color. Each map also has a separate Cycles diffuse irradiance bake of shop lights and emissive signs. Sunlight is excluded from that light bake, so changing the time still changes direct lighting and shadows. The warm irradiance follows the same emission multiplier as the shops. Moving characters retain dynamic shadows; their short-range AO records local clothing and body detail rather than a fixed street shadow.

```sh
blender --background --factory-startup --python-exit-code 1 --python scripts/bake_assets.py -- character park
blender --background --factory-startup --python-exit-code 1 --python scripts/bake_surfaces.py -- character park
blender --background --factory-startup --python-exit-code 1 --python scripts/verify_bake_coverage.py
# If coverage flags fine props, bake those into mesh color attributes:
blender --background --factory-startup --python-exit-code 1 --python scripts/bake_fine_props.py
blender --background --factory-startup --python-exit-code 1 --python scripts/finalize_bakes.py
blender --background --factory-startup --python-exit-code 1 --python scripts/verify_bake_coverage.py
blender --background --factory-startup --python-exit-code 1 --python scripts/render_baked_review.py
```

Run these after rebuilding or changing mesh geometry. `bake_assets.py` gives each asset a non-overlapping `BakeUV` atlas while preserving original billboard UVs. AO is exported through standard glTF occlusion textures. Light maps use material extras `bakedLightmap` and `bakedLightmapScale` and UV1. The runtime waits for the selected map's light atlas, shares it among materials, and disposes it on scene changes. Cycles uses OptiX when available, with CPU fallback. The script needs a Blender build with its bundled glTF exporter.

The 1024px character and 2048px map texture masters live in `assets/bakes/` and are packed into the editable `.blend` files. Browser assets use embedded WebP textures with Draco geometry; only the two small WebP irradiance files are separate downloads, one per selected map. Surface color and local AO work in Balanced as well as High graphics. High additionally enables bloom. `public/renders/crossing-evening-cycles.png` and `crossing-night-cycles.png` are Cycles comparisons using the same starting camera and avatar position as the web game (1280 × 800).

Thin props that fall below atlas resolution use Cycles-baked color attributes instead. Their local AO is limited to a subtle 30% tint, keeping road markings readable and foliage free of black texture holes. A white occlusion carrier preserves UV1 for their independent light maps. The character is merged by material within each animation pivot, reducing draw calls without merging moving limbs together. The coverage check tests actual face-center pixels and baked vertex samples, in addition to the GLB structure tests.

Baking improves material depth and diffuse light spill. Cycles and Three.js still differ in reflections, shadow softness and light transport. The current light maps store scaled LDR irradiance, so the brightest local highlights are bounded. The scene is a stylized reconstruction and still falls short of the reference's fine material, vehicle and character finish.

## Blender assets

Editable scenes live in `assets/blender/`. Rebuild with:

```sh
blender --background --factory-startup --python-exit-code 1 --python scripts/build_assets.py -- character
# Use the concept pipeline above for the crossing.
```

The environment billboard textures are derived inside Blender from the supplied concept image. Rebuilding the crossing requires that reference at the path in `build_crossing_concept.py`; update it if moving computers. The textures are packed in the .blend files and GLBs, so playing the game and opening the scenes do not require the original image. All world, character, vehicle and prop meshes originate in Blender. No remote 3D assets or external asset CDN is required.

Blender sources include lighting and cameras. The web renderer imports the same geometry and PBR materials and uses AgX tone mapping. Blender Cycles and real-time Three.js lighting/reflections differ; this remains a stylized interpretation, **not a pixel-exact reproduction of the concept or of the Cycles render**. The characters use transform pivots for procedural gait rather than production skeletal rigs. Café interiors are visual scenery, and the station staircase is protected by a collision volume; these spaces are not playable interiors yet.

## Scene loading and extension

`lib/game/world.ts` owns rendering, fixed-step motion, third-person camera collision, inputs and resource lifetime. `lib/game/ambience.ts` manages instanced pedestrians and staged traffic. `lib/game/physics.ts` contains collision and Tokyo clock logic. `app/game.tsx` owns the HUD.

Each map is a pair: `public/models/<id>.glb` and `<id>.json`. The JSON declares a spawn, X/Z bounds, and rectangular collision volumes. Static meshes are merged by material in Blender to reduce draw calls and exported with Draco compression. The browser decoder is bundled locally in `public/draco` (from Three.js). Character loads first; only the selected map loads. Vehicles load on first use and are reused. A new map loads before the old map's GPU resources are disposed; serial tokens reject stale map requests. HTTP caching handles repeat downloads. No second map is prefetched on mobile.

To add a map, author/export it in Blender, add its metadata, extend `MapId`, and add an option in the location selector. Keep spawn points free of collision. Repeated props are merged by shared material rather than thousands of scene nodes. Balanced graphics caps device pixel ratio at 1.35 and skips bloom; High caps at 2 and enables bloom. A fine-pointer desktop starts in High; touch devices start in Balanced. Settings can override either. Animation pauses while the tab is hidden. Rendering quality and FPS are device-dependent.

## Verification

The verification script tests blocking, wall sliding, vehicle clearance, bounds, timezone transitions, GLB validity, preserved animation pivots, and map spawn safety. `blender --background --factory-startup --python-exit-code 1 --python scripts/verify_district_geometry.py` also checks terrain coverage beneath building corners, paint separation relative to Draco precision, shared district bake and weathering coordinates, and MAGNET facade separation. Browser checks cover the HUD, travel modes, lighting and responsive layout. A physical mobile-device performance test is still required before production release.

Lighting colors, exposure, emission scale and primary light values are shared through `lib/game/lighting.json`. `scripts/blender_lighting.py` applies a named preset to an open Blender scene. Ambient illumination is calibrated separately for Cycles; differences in shadows and reflections still prevent pixel-identical output. `scripts/render_previews.py` applies the shared evening preset and renders review images.

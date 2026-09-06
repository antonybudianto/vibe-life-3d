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

## Blender assets

Editable scenes live in `assets/blender/`. Rebuild with:

```sh
blender --background --factory-startup --python scripts/build_assets.py
# Or rebuild only a specific asset:
blender --background --factory-startup --python scripts/build_assets.py -- character
```

The environment billboard textures are derived inside Blender from the supplied concept image. Rebuilding the crossing requires that reference at the path in `concept_texture`; update that path if moving computers. The textures are packed in the .blend files and GLBs, so playing the game and opening the scenes do not require the original image. All world, character, vehicle and prop meshes originate in Blender. No remote 3D assets or external asset CDN is required.

Blender sources include studio lighting and cameras. The web renderer imports the same geometry and PBR materials and uses AgX tone mapping. Blender Cycles and real-time Three.js lighting/reflections differ; this first art pass is a stylized interpretation, **not a pixel-exact reproduction of the concept or of the Cycles render**. The character has transform pivots for procedural gait and riding poses, not a full production skeletal/skin rig. This prototype includes no traffic simulation, crowds, NPC interactions, interiors or missions.

## Scene loading and extension

`lib/game/world.ts` owns rendering, fixed-step motion, third-person camera collision, inputs and resource lifetime. `lib/game/physics.ts` contains collision and Tokyo clock logic. `app/game.tsx` owns the HUD.

Each map is a pair: `public/models/<id>.glb` and `<id>.json`. The JSON declares a spawn, X/Z bounds, and rectangular collision volumes. Static meshes are merged by material in Blender to reduce draw calls and exported with Draco compression. The browser decoder is bundled locally in `public/draco` (from Three.js). Character loads first; only the selected map loads. Vehicles load on first use and are reused. A new map loads before the old map's GPU resources are disposed; serial tokens reject stale map requests. HTTP caching handles repeat downloads. No second map is prefetched on mobile.

To add a map, author/export it in Blender, add its metadata, extend `MapId`, and add an option in the location selector. Keep spawn points free of collision. Repeated props are merged by shared material rather than thousands of scene nodes. Balanced graphics caps device pixel ratio at 1.35 and skips bloom; High caps at 2 and enables bloom. Animation pauses while the tab is hidden. Rendering quality and FPS are device-dependent.

## Verification

The verification script tests blocking, wall sliding, vehicle clearance, bounds, timezone transitions, GLB validity, preserved animation pivots, and map spawn safety. Browser checks cover the HUD, travel modes, lighting and responsive layout. A physical mobile-device performance test is still required before production release.

Lighting colors, exposure, emission scale and primary light values are shared through `lib/game/lighting.json`. `scripts/blender_lighting.py` applies a named preset to an open Blender scene. Ambient illumination is calibrated separately for Cycles; differences in shadows and reflections still prevent pixel-identical output. `scripts/render_previews.py` applies the shared evening preset and renders review images.

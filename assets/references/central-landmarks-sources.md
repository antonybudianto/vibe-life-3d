# Ebisubashi, TSUTAYA and Snow Brand references

Checked 2026-09-09. Architecture revision 12 remains a compact game district;
the photographs establish the facade details, not a surveyed scale model or
a claim that every advertisement is current.

- Glico's official panel specification: 20.00 m high by 10.38 m wide:
  https://www.glico.com/jp/health/contents/glicosign/
  Revision 12 uses these dimensions instead of the former 25 x 10.2 panel.
- The building immediately west of CHINTAI, photographed February 14, 2021:
  https://yasudamai.com/fumetsunominami/
  https://yasudamai.com/wp-content/uploads/2021/03/079589c7355697a943c29ffeb941a8fa.jpeg
  The calligraphy artist's own publication shows a tiled wall, recessed windows,
  exterior AC units, a black/gold Koyo cabinet and a white vertical
  `不滅のミナミ` cabinet. `dotonbori_infill.py` models those features at the
  compressed parcel width. Lettering is newly typeset, not a copy of the photo.
  Optional inspection copy: `work/references/minami-sign-house.jpg`.
  The same photo confirms a canal-facing Kukuru octopus below CHINTAI;
  the main store's street-facing entrance does not imply that the canal-side
  octopus should be removed. Tenant and campaign dates are not current guarantees.
- Two opposite-bank infill buildings receive distinct asymmetric facade designs.
  These and the remaining procedural blocks are architectural interpretations,
  not surveyed replicas; the canal extension and bridge spacing remain compressed.

- TSUTAYA EBISUBASHI exterior, OSAKA STYLE, November 2023:
  https://osaka.style/news/37282/10-136/
  Original 900 x 1200 image: https://osaka.style/news/wp-content/uploads/2023/11/10-4.jpg
  Required local input: `dotonbori-tsutaya.jpg`. The two billboard prints and
  Starbucks logo are projectively rectified inside Blender; the tower, cafe,
  window reveals, side cladding and sign cabinets are modeled geometry.
  Image copyright: OSAKA STYLE / information provider; no open license found.
- Snow Brand / 6P cheese: existing user-supplied `dotonbori-asahi-cruise.jpg`
  (1300 x 866; photograph displays January 11, 2023 on its upper sign).
  Three separately rectified panels preserve the blue Snow Brand logo,
  yellow cheese advertisement and blue tagline. They replace the fictional
  snowflake/city artwork cropped from the concept board.
- Osaka City official Ebisubashi description and dimensions:
  https://www.city.osaka.lg.jp/kensetsu/page/0000021695.html
  26 m length; approach width 11 m; central circular portion 18 m.
- Completed bridge overhead, Osaka City Construction Bureau contribution:
  https://kandoken.jp/cms/wp-content/uploads/2021/11/34%E5%8F%B7_%E4%BC%9A%E5%A0%B1.pdf
  Physical PDF page 61 / printed page 55, middle-left completed-bridge image.
  Circle, separate outer crescent ramps, radial paving divisions, dark strip
  on each approach. The upper sketch on that page is the competition proposal.
- Empty bridge paving and inner granite parapet:
  https://commons.wikimedia.org/wiki/File:Ebisubashi_20200422.jpg
  Photograph by 切干大根, CC BY-SA 4.0. Geometry reference only; not shipped as
  a texture. Shows pale rectangular pavers, dark approach strip, rounded stone
  parapet caps and horizontal/vertical stone joints.
- Outer metal railing and fascia close-up:
  https://www.nippon.com/ja/guide-to-japan/gu900283/
  https://www.nippon.com/ja/ncommon/contents/guide-to-japan/2630055/2630055.jpg
  Geometry reference only. Slotted spatula-shaped uprights, folded silver
  fascia panels, rolled lower edge, and spaced `え び す 橋` lettering.

The existing district parcel locations and stairs remain at game scale. The
bridge outline is circular with straight approaches, and its navigation and
sightseeing positions follow the revised outline. Paving finishes receive the
same Cycles AO and shop-light atlas as other walkable surfaces.

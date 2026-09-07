# Shibuya district references

Checked 7 September 2026. These additions are hand-modeled landmarks at the
existing scene's concept scale. They reproduce the documented architectural
forms below; they are not surveyed building models or a geographically exact
street map. Heights, footprints, shop interiors and distances are estimated.
No downloaded photography is embedded in these new buildings.

| Addition | Architectural features used | Primary references |
| --- | --- | --- |
| Taiseido Bookstore, 22-1 Udagawacho | Bowed white shop sign with cobalt lettering and red inset border; blue canopy; recessed entrance and pavement magazine racks; maintenance grate, upper curved advertising board and blue vertical building-name sign | [Shop's location and exterior photo](https://taiseido.co.jp/information.html), [WWDJAPAN's photographed shop interview](https://www.wwdjapan.com/articles/1108956), [advertising agency's upper-façade photo](https://www.adokugai.com/detail/460) |
| MAGNET by SHIBUYA109, 1-23-10 Jinnan | White ceramic wing with a rounded front corner and five continuous upper ribbon windows; taller dark glass frontage; projecting rectangular billboard frame; red/cyan identity and fenced rooftop lookout | [Operator's location](https://magnetbyshibuya109.jp/info/), [Tokyu's venue exterior photograph](https://eventvenues-shibuya.jp/jp/place/commercial/magnet/), [operator's identity and renovation announcement](https://www.atpress.ne.jp/news/147636) |
| Shibuya Mark City East / Excel Hotel Tokyu | Slender blue-gray glass and pale aluminum tower, close horizontal bands, central pale strip and raised crown, above shopping podium | [Hotel's exterior photograph](https://www.tokyuhotels.co.jp/shibuya-e/index.html), [Mark City access](https://www.s-markcity.co.jp/access/) |
| Shibuya Mark City West | Taller gridded office tower paired with the East tower over the long shopping podium | [Operator's office description](https://www.s-markcity.co.jp/office/), [district map](https://www.s-markcity.co.jp/wp/wp-content/themes/s-markcity/public/images/access/by_car_map.jpg?up=20241018) |
| Station-side pedestrian deck | Covered second-level path with slender supports, safety rails, stairs and station wayfinding | [Tokyu's west-side deck announcement](https://www.tokyu.co.jp/company/news/pdf/20200821-1.pdf), [Tokyu's Mark City/Fukuras network overview](https://www.tokyu.co.jp/global/e-book/ebtkk/pageindices/index21.html) |

## Placement and limits

MAGNET is placed beyond the eastern side street, east of the scene's QFRONT.
Taiseido extends the western shopping frontage associated with Center-gai.
The Mark City towers and podium occupy the southwestern station district.
The deck follows that station-side district, away from the scramble; its exact
path is adapted to the compressed block layout and is scenic, not a new
walkable level. Its modeled road clearance is 5.54 m. The district's ground-level
roads and sidewalks are accessible on foot, running, by motorcycle and by car.

The original concept puts a separate Starbucks next to TSUTAYA. In reality,
the crossing's [Starbucks is inside QFRONT/SHIBUYA TSUTAYA](https://store.starbucks.co.jp/detail-2003/).
That existing concept composition has been retained. Billboard campaigns,
roof services and secondary storefronts are simplified. Taiseido's neutral
DMM board identifies the documented advertiser, not a current campaign;
MAGNET's screen likewise does not reproduce a current ad. The MAGNET emblem
and lettering are modeled approximations of the operator's red/cyan identity.

## Architecture review, revision 7

The earlier Taiseido model incorrectly suggested a regular office-window grid
above two flat shop signs. The photographed frontage is dominated by a curved
shop sign and advertising above it. The model now follows that hierarchy,
including the blue canopy, maintenance grate and vertical building-name sign.
MAGNET's previous rectangular white wing missed the rounded corner that joins
its long side façade to the glass frontage. The white shell, upper window bands
and terrace railing now follow one continuous rounded outline. The ceramic
wing and glass tower still adjoin without coplanar exterior faces.

These changes improve the photographed silhouettes and storefront details;
they do not convert the scene to surveyed geography. Exact dimensions, rear
elevations, changing tenants and advertising artwork are not verified replicas.

## Ground and paint

Continuous terrain extends to x = -120..120 and game z = -125..110, including
all rear building footprints. Playable bounds are x = -114..114 and
game z = -118..104, leaving a margin before the terrain edge. Both the central
and outer roads share world-aligned weathering images and a 4096 px AO/light
atlas, so the old boundary does not create a surface or lighting seam.
Main zebra stripes sit 25 mm above the asphalt before compression. Road-paint
materials also export a semantic `surface_role` so the browser applies decal
depth bias while continuing to depth-test against vehicles and characters.

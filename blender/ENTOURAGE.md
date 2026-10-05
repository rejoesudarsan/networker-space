# Entourage: people, cars and two-wheelers

`blender/entourage.blend` is a separate asset library with three collections:
People, Cars and Bikes. `details/entourage.py` links (not appends) its
collections into `space-house.blend` as instances.

Every asset is built from open-source models. Nothing is modelled from
scratch. The sources are in `blender/assets/`, and the library is rebuilt from
them by:

```
/snap/bin/blender -b --factory-startup --python blender/tools/build_entourage.py [-- --render]
```

`--render` also writes a line-up of the whole library to
`blender/renders/entourage-lineup.png` and a close-up of the people to
`entourage-people.png`. `tools/entourage_closeup.py` renders a few
collections side by side, for example to fit a rider on a bike:

```
/snap/bin/blender -b blender/entourage.blend --python blender/tools/entourage_closeup.py -- Bike.Scooter.Blue.Ridden Bike.Auto.Driven
```

## What the builder does to every asset

- Imports the source and joins it into one mesh. It drops the ground planes,
  backdrop spheres, lamps and cameras that came with it.
- Rigged figures are posed. A frame of their own Idle or Walk clip is baked in,
  or bones are turned for the seated and riding poses.
- Turns the asset so its front faces +X, and puts its origin on the ground at
  the centre of its footprint.
- Scales it to metres. People are 1.58 m (women) to 1.72 m (men) tall. Cars and
  bikes are set by length: SUV 4.4 m, hatchback 3.85 m, sedan 4.3 m,
  scooter 1.8 m, motorbike 2.0 m, auto 2.65 m.
- Uses flat shading and clears custom normals, so it reads faceted like the
  house.
- Replaces all source materials and textures with one small flat palette
  (`Ent #RRGGBB` Principled materials).
  - **Vehicles:** source materials are mapped to roles: body, trim, glass,
    tyre, lights.
  - **People:** faces get roles by height band and position: shoes, bottoms,
    top (down to the knee for a kurta), sleeves or forearms, hands, face and
    hair. Real hair and skin materials are kept where the source has them.
    This lets the same figure wear a shirt and trousers, a kurta-pyjama, or a
    kurta over churidar.
- Variants share one mesh and differ only in object-level materials. Examples
  are a white SUV and a silver one, or a man in a shirt and the same man in a
  kurta.

## Library contents

- **Cars:** Car.SUV.White, Car.SUV.Silver, Car.Hatch.White, Car.Hatch.Silver,
  Car.Hatch.Red, Car.Sedan.Grey.
- **Bikes:**
  - Bike.Scooter.Grey, Bike.Scooter.Blue and Bike.Scooter.White: an
    Activa-style step-through scooter.
  - Bike.Vespa.Mint.
  - Bike.Motorbike.Black and Bike.Motorbike.Red.
  - Bike.Auto: a yellow and green auto-rickshaw.
  - Ridden versions with a rider instanced on them: Bike.Scooter.Blue.Ridden,
    Bike.Scooter.Grey.Ridden, Bike.Motorbike.Black.Ridden, and
    Bike.Auto.Driven, whose driver wears khaki.
- **People:**
  - **Standing:** Person.ManIdle.Tee, Person.ManIdle.Shirt and
    Person.WomanIdle.Churidar.
  - **Walking:** Person.ManWalk.Shirt, Person.ManWalk.Kurta,
    Person.WomanWalk.Kurta, Person.WomanWalk.Green, Person.ManPhone,
    Person.ManPhone.Blue and Person.WomanBags.Kurta.
  - **Seated:** Person.ManSit and Person.WomanSit.
  - **Riders:** Person.ManRide, Person.WomanRide and Person.ManRide.Khaki.

## Sources and licences

All sources are CC0 or CC-BY 4.0. None are non-commercial or no-derivatives.
Credit the CC-BY authors wherever renders of the model are published.

| Asset | Source | Author | Licence | File in `blender/assets/` | Changes |
|---|---|---|---|---|---|
| SUV, hatchback, sedan | [Realistic Car Pack (Nov 2018)](https://quaternius.itch.io/lowpoly-cars) | [Quaternius](https://quaternius.com) | CC0 1.0 | `quaternius-cars/SUV.obj`, `NormalCar2.obj` (hatch), `NormalCar1.obj` (sedan) | Rescaled to real lengths, recoloured: white, silver, red, grey. |
| Scooter (Activa-style) | [Gulli Bulli Scooter \| Vespa Low poly](https://sketchfab.com/3d-models/gulli-bulli-scooter-vespa-low-poly-cebde8a7dd0a4f82bba900c8dcd3f7fe) | [noorulhasanhazaribagh4](https://sketchfab.com/noorulhasanhazaribagh4) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/scooter-gulli-bulli_noorulhasan.glb` | Scaled to 1.8 m, recoloured grey, blue or white. Used for riders. |
| Vespa | [Summer Scooter](https://sketchfab.com/3d-models/summer-scooter-19a62f2cd913458d96fd0d61c92abc2b) | [steryo](https://sketchfab.com/steryo) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/scooter-summer_steryo.glb` | Scaled to 1.75 m, recoloured mint. |
| Motorbike | [Low poly motorcycle](https://sketchfab.com/3d-models/low-poly-motorcycle-4fc3500e04b14e73b942d85bc948c5e9) | [matisosanimation](https://sketchfab.com/matisosanimation) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/motorcycle_matisosanimation.glb` | Scaled to 2.0 m, recoloured black or red. |
| Auto-rickshaw | [Auto Rikshaw](https://sketchfab.com/3d-models/auto-rikshaw-bb66fedb7b4a4abfa81033342febf6a8) | [rgbguy (sagarkalbande)](https://sketchfab.com/sagarkalbande) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/auto-rikshaw_sagarkalbande.glb` | Dropped its 70 m ground plane and lamps, scaled to 2.65 m, recoloured green body and yellow canopy. |
| Man on the phone, with a bag | [Low Poly Man Taking Phone While Walking](https://sketchfab.com/3d-models/low-poly-man-taking-phone-while-walking-16522107ad84410dad419e2e3977e721) | [ROH3D](https://sketchfab.com/roh3d) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/man-phone-walking_roh3d.glb` | Scaled to 1.72 m, two recolours. |
| Woman with shopping bags | [Low Poly Business Girl 002](https://sketchfab.com/3d-models/low-poly-business-girl-002-0e277299ac254496b35d7ee4d6385983) | [ROH3D](https://sketchfab.com/roh3d) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/business-girl_roh3d.glb` | Re-centred (it sat 20 m off origin), scaled to 1.6 m. Texture replaced by height bands: kurta over leggings. |
| Man (standing, walking, seated, riding) | [Low-poly Man](https://sketchfab.com/3d-models/low-poly-man-7b93db2d46d847f191cf5e841b322856) | [Razvan Savescu](https://sketchfab.com/razvansavescu) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/man_razvansavescu.glb` | Idle and Walk frames baked in. Seated and riding poses made by turning its bones. Texture replaced by height bands: shirt, tee, kurta, khaki. |
| Woman (standing, seated, riding) | [Low-poly Woman](https://sketchfab.com/3d-models/low-poly-woman-752778128b9a4b578586dbce40c0366f) | [Razvan Savescu](https://sketchfab.com/razvansavescu) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/woman_razvansavescu.glb` | Idle frame baked in, plus seated and riding poses. Shorts and blouse repainted as a kurta over churidar. |
| Woman walking | [Low-poly Girl](https://sketchfab.com/3d-models/low-poly-girl-3e79fef9da5f4db7b6a46f3e0ff89328) | [Razvan Savescu](https://sketchfab.com/razvansavescu) | [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) | `sketchfab/girl_razvansavescu.glb` | Walk frame baked in, scaled to 1.58 m, repainted as a kurta over churidar in two colourways. |

`assets/sketchfab/SOURCES.json` keeps the Sketchfab metadata for each file:
uid, title, author, licence and face count. The Quaternius licence file is
`assets/quaternius-cars/License.txt`.

### How the files were fetched

Poly Pizza and Sketchfab downloads need API keys, which this host doesn't
have. Quaternius' Google Drive links hit a download quota, so his
*Background Posed Humans* pack, the first choice for people, could not be
fetched. The Sketchfab models were found through Sketchfab's public search
API. They were then downloaded from the [Objaverse](https://huggingface.co/datasets/allenai/objaverse)
mirror on Hugging Face, which stores the original GLB with its Sketchfab
licence. Only models whose Sketchfab licence is CC-BY or CC0 were used.

### Tried and dropped

- [low poly people](https://sketchfab.com/3d-models/54ba3955682b42d98be1eea271456ec2)
  by Doug E. (CC-BY): four faceted figures that would suit the house. They
  were dropped because their crossed arms and hands-to-face poses came out
  blotchy under the height-band recolouring.
- The Kenney car and character kits (CC0): too toy-like, with big heads and
  big wheels, beside the house.

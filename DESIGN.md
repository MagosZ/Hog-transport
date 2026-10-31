# Hog Shuttle: design

A small, boxy spacer shuttle, inspired by the Warhammer 40,000 Arvus lighter. It flies in space, has a
sealed and heated cabin, and hovers on the local map like a VTOL aircraft. Mostly XML, plus a small DLL for
the cabin.

## 1. Dependencies

| Mod | packageId | Why |
|---|---|---|
| Harmony | `brrainz.harmony` | Needed by the others |
| Vehicle Framework | `SmashPhil.VehicleFramework` | The vehicle itself, world-map flight, space flight |
| VTOL Vehicle | `rabiosus.vtolvehicle` | Hovering on the local map (closed source) |
| Vanilla Vehicles Expanded | `OskarPotocki.VanillaVehiclesExpanded` | Research tab and prerequisite, engine sounds |
| Odyssey (optional) | `Ludeon.RimWorld.Odyssey` | Space destinations, the `Shuttles` prerequisite |

## 2. The shuttle (`HogShuttle`, `Defs/VehicleDefs/HogShuttle.xml`)

- Footprint 4×7 (`size (4,7)`, was 4×8 until row 2 was cut); the body is a box once its wings are out. Facing
  east or west it takes 7×4.
- Roles: pilot ×1 (Movement, needed to fly, Intellectual 6+ unless the flight computer is fitted; see Pilot
  skill; also fires the roof autocannon if fitted), co-pilot ×1 (no handling, optional), passenger ×8.
- Cargo 1000 kg, mass 1800, flight speed 30.
- Components: 16 parts, generated from one table by `Source/Art/components.py` (cells written as grid names).
  The script writes the components, the armour upgrade's entries and the CE patch, so edit the table and re-run
  it. The parts follow VVE's helicopters (Mosquito, Louie, Cherokee), turned into spacecraft parts, with health at
  the Louie's × 1.5 (28 cells to its 21). Their positions follow the Arvus lighter (Warhammer Community pictures):
  cockpit box at the front centre, wings along the sides with the two ducted turbofans on them, three skids (one
  under the nose, two at the rear sides), cargo bay with a rear door. A part may cover several cells, and a cell may hold several parts. Cells: a 4×7 footprint
  facing north spans x −1..2, z −3..3 (north = z 3).

  **Grid names** (used when talking about part positions): columns **A–D** run port to starboard (x −1, 0, 1,
  2), rows **1–7** run nose to tail (z 3 down to −3), with the Hog facing north. So B3 = (0, 1). The hull
  covers every cell except the four corners A1, D1, A7 and D7, which are empty, physically and in the art: the
  nose and the tail are two columns wide.

  | Row | A (port) | B | C | D (starboard) |
  |---|---|---|---|---|
  | 1 nose | *(empty)* | cockpit, avionics | cockpit, avionics | *(empty)* |
  | 2 | wing | cabin seats, front skid | cabin seats, front skid | wing |
  | 3 | turbofan, wing | fuel tank | fuel tank | turbofan, wing |
  | 4 | turbofan, wing, rear skid | fuel tank | fuel tank | turbofan, wing, rear skid |
  | 5 | turbofan, wing, rear skid | fuel pumps, control servos | fuel pumps, control servos | turbofan, wing, rear skid |
  | 6 | wing | fuel intake | fuel intake | wing |
  | 7 tail | *(empty)* | rear door | rear door | *(empty)* |

  In game, Vehicle Framework's dev-mode setting "Draw hitbox" (mod settings, Debug) shows the real cells.

  | Part (key) | Health | Depth | Affects | Cells | VVE counterpart |
  |---|---|---|---|---|---|
  | Hull | 900 (hit weight 3) | outer | – | all but the corners A1, D1, A7, D7 | side panels |
  | Cockpit | 200 | outer | – | B1–C1 | – |
  | Port / starboard turbofan (`ThrusterPort`, `ThrusterStarboard`) | 220 each | outer, the engines: flight stats can't exceed their state; don't explode | flight speed, control | A3–A5 / D3–D5 | engine, rotor mast |
  | Port / starboard wing | 300 each | outer, hull armour | flight control | A2–A6 / D2–D6 | stabilizers, rudder |
  | Front skid (`SkidFront`) | 120 | outer | flight speed | B2–C2 | landing skids |
  | Port / starboard rear skid (`SkidPort`, `SkidStarboard`) | 120 each | outer | flight speed | A4–A5 / D4–D5 | landing skids |
  | Rear door | 150 | outer | – | B7–C7 | – |
  | Fuel intake | 75 | outer | flight speed | B6–C6 | fuel intake |
  | Fuel pumps | 75 | inner | flight speed | B5–C5 | transmission |
  | Fuel tank | 180 | inner, leaks, may explode | – | **B3–C4** (centre) | chemtank |
  | Avionics | 75 (hit weight 2) | inner | – | B1–C1 | dashboard |
  | Cabin seats | 75 (hit weight 2) | inner | – | B2–C2 | upholstery |
  | Control servos | 105 (hit weight 2) | inner | – | B5–C5 | servos |

  Armour classes: hull and wings 0.50 / 0.90, cockpit 0.45 / 0.80, other outer parts 0.45 / 0.80, inner parts
  0.25 / 0.40. VVE puts armour on the vehicle, not the parts, so these follow the Hog's first parts.
- Fuel: chemfuel, 1200 capacity, used only while flying. Enough to cross the planet twice in the air, or to
  reach orbit and work there for a while (see Range and Orbit costs).
- No weapons built in. The door gun and autocannon upgrades add `VTOLVehicle.VtolVehicleTurret`s, as the Hind does.

### Flight

- **Local map (VTOL):** `thingClass VTOLVehicle.VtolVehiclePawn` with `VTOLVehicle.AircraftProperties`,
  `CompProperties_VtolAirborneMoveBlocker` and `VtolCrewTransferProperties`. Field names come from the Hind
  Helicopter Gunship, the only open example (`Model mods/_Mod_Source_Reference/Mi24HindHelicopter`).
  VTOL Vehicle is built for helicopters; the Hog has one invisible, non-spinning "rotor"
  (`HogShuttle/Transparent`) so it stays on the path the Hind uses. Its rotor sound is VVE's rocket engine.
  Fuel on the local map is all VTOL Vehicle's: `fuelConsumptionPerTick` 0.006 the whole time it's airborne,
  hovering included (15 chemfuel per in-game hour; a full tank hovers about 80 hours). Vehicle Framework burns
  nothing on the map, since its condition is `Flying`, which it applies only on the world map. Kept on purpose
  (user): VTOL craft burn fuel to hover. A half-rate hover discount was considered and turned down.
- **World map:** Vehicle Framework's `CompProperties_VehicleLauncher`, 1-tick launch and landing like the
  Hind (VTOL Vehicle animates take-off and landing on the map).
- **Range:** Vehicle Framework charges the whole trip's fuel at launch:
  fuel per tile = `fuelConsumptionRate` × launcher `fuelConsumptionWorldMultiplier` / (60 × `FlightSpeed`).
  The distance is the great-circle angle in tiles (SmashTools `Ext_Math.SphericalDistance`), so a target in
  orbit would cost about as much as the surface point under it (see Orbit costs). Hog: 300 × 10 / (60 × 30)
  = 1.67 per tile, 720 tiles in the air on 1200 fuel. The rate is set with the speed so a faster Hog doesn't
  also get cheaper per tile. Half the planet's circumference is about 330 tiles (100% coverage; estimate).

  | Aircraft (full tank) | Flight speed | Fuel | Fuel per tile | Range |
  |---|---|---|---|---|
  | VVE Mosquito (helicopter) | 10.5 | 120 | 0.39 | 309 tiles |
  | VVE Louie (helicopter) | 9.95 | 360 | 0.81 | 443 tiles |
  | VVE Cherokee (helicopter) | 4.5 | 420 | 2.76 | 152 tiles |
  | VVE Smuggler (plane) | 22 | 120 | 0.85 | 141 tiles |
  | Odyssey passenger shuttle | – | 400 | 3 | 133 tiles |
  | **Hog shuttle**, in the air | 30 | 1200 | 1.67 | **720 tiles** |
  | **Hog shuttle**, legs ending in space | 30 | 1200 | 16.7 | 72 tiles, less 50 per surface/space change |
- **Orbit costs** (`OrbitTransit.cs`, `OrbitTransitExtension` on the Hog: `transitFuel` 50,
  `spaceDistanceFactor` 10). Vanilla gravships (which VGE only adjusts, through
  `GravshipUtility.TryGetPathFuelCost`) pay a layer-change cost and price distance on the destination layer
  × its `rangeDistanceFactor` (orbit 20). The Hog does the same with fixed numbers:
  - a leg ending on a space layer costs 10× the distance cost. Vanilla's orbit factor is 20, but VF already
    measures in surface tiles and orbit tiles may be larger, so 20 was judged too much (user);
  - each leg that changes layer (surface ↔ orbit) costs 50 more. Surface → orbit straight overhead costs 50,
    and a round trip costs 100.
  - Estimates: postfix on `CompVehicleLauncher.FuelNeededToLaunchAtDist(Vector3, PlanetTile)` (launch checks)
    and on `FuelTargetUpdater.TargeterUpdate`, which re-prices the drawn path leg by leg. Vehicle Framework
    prices it by total distance.
  - Spending: postfix on `AerialVehicleInFlight.SpendFuel` burns the extra 9× while the current leg ends in
    space. Running dry there crashes the shuttle the normal Vehicle Framework way. A postfix on
    `InitializeNextFlight` takes the 50 when a leg changing layer starts. The layer a paid leg heads to counts
    as current, so re-routing mid-leg doesn't pay twice, and resuming a flight after loading is never charged.
    Re-routing in flight after a load may charge once more, a known edge case.
- **Space:** `spaceFlight true`. With Odyssey, Vehicle Framework (1.6.2064 and later) lets the vehicle target
  the world objects it marks as space objects: Gravship, SpaceBase, SpaceSite, GeneratedAsteroid.

### Sealed cabin (`Source/`, `HogShuttle.dll`)

Vehicle Framework keeps ticking what's aboard: the seats (`VehiclePawn.TickHandlers`) and the cargo hold
(`inventory.innerContainer.DoTick()`), both every tick. So passengers live normally aboard, and they and the
cargo feel the outside temperature. In space (orbit: full vacuum, −75 °C) the first test passengers died of
hypothermia. Vanilla shuttles don't have the problem because, as far as can be seen, their transporters don't
tick their contents (stasis). The Hog keeps Vehicle Framework's way and seals the cabin instead:

- `HogShuttle.SealedCabinExtension` on the VehicleDef (`temperature`, 21) turns it on; other vehicles are untouched.
- **Temperature:** a Harmony postfix on `Thing.AmbientTemperature` (and on Pawn's own getter if it has one).
  For anything not spawned whose holder chain reaches a VehiclePawn with the extension, it returns the cabin
  temperature. That covers seats, the cargo hold, and passengers' own gear, on the map, on the world map and
  in orbit.
- **Vacuum (Odyssey):** vacuum belongs to the cell, so it can't be cleared for the cabin alone.
  `StatPart_SealedCabinVacuum` on Odyssey's `VacuumResistance` sets pawns aboard to 100%. Vacuum exposure
  and vacuum burns scale with 1 − resistance. Odyssey's patch, `Mods/Odyssey/Patches/HogShuttle_Vacuum.xml`,
  adds the part to the stat's existing parts list or creates one, so it coexists with VGE's oxygen-pack part.
- Side effect: passengers keep their needs, and food in the hold rots as in a 21 °C room.
- Known Vehicle Framework bug: a passenger who dies aboard throws "Collection was modified" in
  `TickHandlers`. The sealed cabin prevents the deaths that triggered it.

### Pilot skill

- The pilot seat (`Pilot` role) only counts a pawn with **Intellectual 6** or more (`PilotSkillExtension` on the
  Hog: `role`, `skill`, `minLevel`, `waivedByUpgradeNode`). A postfix on Vehicle Framework's per-seat check,
  `VehicleRoleHandler.CanOperateRole(Pawn)`, refuses anyone below that. A pawn with the skill disabled, or no
  skills at all, is refused too.
- That check decides whether the seat is crewed (`RoleFulfilled` → `HasEnoughOperators`), so an under-skilled
  pilot leaves the Hog unable to move or fly. It also decides seat picking, so boarding pawns aren't given the
  pilot seat. The co-pilot and passenger seats have no requirement.
- The auxiliary flight computer upgrade waives it.
- Untested: VTOL Vehicle's own "board nearby" might still seat an under-skilled pawn as pilot (the Hind needed
  extra code for a similar case). The Hog then stays grounded, which is safe; move the pawn by hand.

### Upgrades (`Defs/HogShuttle_UpgradeTree.xml`)

Upgrade nodes have no Vehicle Framework effect of their own; HogShuttle.dll checks whether they're installed.
Vehicle Framework's removal defaults apply: 50% refund, 30% of the work. Upgrade work is spent at construction
speed per tick, like building.

- `HogShuttle_FlightComputer`: "Auxiliary flight computer", *"Lets anyone who can fly a vehicle pilot the
  shuttle, whatever their Intellectual skill."* 1 advanced component, work 200. Waives the pilot skill check.
- `HogShuttle_PlasteelArmour`: "Plasteel armour", *"Plasteel plates over the whole airframe: about 20% more
  armour on every part, at the cost of 200 kg of cargo space."* 150 plasteel + 4 components, work 6000 (the
  Hind Gunship's Plasteel Armour price and work). Unlike the Hind's, it plates the cockpit too. Vehicle
  Framework effects only (no DLL): `VehicleUpgrade` armour, Add, 20% of each component's rating; `StatUpgrade`
  CargoCapacity −200 (1000 → 800).
- `HogShuttle_CargoOutfit`: "Cargo outfit", *"Swaps six of the passenger seats for tie-down points: 2
  passenger seats, 1000 kg more cargo space."* No cost, work 500. `VehicleUpgrade` role edit
  (`editKey` Passenger, slots 2), like the Hind's Cabin Modification; `StatUpgrade` CargoCapacity +1000. Stacks
  with the plasteel armour (1000 − 200 + 1000 = 1800 kg). Vehicle Framework doesn't unload pawns when a role edit
  lowers the slots (`VehicleRole.AddUpgrade` only records it), so unload passengers before fitting it.
- **Rear door gun** (only one can be fitted): `HogShuttle_DoorGunMMG` / `HogShuttle_DoorGunHMG` /
  `HogShuttle_DoorGunMinigun`. These are the Louie's three door-gun options in "VVE - Secondary Weapons"
  (`tgbm.vve.secondary.weapons`, workshop 3459650108, **a dependency**), using its turret defs as they are, with one
  gun instead of two, so half its price and work:

  | Option | Turret def | Range | Fire | Box | Cost | CE |
  |---|---|---|---|---|---|---|
  | Medium machine gun | `TGBM_WisentMMG` | 28.9 | 6 per burst | 75 (steel) | 150 steel, 5 components | 7.62×51 NATO, range 62, 100 |
  | Heavy machine gun | `TGBM_WisentHMG` | 32.9 | 6 per burst, slower | 75 (steel) | 205 steel, 6 components | .50 BMG, range 75, 100 |
  | Minigun | `TGBM_ExposedMinigun` | 30.9 | 25 per burst | 200 (steel) | 135 steel, 11 components | 7.62×51 NATO, range 62, 2000 |

  All take 5000 work. Fitting one adds a **door gunner** role (1 seat, Turret, needed to fire, at B7–C7,
  exposed because the door is open). The role comes first, then a `VTOLVehicle.VtolVehicleTurret`, so the gun
  follows the aircraft's heading as the Hind's do. It is mounted at the tail centre (north offset (0, −3.1)),
  defaultAngleRotated 180, angleRestricted (120, 240): 60° either side of straight back (0 = the nose). The
  stats, art, shot sounds, the Upgrades-tab turret icon and the Combat Extended values (that mod's own CE patch)
  all come from VVE - Secondary Weapons, so they follow its updates. The Hog has an empty `CompProperties_VehicleTurrets` for
  the upgrade to fill, and every upgrade node has an `<upgrades>` list, even an empty one, because Vehicle
  Framework's turret code reads it without a null check.
- `HogShuttle_TwinAutocannon`: "Twin-linked autocannon". 200 steel, 30 plasteel, 6 components, work 6000 (a step up
  from the Hind's heavy chin turret, 150 / 30 / 4 / 5000), and `StatUpgrade` CargoCapacity -50. Can be fitted with a
  door gun. Turret def in `Defs/TurretDefs/HogShuttle_TwinAutocannon.xml`.

  The weapon is vanilla's autocannon turret (`Turret_Autocannon`, `Gun_AutocannonTurret`; with CE, CE's version of it),
  doubled where two barrels change the number.

  | Stat | Without CE | Vanilla turret | With CE | CE's turret |
  |---|---|---|---|---|
  | Rounds per burst | **6** | 3 | **20** | 10 |
  | Ticks between rounds | **9** | 17 | **4** | 7 |
  | Between bursts | 210 ticks (3.5 s) | Same | 60 ticks (1 s) | Same |
  | Warm-up | None | Same | 2.3 s | Same |
  | Range | 8.9 to 32.9 | Same | 0 to 78 | Same |
  | Shell | `Bullet_AutocannonTurret`: 27 damage, speed 88 | Same | `Bullet_20x102mmNATO_AP` by default: 44 damage, 30 sharp AP, speed 182 | Same |
  | Magazine | **180** rounds | 90 shots per barrel | **200** rounds | 100 |
  | Ammo | 2 steel per round (360 to fill) | Same | 20x102mm NATO | Same |
  | Reload | 10 s | A pawn changes the barrel | 7.8 s | Same |
  | Accuracy | Spread 1 | 0.28 / 0.72 / 0.66 / 0.5 | Sway 1.61, spread 0.01 | Same |
  | Arc | Fixed forward, 6° either side | Full turret | Same | Full turret |

  Choices:
  - Each barrel keeps the original's rhythm, so the gun fires twice the rounds in about the same burst time: twice the
    damage over time. Half of 17 and of 7 aren't whole ticks, so they round up. Damage per round and range don't double.
  - Vehicle Framework has no accuracy stats, so spread 1 stands in without CE.
  - CE recoil is 0, like the Hind's: Vehicle Framework multiplies it by the shot number, and these bursts are long.

  - Twin-linked means two barrels bound together in one gun, drawn after VFE Security's double autocannon (one breech
    block, an ammo drum on each side, barrels almost touching). Two fire points, 0.17 of a cell apart, `LoopPerShot`:
    half the rounds from each barrel.
  - Mounted on the **roof behind the cockpit** (B2-C2, centre line, pivot north offset (0, 1.84)), drawn on top of the
    airframe (`drawLayer` 1). The barrels run over the cockpit roof and clear the nose by 1.32 cells (art and fire points only, no hitbox). It's
    a separate turret image because it only shows once fitted, and because the muzzles reach past the body texture.
  - The **pilot** controls it. Vehicle Framework bars pawns incapable of violence from any seat with Turret handling,
    so the seat stays Movement only and no role lists the turret. `PilotGunExtension` on the Hog (`Source/PilotGun.cs`):
    a postfix on `VehicleTurret.RecacheMannedStatus` counts the gun as manned only with a crewed pilot's seat and a
    pilot capable of violence, and a postfix on `VehicleTurret.IsDisabled` greys out its button with a reason.
  - Pacifist pilots can fly but can't fire. A caution message appears when one takes the seat (keyed
    `HogShuttle_PacifistPilot`), found by comparing pilots in that same recheck, which runs on boarding, leaving and
    seat changes. The first check of a turret only records the pilot, so loading a save says nothing.
  - The pilot aims by turning the shuttle: `rotateVehicleToTargetWhileTargeting`, and the AircraftProperties' combat
    hover is on with `combatDirectionalHoverTurretKey` = `twinAutocannon`. The key names a turret that only exists
    once the upgrade is fitted; how VTOL handles that without it needs checking in game (TESTING.md).
  - The Hind's own code isn't here (no license, and not copied): bursts stop when the target dies, the nose may drift
    back to the move-order facing, a door gun's auto-target may swing the nose, and a newly fitted gun may point
    north until the pilot boards.
  - CE: `Mods/CombatExtended/Patches/HogShuttle_TwinAutocannon.xml`.
- `HogShuttle_ChemicalToilet`, only with `Dubwise.DubsBadHygiene` (added to the tree by
  `Mods/DubsBadHygiene/Patches/HogShuttle_Upgrades.xml`): "Chemical toilet", *"Keeps the bladder of everyone
  aboard satisfied."* 10 steel + 10 neutroamine, work 95 (a wooden wall: Wall 135 × wood 0.7).
- Toilet effect: `UpgradeNeedRefillExtension` on the Hog (`upgradeNode`, `need` =
  DBH's `Bladder`) and a postfix on `VehiclePawn.TickRare` (every 250 ticks, on the map and in flight) fill
  that need for everyone in `AllPawnsAboard` while the node is installed. The NeedDef is named in XML, so the
  DLL doesn't reference DBH.
- When the Hog gets turrets: give every node an empty `<upgrades />`. Vehicle Framework's turret code
  (`CompVehicleTurrets`) reads every node's upgrades list without a null check.

### Combat Extended (optional)

`Mods/CombatExtended/Patches/HogShuttle_CombatExtended.xml`, loaded only with `CETeam.CombatExtended`. Without
CE the vanilla ratings in Defs/ apply. With CE, each component's rating is the Hind Gunship's CE rating for the
matching part × (Hog vanilla / Hind vanilla). That's the same ratio rule as the VGE CE patch. Hull and wings = Hind
body, outer parts = Hind engines, inner parts = Hind fuel tank. The plasteel armour upgrade's amounts become 20%
of these. Generated by `Source/Art/components.py`.

| Armour class (parts) | Vanilla (blunt / sharp) | + upgrade | CE (blunt / sharp) | + upgrade (CE) |
|---|---|---|---|---|
| Hull, wings | 0.50 / 0.90 | +0.10 / +0.18 | 22.5 / 11.6 | +4.5 / +2.32 |
| Cockpit | 0.45 / 0.80 | +0.09 / +0.16 | 13.8 / 8.6 | +2.76 / +1.72 |
| Outer: turbofans, skids, rear door, fuel intake | 0.45 / 0.80 | +0.09 / +0.16 | 17.9 / 9.3 | +3.58 / +1.86 |
| Inner: fuel pumps, fuel tank, avionics, cabin seats, control servos | 0.25 / 0.40 | +0.05 / +0.08 | 10 / 5.3 | +2 / +1.06 |

Not covered: the Hind's CE patch also gives its airframe CE's real collision width (CE treats every vehicle as
a one-cell-wide target).

## 3. Building and research

- `HogShuttle_Blueprint`: 450 steel, 250 plasteel, 10 components and, with Odyssey, 3 advanced components
  + 2 shuttle engines; without Odyssey, 9 advanced components. Work 48000, construction 10. About 1.7×
  Odyssey's passenger shuttle. The base def has the no-Odyssey cost; `Mods/Odyssey/Patches/HogShuttle_Cost.xml`
  (loaded only with Odyssey via LoadFolders.xml) replaces the 9 advanced components with 3 + 2 shuttle engines.
- `HogShuttle_Research` in VVE's `Vehicles` tab at (3, 0): Spacer, 3000, hi-tech research bench and
  multi-analyzer. Prerequisites `VVE_AerialVehicles` and, only with Odyssey, `Shuttles`.

## 4. Art

Placeholder, from `Source/Art/body_views.py` (run `make_textures.py`): **one top-down view**, `Body.png`, at
128 px per cell, with its paint mask `Body_m.png`. VTOL Vehicle turns that one picture to the aircraft's heading
(the Hind ships one top-down view too). A three-view VVE-style set (`_north/_south/_east`) was tried and dropped,
since in game only the top-down view is used (user). Mask: red = hull and nacelles, green = cockpit armour and the
wing stripe, blue = wings. Glass, brass intake lips, exhaust rims, the grille, the fuel cap and lights are
unpainted. `CutoutComplexPattern`, default colours grey / green / grey. Square drawSize (7,7), like the Hind's.
The wings are painted one cell past their component (A2–A6 / D2–D6) on each side, an outer cell that is art
only. `Shadow` is the silhouette, `BuildIcon` the view scaled down.

Drawn as seen from straight above: only upward-facing surfaces show, with light from the north-west and shadows
cast down-right onto lower surfaces.
- **Turbofans** (A3–A5 / D3–D5): they face forward, so each is a cylinder lying lengthwise, shaded across its
  width. The intake lip shows as a thin brass band at the front, with rib bands round the housing and the exhaust
  rim at the back. The fan isn't visible. They cast shadows onto the wings.
- **Hull:** one roof from row 2 to the tail, with lit west and shaded east chamfers and a shaded tail edge. Row 7
  (B7–C7; A7 and D7 are empty) is ordinary roof; the rear door is a vertical face at the tail, so it isn't
  visible from above.
- **Cockpit** (B1–C1): an armoured roof, with the sloped windscreen foreshortened at the front.
- **Roof details**, after the kit photo: a raised sensor housing with a grille and a red dome right behind the
  cockpit (B2–C2), then the cabin hatch; the fuel tank bay's two filler plates (B3–C4); the vent grille (B5–C5);
  the refuelling cap at the front of B6 with roof vents behind it in B6 and C6; the green dorsal fin on the
  centre line (C6–C7), seen edge-on as a thin strip with its shadow; copper pipes with clamps
  along both roof edges (rows 3–5); rivets along the seams.
- **Cockpit:** riveted green armour, a three-pane windscreen, a roof escape hatch, red (port) and green
  (starboard) lamp domes at its rear corners.
- **Turbofans:** mounting straps and a copper fuel line along the top of each nacelle; soot streaks on the wings
  behind the exhausts (A6 / D6).
- **Wings:** rivet rows along the plate seams, the green band with a star emblem, a caged landing light near each
  root (A2 / D2), and navigation lights at the tips (red port, green starboard).
- **Skids:** hidden under the hull and wings.
- Domes, caps and lamps facing up show from above; lenses facing forward don't, so none are drawn.
- **Twin-linked autocannon** (`TwinAutocannon.png`, 6 cells square, `twin_autocannon()` in `body_views.py`): own drawing
  after VFE Security's double autocannon. A mounting ring on the roof, the breech block, an ammo drum on each side, and
  two ribbed barrels lying lengthwise with straps binding them together. Unpainted.

`python make_textures.py <path.png>` also writes a check image with the grid names over the view (not shipped).
Reference: the Warhammer Community and ifelix.net pictures of the Arvus lighter.

## 5. Later

- Real art.
- Check the range against an actual pole-to-pole flight and a surface-to-orbit trip.

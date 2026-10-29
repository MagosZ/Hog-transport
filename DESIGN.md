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

- Footprint 4×8 (`size (4,8)`); the body is a box once its wings are out. Facing east or west it takes 8×4.
- Roles: pilot ×1 (Movement, needed to fly), co-pilot ×1 (no handling, optional), passenger ×8.
- Cargo 1000 kg, mass 1800, flight speed 20.
- Components: hull (all cells), cockpit (front edge), port and starboard thrusters (side edges; flight speed
  and control), fuel tank (back edge, internal; leaks, may explode below 20% health).
- Fuel: chemfuel, 600 capacity, used only while flying. Sized so one tank crosses the planet (see Range).
- No weapons yet. When they come: VTOL Vehicle's `VtolVehicleTurret` in `CompProperties_VehicleTurrets`,
  as the Hind does.

### Flight

- **Local map (VTOL):** `thingClass VTOLVehicle.VtolVehiclePawn` with `VTOLVehicle.AircraftProperties`,
  `CompProperties_VtolAirborneMoveBlocker` and `VtolCrewTransferProperties`. Field names come from the Hind
  Helicopter Gunship, the only open example (`Model mods/_Mod_Source_Reference/Mi24HindHelicopter`).
  VTOL Vehicle is built for helicopters; the Hog has one invisible, non-spinning "rotor"
  (`HogShuttle/Transparent`) so it stays on the path the Hind uses. Its rotor sound is VVE's rocket engine.
- **World map:** Vehicle Framework's `CompProperties_VehicleLauncher`, 1-tick launch and landing like the
  Hind (VTOL Vehicle animates take-off and landing on the map).
- **Range:** Vehicle Framework charges the whole trip's fuel at launch:
  fuel per tile = `fuelConsumptionRate` × launcher `fuelConsumptionWorldMultiplier` / (60 × `FlightSpeed`).
  The distance is the great-circle angle in tiles (SmashTools `Ext_Math.SphericalDistance`), so a target in
  orbit costs about as much as the surface point under it. Hog: 200 × 10 / (60 × 20) = 1.67 per tile, 360
  tiles on 600 fuel. Half the planet's circumference is about 330 tiles (100% coverage; estimate), so a
  full tank flies pole to pole, and reaching orbit costs far less.

  | Aircraft (full tank) | Flight speed | Fuel | Fuel per tile | Range |
  |---|---|---|---|---|
  | VVE Mosquito (helicopter) | 10.5 | 120 | 0.39 | 309 tiles |
  | VVE Louie (helicopter) | 9.95 | 360 | 0.81 | 443 tiles |
  | VVE Cherokee (helicopter) | 4.5 | 420 | 2.76 | 152 tiles |
  | VVE Smuggler (plane) | 22 | 120 | 0.85 | 141 tiles |
  | Odyssey passenger shuttle | – | 400 | 3 | 133 tiles |
  | **Hog shuttle** | 20 | 600 | 1.67 | **360 tiles** |
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

### Upgrades (with Dubs Bad Hygiene)

Loaded only with `Dubwise.DubsBadHygiene` (`Mods/DubsBadHygiene/`, LoadFolders.xml). Without DBH the Hog has
no upgrade tree and no Upgrades tab.

- `HogShuttle_UpgradeTree`, one node `HogShuttle_ChemicalToilet`: "Chemical toilet", *"Keeps the bladder of
  everyone aboard satisfied."* 10 steel + 10 neutroamine, work 95 (a wooden wall: Wall 135 × wood 0.7;
  Vehicle Framework spends upgrade work at construction speed per tick, like building). Vehicle Framework's
  defaults for removal: 50% refund, 30% of the work.
- The node has no Vehicle Framework effect. `UpgradeNeedRefillExtension` on the Hog (`upgradeNode`, `need` =
  DBH's `Bladder`) and a postfix on `VehiclePawn.TickRare` (every 250 ticks, on the map and in flight) fill
  that need for everyone in `AllPawnsAboard` while the node is installed. The NeedDef is named in XML, so the
  DLL doesn't reference DBH.
- When the Hog gets turrets: give this node an empty `<upgrades />`. Vehicle Framework's turret code
  (`CompVehicleTurrets`) reads every node's upgrades list without a null check.

## 3. Building and research

- `HogShuttle_Blueprint`: 450 steel, 250 plasteel, 10 components and, with Odyssey, 3 advanced components
  + 2 shuttle engines; without Odyssey, 9 advanced components. Work 48000, construction 10. About 1.7×
  Odyssey's passenger shuttle. The base def has the no-Odyssey cost; `Mods/Odyssey/Patches/HogShuttle_Cost.xml`
  (loaded only with Odyssey via LoadFolders.xml) replaces the 9 advanced components with 3 + 2 shuttle engines.
- `HogShuttle_Research` in VVE's `Vehicles` tab at (3, 0): Spacer, 3000, hi-tech research bench and
  multi-analyzer. Prerequisites `VVE_AerialVehicles` and, only with Odyssey, `Shuttles`.

## 4. Art

Placeholders from `Source/Art/make_textures.py` (top-down, nose north, 64 px per cell): `Body` (8×8 cells
texture, body 4×8), `Shadow`, `BuildIcon`, `Transparent`.

## 5. Later

- Weapons.
- Real art.
- Check the range against an actual pole-to-pole flight and a surface-to-orbit trip.

# Hog Shuttle: design

A small, boxy spacer shuttle, inspired by the Warhammer 40,000 Arvus lighter. It flies in space, is
airtight, and hovers on the local map like a VTOL aircraft. XML only for now: no C#.

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
- Fuel: chemfuel, 600 capacity, used only while flying. Placeholder numbers.
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
- **Space:** `spaceFlight true`. With Odyssey, Vehicle Framework (1.6.2064 and later) lets the vehicle target
  the world objects it marks as space objects: Gravship, SpaceBase, SpaceSite, GeneratedAsteroid.

### Airtight

Nothing to add today. Pawns aboard a Vehicle Framework vehicle aren't spawned, so vacuum never reaches
them (Vehicle Framework only has a to-do, VF-301..303, to let gas, toxic and vacuum affect them). The
vehicle overrides the pawn tick, so vacuum doesn't hurt the vehicle either. If Vehicle Framework adds vacuum
for passengers later, this mod needs a small patch to keep the Hog sealed.

## 3. Building and research

- `HogShuttle_Blueprint`: 450 steel, 250 plasteel, 10 components, 3 advanced components; work 48000,
  construction 10. About 1.7× Odyssey's passenger shuttle, with advanced components instead of its shuttle
  engine so it builds without Odyssey.
- `HogShuttle_Research` in VVE's `Vehicles` tab at (3, 0): Spacer, 3000, hi-tech research bench and
  multi-analyzer. Prerequisites `VVE_AerialVehicles` and, only with Odyssey, `Shuttles`.

## 4. Art

Placeholders from `Source/Art/make_textures.py` (top-down, nose north, 64 px per cell): `Body` (8×8 cells
texture, body 4×8), `Shadow`, `BuildIcon`, `Transparent`.

## 5. Later

- Weapons.
- Real art.
- Tune fuel against an actual surface-to-orbit trip.

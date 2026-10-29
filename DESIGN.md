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
- Roles: pilot ×1 (Movement, needed to fly, Intellectual 6+ unless the flight computer is fitted; see Pilot
  skill), co-pilot ×1 (no handling, optional), passenger ×8.
- Cargo 1000 kg, mass 1800, flight speed 30.
- Components: hull (all cells), cockpit (front edge), port and starboard thrusters (side edges; flight speed
  and control), port and starboard wings (300 health, the hull's armour; the outer columns at z 1, 0, −1,
  where the art draws them; flight control), fuel tank (back edge, internal; leaks, may explode below 20%
  health). Cells: a 4×8 footprint facing north spans x −1..2, z −3..4 (north = z 4).
- Fuel: chemfuel, 1200 capacity, used only while flying. Enough to cross the planet twice in the air, or to
  reach orbit and work there for a while (see Range and Orbit costs).
- No weapons yet. When they come: VTOL Vehicle's `VtolVehicleTurret` in `CompProperties_VehicleTurrets`,
  as the Hind does.

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
matching part × (Hog vanilla / Hind vanilla). That's the same ratio rule as the VGE CE patch. Hull = Hind body,
thrusters = Hind engines. The plasteel armour upgrade's amounts become 20% of these.

| Part | Vanilla (blunt / sharp) | + upgrade | CE (blunt / sharp) | + upgrade (CE) |
|---|---|---|---|---|
| Hull | 0.50 / 0.90 | +0.10 / +0.18 | 22.5 / 11.6 | +4.5 / +2.32 |
| Cockpit | 0.45 / 0.80 | +0.09 / +0.16 | 13.8 / 8.6 | +2.76 / +1.72 |
| Port, starboard thruster | 0.45 / 0.80 | +0.09 / +0.16 | 17.9 / 9.3 | +3.58 / +1.86 |
| Port, starboard wing (as hull) | 0.50 / 0.90 | +0.10 / +0.18 | 22.5 / 11.6 | +4.5 / +2.32 |
| Fuel tank | 0.25 / 0.40 | +0.05 / +0.08 | 10 / 5.3 | +2 / +1.06 |

Not covered: the Hind's CE patch also gives its airframe CE's real collision width (CE treats every vehicle as
a one-cell-wide target). On the author's machine CE's own `VehiclesCompat` assembly fails to load (a
TypeLoadException for `VehiclePartDepth` from Vehicles 1.6), which may stop CE's vehicle armour from working at
all. That's a CE/VF version issue, not this mod's.

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

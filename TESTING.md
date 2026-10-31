# Hog Shuttle: in-game checks

Nothing here has been tested in game yet. Check `Player.log` for errors mentioning `HogShuttle` first.

## Loading
- [ ] No config or XML errors for `HogShuttle`, `HogShuttle_Blueprint` or `HogShuttle_Research`.
- [ ] VTOL Vehicle's "no aircraft found" letter does not appear.
- [ ] The invisible rotor causes no texture or rotor errors.

## Research
- [ ] "hog shuttle" shows in the Vehicles tab at column 3, row 0, linked to aerial vehicles.
- [ ] With Odyssey, it also needs shuttle; without Odyssey it loads and needs only aerial vehicles.
- [ ] Needs a hi-tech research bench with a multi-analyzer.

## Building
- [ ] Blueprint appears in the Vehicles architect tab after the research.
- [ ] Cost with Odyssey: 450 steel, 250 plasteel, 10 components, 3 advanced components, 2 shuttle engines.
- [ ] Cost without Odyssey: the same but 9 advanced components and no shuttle engine.
- [ ] Footprint is 4×7 and rotates to 7×4; the placeholder art lines up with it (Draw hitbox).
- [ ] Parked with the engines off: the art stops exactly at the 4-cell footprint, with no wing tips. The blueprint too.
- [ ] Engines on: the wing tips fade in over about 4 seconds and reach one cell past the footprint on each side, lined
      up with the body at any heading and at flight scale, with no visible seam in the default paint. After shutdown
      they fade out.
- [ ] The flight shadow keeps its wings, and doesn't show under a parked Hog.
- [ ] Repainted wings: a colour change stops at the footprint's edge (the tips keep the default paint; expected).
- [ ] The art at game zoom: the engines, yokes and roof plates read clearly, not as noise.
- [ ] Painting / patterns: hull and nacelles, cockpit armour + wing stripe, and wings take colours one, two and
      three.

## Crew and cargo
- [ ] Pilot seat needed to fly; co-pilot optional; 8 passenger seats.
- [ ] Cargo capacity about 1000 kg.

## Local-map flight (VTOL Vehicle)
- [ ] Take off, fly to a cell, land here, land at a cell, save a landing spot and auto-land.
- [ ] Board nearby and disembark crew.
- [ ] Engine sound plays during flight (VVE rocket engine) and stops after landing.
- [ ] Shadow draws under the shuttle in flight.
- [ ] Out of fuel in flight: emergency landing.

## World map and space (Odyssey)
- [ ] Launch to another surface tile and land.
- [ ] Launch to orbit: a gravship, an orbital site, an asteroid. Land there and come back.
- [ ] Range: on a full tank (1200) the launch targeter reaches about 720 tiles over the surface (1.67 fuel
      per tile).
- [ ] Orbit, straight up: the targeter shows about 50 fuel for an orbital target overhead, and about 50 is
      spent; the trip back down costs about 50 plus distance.
- [ ] Orbit to orbit: a hop between two orbital sites costs about 17 fuel per tile (10×), and the tank drains
      that fast in flight.
- [ ] A multi-stop path (surface → orbit → surface) shows and spends 50 for each change.
- [ ] Save mid-flight to orbit, load: no second 50 is taken.
- [ ] Other Vehicle Framework aircraft (VVE, the Hind) keep their old fuel costs.

## Pilot skill and flight computer
- [ ] A pilot with Intellectual 5 or less: the Hog can't move, take off or launch (Vehicle Framework's "not
      enough crew" state). With Intellectual 6+: it flies.
- [ ] Boarding through Vehicle Framework (the gizmo, a caravan) never puts an under-skilled pawn in the pilot
      seat; they take the co-pilot or passenger seats.
- [ ] VTOL Vehicle's "board nearby": check whether it can still seat an under-skilled pilot (the Hog should
      then just stay grounded).
- [ ] The Upgrades tab has "Auxiliary flight computer": 1 advanced component, 200 work, placeholder icon.
- [ ] With it installed, a pilot below Intellectual 6 can fly. If the state doesn't update at once, check
      after the pilot gets out and back in (Vehicle Framework may cache it).
- [ ] Removing it brings the requirement back. Co-pilot and passengers never need the skill.

## Plasteel armour
- [ ] The Upgrades tab has "Plasteel armour": 150 plasteel, 4 components, 6000 work, placeholder icon.
- [ ] Health tab lists all 16 parts (DESIGN.md table). A1, D1, A7 and D7 have no part: check what a hit there does
      (Vehicle Framework may pass it to the nearest part; under CE, the Hind notes such hits do no damage). Shots at the sides (A2-A6, D2-D6) hit the wings, and in
      rows 3-5 also the turbofans (rows 4-5 the rear skids); shots at the tail hit the rear door; the fuel tank sits in the centre (it leaks
      when hit). Damaged turbofans, wings, skids, fuel intake or fuel pumps lower flight speed or
      control; badly damaged turbofans cap both, and they never explode.
- [ ] Installed: every part's armour rises by about 20% in the
      Health tab, and cargo capacity drops from 1000 to 800 kg.
- [ ] Removed: armour and cargo return to normal; half the cost is refunded.
- [ ] Without CE: vanilla ratings (hull 0.50 / 0.90). With CE: CE ratings (hull 22.5 / 11.6) and the
      upgrade adds the CE amounts. No patch errors either way.

## Cargo outfit
- [ ] The Upgrades tab has "Cargo outfit": no ingredients, 500 work, placeholder icon.
- [ ] Installed: 2 passenger seats (pilot and co-pilot unchanged), cargo 2000 kg; with plasteel armour too,
      1800 kg. Removed: 8 seats and 1000 kg again.
- [ ] Fitting it with more than 2 passengers aboard: see what Vehicle Framework does with the extra pawns.
      Expected: nothing ejects them; they stay until they get out.

## Rear door gun
- [ ] Three door gun nodes; fitting one greys out the other two. Costs and work as in DESIGN.md.
- [ ] Fitted: a "door gunner" seat appears (1 slot). A gunner can fire; nobody else can. A pawn incapable of
      violence can't take the seat.
- [ ] The gun sits at the tail and points straight back when idle; it only swings 60 degrees to each side.
- [ ] In flight the gun turns with the aircraft's heading (VTOL turret class). A newly fitted gun points straight back
      at once, at any heading, with nobody aboard. On loading a save, a gun keeps the rotation it was saved with.
- [ ] Reloads from steel; without CE the box is 75 (minigun 200). With CE: 7.62x51 NATO / .50 BMG ammo.
- [ ] The guns show VVE - Secondary Weapons' art, sounds and turret icon (it's a dependency now).
- [ ] Removing the upgrade removes the gun and the gunner seat (the gunner gets out).

## Autocannon
- [ ] Log: no Harmony error for `MagosZ.HogShuttle`, and no error about `HogShuttle.PilotGunExtension`.
- [ ] The Upgrades tab has "Autocannon": 100 steel, 15 plasteel, 3 components, 6000 work. It can be fitted together with
      a door gun, not with the front minigun.
- [ ] Cargo capacity drops by 30 kg when fitted (970; with plasteel armour 770; with the cargo outfit 1970; with
      both 1770) and comes back when removed.
- [ ] Fitted: the turret draws on the roof behind the cockpit, on the centre line, at any heading, parked and in flight.
      Without the upgrade, no gun shows.
- [ ] It swings 30 degrees either side of the nose on its own: the head and barrel turn, the mounting ring looks fixed, and
      the nose doesn't turn for it, by hand or on auto-target. After firing it swings back to face forward.
- [ ] A newly fitted gun on a Hog parked facing east or west: it points forward straight away, with nobody aboard.
- [ ] Without CE: 3-round bursts every 3.5 s or so, range 8.9 to 29.6, 27 damage, 135 rounds at 2 steel each. Shots and the
      muzzle flash leave from the muzzle, also at full traverse.
- [ ] With CE: 20x102mm shells (AP by default), 150 rounds, range 70.2, 10-round bursts every second or so, 2.3 s warm-up;
      the shells fly straight and land on the target.

## Front minigun
- [ ] The Upgrades tab has "Front minigun": 135 steel, 11 components, 5000 work. Cargo capacity doesn't change. It can be
      fitted together with a door gun, not with the autocannon.
- [ ] Fitted: only the barrel shows, on the starboard side beside the cockpit, with the receiver hidden under the wing.
      Parked and in flight, at any heading.
- [ ] Its arc is 6 degrees either side of the nose. Airborne with a target by hand: the nose turns to it. Parked, it can
      only reach what's nearly straight ahead.
- [ ] Hovering on auto-target: the nose turns to enemies (VTOL's combat hover, key `frontGun`).
- [ ] Without CE: 25-round bursts, range 30.9, 200 rounds, steel. Accuracy doesn't change with the pilot's Shooting skill.
- [ ] With CE: Single / Burst / Auto, range 62, 2000 rounds of 7.62×51 NATO; the shells fly straight.

## Front gun and the pilot
- [ ] Pilot capable of violence: the gun fires, with no extra seat. Nobody in the pilot's seat: it doesn't, and its button
      says "Needs a pilot capable of violence."
- [ ] Pilot incapable of violence: boards the pilot's seat and flies. The gun doesn't fire or auto-target, its button is
      greyed out, and a caution message names the pilot. Check boarding, dragging between seats in the crew tab, and
      VTOL's "board nearby".
- [ ] No message: on loading a save with such a pilot aboard, for a pilot capable of violence, for a pacifist co-pilot
      or passenger, or on a Hog without a front gun.
- [ ] A pacifist pilot hovering with enemies near, minigun fitted: see whether the nose still turns to them with the gun
      dead (VTOL's combat hover may ignore the gun's state).
- [ ] **Check on every Hog:** combat hover is on and names a turret that only exists once the minigun is fitted. Without it:
      no log errors, and the nose doesn't turn by itself.
- [ ] Door gun fitted: see whether its auto-target swings the nose round to enemies behind (the Hind needed extra code to
      stop this; the Hog has none). Also with the autocannon fitted, whether its targets do.

## Chemical toilet (with Dubs Bad Hygiene)
- [ ] The Upgrades tab also has "Chemical toilet", with the description and the placeholder icon; without DBH
      only the flight computer is there.
- [ ] Installing it needs 10 steel and 10 neutroamine and takes about as long as building a wooden wall.
- [ ] With it installed, the bladder need of everyone aboard (pilot, co-pilot, passengers) stays full, on the
      map and on the world map; nobody wets themselves on a long trip.
- [ ] Without it, bladder drains as before. Removing it refunds half the cost.
- [ ] Without DBH: no toilet node and no errors.

## Sealed cabin
- [ ] Log: no Harmony error for `MagosZ.HogShuttle`; no error about `HogShuttle.StatPart_SealedCabinVacuum`.
- [ ] In orbit (−75 °C, full vacuum), pawns aboard for a few hours: no hypothermia, no vacuum exposure, no
      vacuum burns.
- [ ] A pawn aboard: vacuum resistance shows 100% with an "Inside a sealed cabin" line in its breakdown.
- [ ] Passengers still get hungry over time (needs keep ticking, as Vehicle Framework intends).
- [ ] Cargo in orbit doesn't freeze; food in the hold rots at room-temperature speed.
- [ ] A pawn who gets out loses the protection again: vacuum resistance back to normal right away or after a
      short delay (the stat is cached), and outside temperature applies.
- [ ] Other Vehicle Framework vehicles (VVE, the Hind) are unchanged: passengers still feel the outside temperature.

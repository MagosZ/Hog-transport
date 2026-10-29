"""The Hog's components, in one table: writes the <components> block of Defs/VehicleDefs/HogShuttle.xml, the plasteel
armour upgrade's <armor> list in Defs/HogShuttle_UpgradeTree.xml, and Mods/CombatExtended/Patches/
HogShuttle_CombatExtended.xml.

Run from anywhere: python components.py

Cells: a 4x8 footprint facing north spans x -1..2, z -3..4 (north = z 4), as GenAdj.OccupiedRect.
Grid names (DESIGN.md): columns A-D = x -1, 0, 1, 2 (port to starboard), rows 1-8 = z 4 down to -3 (nose to tail).
Parts follow VVE's helicopters (Mosquito, Louie, Cherokee), turned into spacecraft parts: engine -> engine core,
fuel intake, transmission -> fuel pumps, chemtank -> fuel tank, rotor mast -> the turbofans, skids -> landing gear,
dashboard -> avionics, upholstery -> cabin seats, servos -> control servos. VVE's stabilizers and rudder are the
Hog's wings; VVE's side panels are its hull. Health is the Louie's x1.5 (the Hog has 32 cells to its 21). Positions
follow the Arvus lighter; a part may cover several cells, and cells may hold several parts.
"""
import re
from pathlib import Path

MOD = Path(__file__).resolve().parents[2]

# Armour classes (vanilla blunt, sharp; Combat Extended blunt, sharp). CE = the Hind Gunship's CE rating for the
# matching part x (Hog vanilla / Hind vanilla), as in the first CE patch.
HULL = ((0.50, 0.90), (22.5, 11.6))
COCKPIT = ((0.45, 0.80), (13.8, 8.6))
EXTERNAL = ((0.45, 0.80), (17.9, 9.3))   # thrusters and other outer parts (Hind engines)
INTERNAL = ((0.25, 0.40), (10.0, 5.3))   # inside the hull (Hind fuel tank)

EXPLOSIVE = """<li Class="Vehicles.Reactor_Explosive">
	<indicator>VF_Explosive</indicator>
	<chance>0.08</chance>
	<maxHealth>0.2</maxHealth>
	<radius>3</radius>
	<damageDef>Bomb</damageDef>
	<damage>10</damage>
</li>"""
LEAK = '<li Class="Vehicles.Reactor_FuelLeak" />'


def grid(*names):
    """Cells from grid names: "B4", or a column or row run such as "A3-A6" or "A8-D8"."""
    out = []
    for name in names:
        a, _, b = name.partition("-")
        b = b or a
        for col in range(ord(a[0]), ord(b[0]) + 1):
            for row in range(int(a[1:]), int(b[1:]) + 1):
                out.append((col - ord("A") - 1, 5 - row))   # A..D -> x -1..2, rows 1..8 -> z 4..-3
    return out


# key, label, health, depth, hitWeight, priorityStatEfficiency, categories, reactors, armour, hitbox, note
# Layout after the Arvus lighter (Warhammer Community pictures): cockpit box at the front centre, two turbofans and
# the wings on the sides of the middle (rows 3-6), three landing legs (nose, and both sides), cargo bay with the
# fuel tank in the middle, engine core behind it, rear door at the tail.
PARTS = [
    ("Hull", "hull", 900, "External", 3, False, [], [], HULL, "Body", "Covers every cell."),
    ("Cockpit", "cockpit", 200, "External", 1, False, [], [], COCKPIT, grid("B1-C2"),
     "The cockpit box at the front centre."),
    ("ThrusterPort", "port turbofan", 220, "External", 1, False, ["FlightSpeed", "FlightControl"], [], EXTERNAL,
     grid("A3-A6"), "The Arvus' two ducted turbofans, on the sides: they lift and push."),
    ("ThrusterStarboard", "starboard turbofan", 220, "External", 1, False, ["FlightSpeed", "FlightControl"], [],
     EXTERNAL, grid("D3-D6"), None),
    ("WingPort", "port wing", 300, "External", 1, False, ["FlightControl"], [], HULL, grid("A3-A6"),
     "Wings: the hull's armour (VVE's stabilizers and rudder)."),
    ("WingStarboard", "starboard wing", 300, "External", 1, False, ["FlightControl"], [], HULL, grid("D3-D6"), None),
    ("LandingGearFront", "front landing gear", 120, "External", 1, False, ["FlightSpeed"], [], EXTERNAL,
     grid("B2-C2"), "Three landing legs (VVE's skids): one under the nose, one each side."),
    ("LandingGearPort", "port landing gear", 120, "External", 1, False, ["FlightSpeed"], [], EXTERNAL,
     grid("A3-A6"), None),
    ("LandingGearStarboard", "starboard landing gear", 120, "External", 1, False, ["FlightSpeed"], [], EXTERNAL,
     grid("D3-D6"), None),
    ("RearDoor", "rear door", 150, "External", 1, False, [], [], EXTERNAL, grid("A8-D8"),
     "The cargo bay's rear door."),
    ("FuelIntake", "fuel intake", 75, "External", 1, False, ["FlightSpeed"], [], EXTERNAL, grid("B8-C8"), None),
    ("EngineCore", "engine core", 180, "Internal", 1, True, ["FlightSpeed", "FlightControl"], [EXPLOSIVE], INTERNAL,
     grid("B7-C7"), "VVE's engine: its efficiency leads the flight stats."),
    ("FuelPumps", "fuel pumps", 75, "Internal", 1, False, ["FlightSpeed"], [], INTERNAL, grid("B6-C6"),
     "VVE's transmission."),
    ("FuelTank", "fuel tank", 180, "Internal", 1, False, [], [LEAK, EXPLOSIVE], INTERNAL, grid("B4-C5"),
     "In the centre. A critically damaged tank (20% health or less) can blow on a hit."),
    ("Avionics", "avionics", 75, "Internal", 2, False, [], [], INTERNAL, grid("B1-C1"),
     "VVE's dashboard, behind the cockpit glass."),
    ("CabinSeats", "cabin seats", 75, "Internal", 2, False, [], [], INTERNAL, grid("B3-C3"), "VVE's upholstery."),
    ("ControlServos", "control servos", 105, "Internal", 2, False, [], [], INTERNAL, grid("B6-C6"), "VVE's servos."),
]


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".") if abs(x) < 1 else f"{x:.2f}".rstrip("0").rstrip(".")


def indent(text, tabs):
    return "\n".join("\t" * tabs + line for line in text.splitlines())


def components_xml():
    out = ["\t\t<components>",
           "\t\t\t<!-- Generated by Source/Art/components.py: edit the table there and re-run it. -->"]
    for key, label, hp, depth, weight, prio, cats, reactors, armour, hitbox, note in PARTS:
        (vb, vs), _ = armour
        if note:
            out.append(f"\t\t\t<!-- {note} -->")
        out += ["\t\t\t<li>", f"\t\t\t\t<key>{key}</key>", f"\t\t\t\t<label>{label}</label>",
                f"\t\t\t\t<health>{hp}</health>"]
        if weight != 1:
            out.append(f"\t\t\t\t<hitWeight>{weight}</hitWeight>")
        if prio:
            out.append("\t\t\t\t<priorityStatEfficiency>true</priorityStatEfficiency>")
        out += [f"\t\t\t\t<depth>{depth}</depth>", "\t\t\t\t<armor>",
                f"\t\t\t\t\t<ArmorRating_Blunt>{vb:.2f}</ArmorRating_Blunt>",
                f"\t\t\t\t\t<ArmorRating_Sharp>{vs:.2f}</ArmorRating_Sharp>", "\t\t\t\t</armor>",
                "\t\t\t\t<hitbox>"]
        if isinstance(hitbox, str):
            out.append(f"\t\t\t\t\t<side>{hitbox}</side>")
        else:
            out.append("\t\t\t\t\t<cells>")
            out += [f"\t\t\t\t\t\t<li>({x}, {z})</li>" for x, z in hitbox]
            out.append("\t\t\t\t\t</cells>")
        out.append("\t\t\t\t</hitbox>")
        if cats:
            out += ["\t\t\t\t<categories>"] + [f"\t\t\t\t\t<li>{c}</li>" for c in cats] + ["\t\t\t\t</categories>"]
        if reactors:
            out += ["\t\t\t\t<reactors>"] + [indent(r, 5) for r in reactors] + ["\t\t\t\t</reactors>"]
        out.append("\t\t\t</li>")
    out.append("\t\t</components>")
    return "\n".join(out)


def upgrade_armor_xml(ce=False):
    """The armour upgrade adds 20% of each component's rating."""
    out = []
    for key, *_rest in PARTS:
        armour = _rest[7]
        b, s = armour[1] if ce else armour[0]
        out.append((key, round(b * 0.2, 2), round(s * 0.2, 2)))
    return out


def write_vehicle():
    p = MOD / "Defs/VehicleDefs/HogShuttle.xml"
    t = p.read_text(encoding="utf-8")
    t, n = re.subn(r"\t\t<components>.*?\t\t</components>", lambda m: components_xml(), t, count=1, flags=re.S)
    assert n == 1
    p.write_text(t, encoding="utf-8", newline="\n")


def write_upgrade():
    p = MOD / "Defs/HogShuttle_UpgradeTree.xml"
    t = p.read_text(encoding="utf-8")
    lines = ["\t\t\t\t\t\t<armor>"]
    for key, b, s in upgrade_armor_xml():
        lines += ["\t\t\t\t\t\t\t<li>", f"\t\t\t\t\t\t\t\t<key>{key}</key>", "\t\t\t\t\t\t\t\t<type>Add</type>",
                  "\t\t\t\t\t\t\t\t<statModifiers>",
                  f"\t\t\t\t\t\t\t\t\t<ArmorRating_Blunt>{b:.2f}</ArmorRating_Blunt>",
                  f"\t\t\t\t\t\t\t\t\t<ArmorRating_Sharp>{s:.2f}</ArmorRating_Sharp>",
                  "\t\t\t\t\t\t\t\t</statModifiers>", "\t\t\t\t\t\t\t</li>"]
    lines.append("\t\t\t\t\t\t</armor>")
    t, n = re.subn(r"\t\t\t\t\t\t<armor>.*?\t\t\t\t\t\t</armor>", lambda m: "\n".join(lines), t, count=1, flags=re.S)
    assert n == 1
    p.write_text(t, encoding="utf-8", newline="\n")


def write_ce():
    p = MOD / "Mods/CombatExtended/Patches/HogShuttle_CombatExtended.xml"
    out = ['<?xml version="1.0" encoding="utf-8"?>', "<Patch>",
           "\t<!-- Loaded only with Combat Extended (LoadFolders.xml). Without CE the vanilla ratings in Defs/ apply.",
           "\t     Generated by Source/Art/components.py. Each armour class takes the Hind Gunship's CE rating for the",
           "\t     matching part, scaled by the Hog's vanilla rating over the Hind's: hull and wings = Hind body, cockpit =",
           "\t     Hind cockpit, outer parts = Hind engines, inner parts = Hind fuel tank. The plasteel armour upgrade adds",
           "\t     20% of these, in place of 20% of the vanilla ratings. -->"]
    for key, *_rest in PARTS:
        b, s = _rest[7][1]
        out += ["\t<Operation Class=\"PatchOperationReplace\">",
                f"\t\t<xpath>Defs/Vehicles.VehicleDef[defName=\"HogShuttle\"]/components/li[key=\"{key}\"]/armor</xpath>",
                "\t\t<value>", "\t\t\t<armor>", f"\t\t\t\t<ArmorRating_Blunt>{b:g}</ArmorRating_Blunt>",
                f"\t\t\t\t<ArmorRating_Sharp>{s:g}</ArmorRating_Sharp>", "\t\t\t</armor>", "\t\t</value>",
                "\t</Operation>"]
    out.append("\n\t<!-- Plasteel armour upgrade (Defs/HogShuttle_UpgradeTree.xml): 20% of the ratings above. -->")
    for key, b, s in upgrade_armor_xml(ce=True):
        out += ["\t<Operation Class=\"PatchOperationReplace\">",
                "\t\t<xpath>Defs/Vehicles.UpgradeTreeDef[defName=\"HogShuttle_UpgradeTree\"]/nodes/"
                f"li[key=\"HogShuttle_PlasteelArmour\"]/upgrades/li/armor/li[key=\"{key}\"]/statModifiers</xpath>",
                "\t\t<value>", "\t\t\t<statModifiers>", f"\t\t\t\t<ArmorRating_Blunt>{b:g}</ArmorRating_Blunt>",
                f"\t\t\t\t<ArmorRating_Sharp>{s:g}</ArmorRating_Sharp>", "\t\t\t</statModifiers>", "\t\t</value>",
                "\t</Operation>"]
    out.append("</Patch>")
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def main():
    write_vehicle()
    write_upgrade()
    write_ce()
    for key, label, hp, depth, weight, prio, cats, reactors, armour, hitbox, note in PARTS:
        print(f"{key:21} {hp:4} {depth:8} {armour[0]} CE {armour[1]} {hitbox}")


if __name__ == "__main__":
    main()

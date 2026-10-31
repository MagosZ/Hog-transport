using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: the turrets with keys in <see cref="turrets"/> are fired by whoever sits in
    /// <see cref="role"/>. The seat keeps Movement handling only, because Vehicle Framework bars pawns incapable of
    /// violence from any seat with Turret handling, and those pawns should still be able to fly. So no role lists
    /// these turrets, and the patches here decide whether they count as manned.</summary>
    public class PilotGunExtension : DefModExtension
    {
        public string role = "Pilot";
        public List<string> turrets;

        public static PilotGunExtension For(VehicleTurret turret)
        {
            PilotGunExtension gun = turret?.vehicle?.def.GetModExtension<PilotGunExtension>();
            return gun?.turrets != null && gun.turrets.Contains(turret.key) ? gun : null;
        }
    }

    /// <summary>Vehicle Framework rechecks this whenever anyone boards, leaves, changes seats, dies or is hurt. With
    /// no role listing the turret it would count as always manned. Also tells the player when a pawn incapable of
    /// violence takes the seat, once per vehicle however many guns it has. The first check of a vehicle only records
    /// the pilot, so loading a save says nothing.</summary>
    [HarmonyPatch]
    public static class Patch_VehicleTurret_RecacheMannedStatus
    {
        private static readonly Action<VehicleTurret, bool> SetIsManned =
            AccessTools.MethodDelegate<Action<VehicleTurret, bool>>(
                AccessTools.PropertySetter(typeof(VehicleTurret), nameof(VehicleTurret.IsManned)));

        private static readonly ConditionalWeakTable<VehiclePawn, StrongBox<Pawn>> LastPilot =
            new ConditionalWeakTable<VehiclePawn, StrongBox<Pawn>>();

        public static IEnumerable<MethodBase> TargetMethods()
        {
            yield return AccessTools.Method(typeof(VehicleTurret), nameof(VehicleTurret.RecacheMannedStatus));
            // VTOL Vehicle is closed source; cover its turret class in case it overrides the check.
            Type vtolTurret = AccessTools.TypeByName("VTOLVehicle.VtolVehicleTurret");
            MethodInfo declared = vtolTurret == null
                ? null
                : AccessTools.DeclaredMethod(vtolTurret, nameof(VehicleTurret.RecacheMannedStatus));
            if (declared != null)
            {
                yield return declared;
            }
        }

        public static void Postfix(VehicleTurret __instance)
        {
            PilotGunExtension gun = PilotGunExtension.For(__instance);
            if (gun == null)
            {
                return;
            }
            VehiclePawn vehicle = __instance.vehicle;
            VehicleRoleHandler handler = vehicle.GetHandler(gun.role);
            Pawn pilot = handler == null || handler.thingOwner.Count == 0 ? null : handler.thingOwner[0];
            bool pacifist = pilot != null && pilot.WorkTagIsDisabled(WorkTags.Violent);

            if (!VehicleMod.settings.debug.debugShootAnyTurret)
            {
                SetIsManned(__instance, pilot != null && !pacifist && handler.RoleFulfilled);
            }

            if (!LastPilot.TryGetValue(vehicle, out StrongBox<Pawn> last))
            {
                LastPilot.Add(vehicle, new StrongBox<Pawn>(pilot));
                return;
            }
            if (last.Value == pilot)
            {
                return;
            }
            last.Value = pilot;
            if (pacifist && vehicle.Faction == Faction.OfPlayerSilentFail)
            {
                Messages.Message("HogShuttle_PacifistPilot".Translate(pilot.LabelShort, vehicle.LabelShort),
                    new LookTargets(vehicle), MessageTypeDefOf.CautionInput, false);
            }
        }
    }

    /// <summary>Greys out the gun's button with a reason; Vehicle Framework's own reason looks at role seats.</summary>
    [HarmonyPatch(typeof(VehicleTurret), nameof(VehicleTurret.IsDisabled))]
    public static class Patch_VehicleTurret_IsDisabled
    {
        public static void Postfix(VehicleTurret __instance, ref bool __result, ref string reason)
        {
            if (__result || __instance.IsManned || PilotGunExtension.For(__instance) == null)
            {
                return;
            }
            __result = true;
            reason = "HogShuttle_GunNeedsPilot".Translate();
        }
    }
}

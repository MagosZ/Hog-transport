using System;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;
using Verse.AI;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: VTOL Vehicle's combat hover answers only to the turret with key <see cref="turret"/>, and
    /// holds the nose on its target.</summary>
    public class SteadyFrontGunExtension : DefModExtension
    {
        public string turret;
    }

    /// <summary>VTOL Vehicle stops applying the combat facing once the hovering aircraft has lined up, and hands the nose back
    /// to the last move order's facing. The nose wanders off, comes back, and the gun loses its target over and over. So
    /// the combat facing stays applied.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_ShouldApplyCombatFacing
    {
        private static readonly Type Controller = AccessTools.TypeByName("VTOLVehicle.VtolFlightController");
        private static readonly FieldInfo Vehicle = Controller == null ? null : AccessTools.Field(Controller, "vehicle");

        public static bool Prepare() => TargetMethod() != null && Vehicle != null;

        public static MethodBase TargetMethod() =>
            Controller == null ? null : AccessTools.Method(Controller, "ShouldApplyCombatDirectionalHoverFacing");

        public static void Postfix(object __instance, ref bool __result)
        {
            if (!__result && (Vehicle.GetValue(__instance) as VehiclePawn)?.def.GetModExtension<SteadyFrontGunExtension>() != null)
            {
                __result = true;
            }
        }
    }

    /// <summary>VTOL Vehicle's combat hover turns the nose to the best target of any auto-targeting gun, so a door gun's
    /// target behind the shuttle would swing the front gun away from its own. Only the front gun's target counts, and with
    /// no front gun, or one that can't fire, the nose stays free.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_BestAutoTarget
    {
        // VTOL Vehicle's own scan flag for these searches, which looks past the gun's arc.
        private const TargetScanFlags HoverScan = (TargetScanFlags)256;

        private static readonly Type Controller = AccessTools.TypeByName("VTOLVehicle.VtolFlightController");
        private static readonly FieldInfo Vehicle = Controller == null ? null : AccessTools.Field(Controller, "vehicle");
        private static readonly MethodInfo IsValid =
            Controller == null ? null : AccessTools.Method(Controller, "IsValidCombatDirectionalHoverTarget");

        public static bool Prepare() => TargetMethod() != null && Vehicle != null && IsValid != null;

        public static MethodBase TargetMethod() =>
            Controller == null ? null : AccessTools.Method(Controller, "BestVehicleTurretAutoTarget");

        public static void Postfix(object __instance, ref Thing __result)
        {
            VehiclePawn vehicle = Vehicle.GetValue(__instance) as VehiclePawn;
            SteadyFrontGunExtension steady = vehicle?.def.GetModExtension<SteadyFrontGunExtension>();
            if (steady == null)
            {
                return;
            }
            __result = null;
            foreach (VehicleTurret turret in vehicle.CompVehicleTurrets?.Turrets ?? new System.Collections.Generic.List<VehicleTurret>())
            {
                if (turret.key == steady.turret && turret.AutoTarget && !turret.TurretDisabled &&
                    turret.TryGetTarget(out LocalTargetInfo found, HoverScan) && found.HasThing &&
                    (bool)IsValid.Invoke(__instance, new object[] { found.Thing, true }))
                {
                    __result = found.Thing;
                }
            }
        }
    }
}

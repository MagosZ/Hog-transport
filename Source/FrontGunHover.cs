using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;
using Verse.AI;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: the gun with key <see cref="turret"/> drives: VTOL Vehicle's combat hover answers only to it
    /// and holds the nose on its target. Other guns never turn the shuttle.</summary>
    public class SteadyFrontGunExtension : DefModExtension
    {
        public string turret;

        public VehicleTurret Driver(VehiclePawn vehicle)
        {
            IReadOnlyList<VehicleTurret> fitted = vehicle.CompVehicleTurrets?.Turrets;
            if (fitted != null)
            {
                foreach (VehicleTurret candidate in fitted)
                {
                    if (candidate.key == turret)
                    {
                        return candidate;
                    }
                }
            }
            return null;
        }
    }

    /// <summary>VTOL Vehicle's flight controller, by reflection: the build has no reference to VTOLVehicle.dll. Method and
    /// field names as the Hind Gunship's source uses them.</summary>
    internal static class Vtol
    {
        public static readonly Type Controller = AccessTools.TypeByName("VTOLVehicle.VtolFlightController");
        public static readonly FieldInfo ControllerVehicle = Controller == null ? null : AccessTools.Field(Controller, "vehicle");

        public static readonly Type Turret = AccessTools.TypeByName("VTOLVehicle.VtolVehicleTurret");
        public static readonly MethodInfo IsValidHoverTarget =
            Controller == null ? null : AccessTools.Method(Controller, "IsValidCombatDirectionalHoverTarget");

        public static readonly MethodInfo LastRequest =
            Turret == null ? null : AccessTools.PropertyGetter(Turret, "LastVtolTargetRequest");
        public static readonly MethodInfo FacingFor =
            Turret == null ? null : AccessTools.Method(Turret, "TryGetVehicleFacingForTarget");

        public static MethodInfo Method(string name) => Controller == null ? null : AccessTools.Method(Controller, name);

        public static VehiclePawn VehicleOf(object controller) => ControllerVehicle?.GetValue(controller) as VehiclePawn;

        public static VehicleTurret DriverOf(object controller)
        {
            VehiclePawn vehicle = VehicleOf(controller);
            return vehicle?.def.GetModExtension<SteadyFrontGunExtension>()?.Driver(vehicle);
        }

        public static Thing Request(VehicleTurret turret) =>
            LastRequest != null && Turret.IsInstanceOfType(turret) ? ((LocalTargetInfo)LastRequest.Invoke(turret, null)).Thing : null;

        /// <summary>What the driving gun is after: its own target, else the one asked for by hand.</summary>
        public static Thing Aim(object controller, VehicleTurret driver)
        {
            if (driver == null || driver.TurretDisabled || IsValidHoverTarget == null)
            {
                return null;
            }
            Thing own = driver.targetInfo.Thing;
            if (Usable(controller, driver, own))
            {
                return own;
            }
            Thing asked = Request(driver);
            return Usable(controller, driver, asked) ? asked : null;
        }

        private static bool Usable(object controller, VehicleTurret turret, Thing thing) =>
            thing != null && thing.Spawned && !thing.Destroyed &&
            (bool)IsValidHoverTarget.Invoke(controller, new object[] { thing, true }) &&
            turret.InRange(new LocalTargetInfo(thing));
    }

    /// <summary>Diagnostics for the steering, in development mode only, at most once a second per vehicle and step. VTOL
    /// Vehicle is closed source, so this is how its steps can be seen. The hooks found are listed once at startup.</summary>
    [StaticConstructorOnStartup]
    internal static class SteerLog
    {
        private static readonly Dictionary<string, int> Last = new Dictionary<string, int>();

        static SteerLog()
        {
            string Found(MethodInfo m) => m != null ? "yes" : "NO";
            Log.Message("[HogShuttle] VTOL steering hooks: TryGetTurretCombatFacing " + Found(Vtol.Method("TryGetTurretCombatFacing")) +
                ", ShouldApplyCombatDirectionalHoverFacing " + Found(Vtol.Method("ShouldApplyCombatDirectionalHoverFacing")) +
                ", TryManualTurretTargetFacing " + Found(Vtol.Method("TryManualTurretTargetFacing")) +
                ", BestVehicleTurretAutoTarget " + Found(Vtol.Method("BestVehicleTurretAutoTarget")) +
                ", IsValidCombatDirectionalHoverTarget " + Found(Vtol.IsValidHoverTarget) +
                ", LastVtolTargetRequest " + Found(Vtol.LastRequest) + ", TryGetVehicleFacingForTarget " + Found(Vtol.FacingFor));
        }

        public static void Note(VehiclePawn vehicle, string step, string text)
        {
            if (!Prefs.DevMode || vehicle == null)
            {
                return;
            }
            string key = vehicle.thingIDNumber + step;
            int now = Find.TickManager.TicksGame;
            if (Last.TryGetValue(key, out int last) && now - last < 60)
            {
                return;
            }
            Last[key] = now;
            Log.Message($"[HogShuttle] {vehicle.LabelShort} {step}: {text}");
        }
    }

    /// <summary>VTOL Vehicle's combat facing only follows a gun's current target. A fixed gun can't take a target outside its
    /// narrow arc, so a target given by hand off the nose stays a request (LastVtolTargetRequest) and the nose never turns
    /// to it. So the minigun's own target comes first, then the one asked for by hand, and the nose turns to whichever it
    /// is. With neither, VTOL picks as usual.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_CombatFacing
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null &&
            Vtol.IsValidHoverTarget != null && Vtol.LastRequest != null && Vtol.FacingFor != null;

        public static MethodBase TargetMethod() => Vtol.Method("TryGetTurretCombatFacing");

        public static bool Prefix(object __instance, ref bool __result, ref float facingAngle, ref Thing target)
        {
            VehicleTurret driver = Vtol.DriverOf(__instance);
            Thing aim = Vtol.Aim(__instance, driver);
            if (aim == null)
            {
                SteerLog.Note(driver?.vehicle, "combat facing", driver == null ? "no minigun, VTOL picks" :
                    $"nothing to aim at (own {driver.targetInfo}, asked {Vtol.Request(driver)?.LabelShort ?? "none"}), VTOL picks");
                return true;
            }
            object[] args = { aim.DrawPos, 0f };
            if (!(bool)Vtol.FacingFor.Invoke(driver, args))
            {
                SteerLog.Note(driver.vehicle, "combat facing", $"no facing for {aim.LabelShort}, VTOL picks");
                return true;
            }
            facingAngle = (float)args[1];
            target = aim;
            __result = true;
            SteerLog.Note(driver.vehicle, "combat facing", $"facing {facingAngle:0} for {aim.LabelShort}");
            return false;
        }
    }

    /// <summary>For the log only: what VTOL Vehicle's own steering for a target given by hand comes up with.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_ManualFacing_Log
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null;

        public static MethodBase TargetMethod() => Vtol.Method("TryManualTurretTargetFacing");

        public static void Postfix(object __instance, bool __result, float facingAngle, Thing target)
        {
            if (Prefs.DevMode && Vtol.VehicleOf(__instance)?.def.GetModExtension<SteadyFrontGunExtension>() != null)
            {
                SteerLog.Note(Vtol.VehicleOf(__instance), "manual facing",
                    __result ? $"facing {facingAngle:0} for {target?.LabelShort ?? "a cell"}" : "none");
            }
        }
    }

    /// <summary>For the log only: what a target given to the minigun becomes.</summary>
    [HarmonyPatch]
    public static class Patch_VehicleTurret_SetTarget_Log
    {
        public static IEnumerable<MethodBase> TargetMethods()
        {
            yield return AccessTools.Method(typeof(VehicleTurret), nameof(VehicleTurret.SetTarget), new[] { typeof(LocalTargetInfo) });
            MethodInfo vtol = Vtol.Turret == null ? null : AccessTools.DeclaredMethod(Vtol.Turret, "SetTarget", new[] { typeof(LocalTargetInfo) });
            if (vtol != null)
            {
                yield return vtol;
            }
        }

        public static void Postfix(VehicleTurret __instance, LocalTargetInfo target)
        {
            if (!Prefs.DevMode || !target.IsValid || __instance.vehicle?.def.GetModExtension<SteadyFrontGunExtension>() == null)
            {
                return;
            }
            Log.Message($"[HogShuttle] {__instance.vehicle.LabelShort} {__instance.key} asked for {target}: now has {__instance.targetInfo}, " +
                $"request {Vtol.Request(__instance)?.LabelShort ?? "none"}");
        }
    }

    /// <summary>VTOL Vehicle stops applying the combat facing once the hovering aircraft has lined up, and hands the nose back
    /// to the last move order's facing. The nose wanders off, comes back, and the gun loses its target over and over. So
    /// the combat facing stays applied while the minigun has a target.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_ShouldApplyCombatFacing
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null;

        public static MethodBase TargetMethod() => Vtol.Method("ShouldApplyCombatDirectionalHoverFacing");

        public static void Postfix(object __instance, ref bool __result)
        {
            if (__result)
            {
                return;
            }
            // Only while the minigun is after something, so VTOL's own steering for a target given by hand isn't shut out.
            VehicleTurret driver = Vtol.DriverOf(__instance);
            if (Vtol.Aim(__instance, driver) != null)
            {
                __result = true;
                SteerLog.Note(driver.vehicle, "hold facing", "kept on");
            }
        }
    }

    /// <summary>VTOL Vehicle's combat hover turns the nose to the best target of any auto-targeting gun, so a door gun's
    /// target behind the shuttle, or the autocannon's, would swing the nose. Only the minigun's target counts, and with no
    /// minigun, or one that can't fire, the nose stays free.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_BestAutoTarget
    {
        // VTOL Vehicle's own scan flag for these searches, which looks past the gun's arc.
        private const TargetScanFlags HoverScan = (TargetScanFlags)256;

        private static readonly MethodInfo IsValid = Vtol.IsValidHoverTarget;

        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null && IsValid != null;

        public static MethodBase TargetMethod() => Vtol.Method("BestVehicleTurretAutoTarget");

        public static void Postfix(object __instance, ref Thing __result)
        {
            VehiclePawn vehicle = Vtol.VehicleOf(__instance);
            SteadyFrontGunExtension steady = vehicle?.def.GetModExtension<SteadyFrontGunExtension>();
            if (steady == null)
            {
                return;
            }
            __result = null;
            VehicleTurret driver = steady.Driver(vehicle);
            if (driver != null && driver.AutoTarget && !driver.TurretDisabled &&
                driver.TryGetTarget(out LocalTargetInfo found, HoverScan) && found.HasThing &&
                (bool)IsValid.Invoke(__instance, new object[] { found.Thing, true }))
            {
                __result = found.Thing;
            }
        }
    }
}

using HarmonyLib;
using Vehicles;
using Vehicles.Rendering;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: pictures of a vehicle in the UI show it without the guns fitted to it.</summary>
    public class BareHullIconsExtension : DefModExtension
    {
    }

    /// <summary>The shared request for a vehicle's picture, used by the "before" side of the Upgrades tab's comparison and by
    /// other UI icons. The "after" side builds its own request, so it still shows the guns.</summary>
    [HarmonyPatch(typeof(BlitRequest), nameof(BlitRequest.For), new[] { typeof(VehiclePawn) })]
    public static class Patch_BlitRequest_For
    {
        public static void Postfix(VehiclePawn vehicle, ref BlitRequest __result)
        {
            if (vehicle.def.GetModExtension<BareHullIconsExtension>() != null)
            {
                __result.blitTargets.RemoveAll(target => target is VehicleTurret);
            }
        }
    }
}

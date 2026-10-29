using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using Verse;

namespace HogShuttle
{
    /// <summary>Things aboard a sealed cabin feel its temperature instead of the cell's. Vehicle Framework ticks
    /// passengers and cargo every tick, so without this they freeze (hypothermia) in space.</summary>
    [HarmonyPatch]
    public static class Patch_AmbientTemperature
    {
        // Thing's getter, plus Pawn's if Pawn declares its own (then Thing's would not run for pawns).
        public static IEnumerable<MethodBase> TargetMethods()
        {
            yield return AccessTools.PropertyGetter(typeof(Thing), nameof(Thing.AmbientTemperature));
            MethodInfo pawnGetter = AccessTools.DeclaredPropertyGetter(typeof(Pawn), nameof(Thing.AmbientTemperature));
            if (pawnGetter != null)
            {
                yield return pawnGetter;
            }
        }

        public static void Postfix(Thing __instance, ref float __result)
        {
            SealedCabinExtension cabin = SealedCabin.HolderOf(__instance);
            if (cabin != null)
            {
                __result = cabin.temperature;
            }
        }
    }
}

using HarmonyLib;
using Verse;

namespace HogShuttle
{
    public class HogShuttleMod : Mod
    {
        public const string HarmonyId = "MagosZ.HogShuttle";

        public HogShuttleMod(ModContentPack content) : base(content)
        {
            new Harmony(HarmonyId).PatchAll(typeof(HogShuttleMod).Assembly);
        }
    }
}

using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: everything aboard (seats and cargo hold) is kept at <see cref="temperature"/>, and
    /// pawns aboard take no vacuum.</summary>
    public class SealedCabinExtension : DefModExtension
    {
        public float temperature = 21f;
    }

    public static class SealedCabin
    {
        /// <summary>The sealed cabin holding <paramref name="thing"/>, if any. Vehicle Framework holds passengers in
        /// seat handlers and cargo in the vehicle's inventory; both chains lead up to the VehiclePawn. A passenger's
        /// own inventory and apparel sit one level further down, behind the passenger.</summary>
        public static SealedCabinExtension HolderOf(Thing thing)
        {
            if (thing.Spawned)
            {
                return null;
            }
            for (IThingHolder holder = thing.ParentHolder; holder != null; holder = holder.ParentHolder)
            {
                if (holder is VehiclePawn vehicle)
                {
                    return vehicle.def.GetModExtension<SealedCabinExtension>();
                }
            }
            return null;
        }
    }
}

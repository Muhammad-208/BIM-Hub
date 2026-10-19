using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using Autodesk.Revit.DB;

namespace BIMHub.Revit
{
    /// <summary>API differences between Revit 2020 and 2027 live here and nowhere else.</summary>
    internal static class Compat
    {
        public const double FeetToMetres = 0.3048;

        /// <summary>ElementId value: IntegerValue (≤2023) vs Value (2024+, long).</summary>
        public static long IdValue(ElementId id)
        {
#if REVIT2024_OR_GREATER
            return id.Value;
#else
            return id.IntegerValue;
#endif
        }

        public static ElementId MakeId(long value)
        {
#if REVIT2024_OR_GREATER
            return new ElementId(value);
#else
            return new ElementId((int)value);
#endif
        }

        /// <summary>Accepts an ElementId number or a UniqueId string.</summary>
        public static Element Resolve(Document doc, string idOrUnique)
        {
            if (string.IsNullOrWhiteSpace(idOrUnique)) return null;
            if (long.TryParse(idOrUnique, NumberStyles.Integer, CultureInfo.InvariantCulture, out long n))
                return doc.GetElement(MakeId(n));
            return doc.GetElement(idOrUnique);
        }

        public static string CategoryName(Element e)
        {
            try { return e?.Category?.Name; } catch { return null; }
        }

        public static string BuiltInCategoryName(Category c)
        {
            if (c == null) return null;
#if REVIT2023_OR_GREATER
            return c.BuiltInCategory.ToString();
#else
            long v = IdValue(c.Id);
            return Enum.IsDefined(typeof(BuiltInCategory), (int)v) ? ((BuiltInCategory)(int)v).ToString() : null;
#endif
        }
    }

    /// <summary>Typed reads from the JSON args dictionary.</summary>
    internal static class Args
    {
        public static string Str(Dictionary<string, object> a, string key, string def = null)
            => a != null && a.TryGetValue(key, out object v) && v != null ? Convert.ToString(v, CultureInfo.InvariantCulture) : def;

        public static int Int(Dictionary<string, object> a, string key, int def)
            => a != null && a.TryGetValue(key, out object v) && v != null ? Convert.ToInt32(v, CultureInfo.InvariantCulture) : def;

        public static bool Bool(Dictionary<string, object> a, string key, bool def)
            => a != null && a.TryGetValue(key, out object v) && v != null ? Convert.ToBoolean(v, CultureInfo.InvariantCulture) : def;

        public static List<string> StrList(Dictionary<string, object> a, string key)
        {
            var list = new List<string>();
            if (a == null || !a.TryGetValue(key, out object v) || v == null) return list;
            if (v is string s) { list.Add(s); return list; }
            if (v is IEnumerable e)
                foreach (var x in e) if (x != null) list.Add(Convert.ToString(x, CultureInfo.InvariantCulture));
            return list;
        }

        public static Dictionary<string, object> Obj(Dictionary<string, object> a, string key)
            => a != null && a.TryGetValue(key, out object v) ? v as Dictionary<string, object> : null;

        public static string Required(Dictionary<string, object> a, string key)
            => Str(a, key) ?? throw new ArgumentException($"'{key}' is required");
    }
}

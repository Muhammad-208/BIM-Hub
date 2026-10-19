using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace BIMHub.Revit
{
    /// <summary>
    /// Every command the BIM Hub `revit` MCP server can call. Runs on the Revit API thread (via Dispatcher).
    /// Names and argument keys must match mcp-layer/src/bimhub/servers/revit.py.
    /// Lengths/elevations are returned in metres (suffix _m) — Revit internal feet are converted here.
    /// </summary>
    internal static class Commands
    {
        public static object Run(UIApplication uiapp, string command, Dictionary<string, object> a)
        {
            UIDocument uidoc = uiapp.ActiveUIDocument;
            if (uidoc == null) throw new InvalidOperationException("No active document in Revit");
            Document doc = uidoc.Document;

            switch (command)
            {
                case "get_model_info": return ModelInfo(uiapp, doc);
                case "list_elements": return ListElements(doc, a);
                case "get_element_parameters": return ElementParameters(doc, a);
                case "list_warnings": return Warnings(doc, a);
                case "audit_model": return Audit(doc);
                case "list_views_and_sheets": return ViewsAndSheets(doc, a);
                case "get_selection": return Selection(uidoc);
                case "show_elements": return ShowElements(uidoc, a);
                case "export_ifc": return ExportIfc(doc, a);
                case "set_parameters": return SetParameters(doc, a);
                case "export_nwc": return ExportNwc(doc, a);
                default: throw new ArgumentException($"Unknown command '{command}'");
            }
        }

        // ───────────────────────── read ─────────────────────────
        private static object ModelInfo(UIApplication uiapp, Document doc)
        {
            var levels = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = Compat.IdValue(l.Id), name = l.Name, elevation_m = Math.Round(l.Elevation * Compat.FeetToMetres, 4) })
                .ToList();
            var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Select(g => g.Name).OrderBy(n => n).ToList();
            var phases = doc.Phases.Cast<Phase>().Select(p => p.Name).ToList();

            var basePoints = new List<object>();
            foreach (BasePoint bp in new FilteredElementCollector(doc).OfClass(typeof(BasePoint)).Cast<BasePoint>())
            {
                basePoints.Add(new
                {
                    kind = bp.IsShared ? "survey_point" : "project_base_point",
                    east_west_m = Feet(bp, BuiltInParameter.BASEPOINT_EASTWEST_PARAM),
                    north_south_m = Feet(bp, BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM),
                    elevation_m = Feet(bp, BuiltInParameter.BASEPOINT_ELEVATION_PARAM),
                    angle_to_true_north_deg = AngleDeg(bp, BuiltInParameter.BASEPOINT_ANGLETON_PARAM),
                });
            }

            int links = new FilteredElementCollector(doc).OfClass(typeof(RevitLinkInstance)).GetElementCount();
            return new
            {
                title = doc.Title,
                file_name = App.DocFileName(doc),
                path = doc.PathName,
                revit_version = uiapp.Application.VersionNumber,
                revit_build = uiapp.Application.VersionBuild,
                is_workshared = doc.IsWorkshared,
                is_family = doc.IsFamilyDocument,
                active_view = doc.ActiveView?.Name,
                project_location = doc.ActiveProjectLocation?.Name,
                levels,
                grids,
                phases,
                base_points = basePoints,
                revit_links = links,
            };
        }

        private static object ListElements(Document doc, Dictionary<string, object> a)
        {
            string category = Args.Required(a, "category");
            int limit = Args.Int(a, "limit", 500);
            var filter = Args.Obj(a, "parameter_filter");

            FilteredElementCollector col = new FilteredElementCollector(doc).WhereElementIsNotElementType();
            if (category.StartsWith("OST_", StringComparison.OrdinalIgnoreCase) &&
                Enum.TryParse(category, true, out BuiltInCategory bic))
            {
                col = col.OfCategory(bic);
            }
            else
            {
                Category cat = doc.Settings.Categories.Cast<Category>()
                    .FirstOrDefault(c => string.Equals(c.Name, category, StringComparison.OrdinalIgnoreCase));
                if (cat == null) throw new ArgumentException($"Category '{category}' not found (use a display name or OST_ name)");
                col = col.OfCategoryId(cat.Id);
            }

            var rows = new List<object>();
            int total = 0;
            foreach (Element e in col)
            {
                if (filter != null && filter.Count > 0 && !Matches(doc, e, filter)) continue;
                total++;
                if (rows.Count >= limit) continue;
                rows.Add(Summary(doc, e));
            }
            return new { category, total, returned = rows.Count, elements = rows };
        }

        private static object ElementParameters(Document doc, Dictionary<string, object> a)
        {
            var ids = Args.StrList(a, "element_ids");
            if (ids.Count == 0) throw new ArgumentException("'element_ids' is required");
            var names = new HashSet<string>(Args.StrList(a, "parameter_names"), StringComparer.OrdinalIgnoreCase);
            var output = new List<object>();
            foreach (string id in ids)
            {
                Element e = Compat.Resolve(doc, id);
                if (e == null) { output.Add(new { id, error = "not found" }); continue; }
                Element type = doc.GetElement(e.GetTypeId());
                output.Add(new
                {
                    id = Compat.IdValue(e.Id),
                    unique_id = e.UniqueId,
                    category = Compat.CategoryName(e),
                    name = e.Name,
                    instance = Params(e, names),
                    type = type == null ? null : Params(type, names),
                });
            }
            return output;
        }

        private static object Warnings(Document doc, Dictionary<string, object> a)
        {
            int limit = Args.Int(a, "limit", 1000);
            IList<FailureMessage> all = doc.GetWarnings();
            var groups = all.GroupBy(w => w.GetDescriptionText())
                .Select(g => new
                {
                    description = g.Key,
                    severity = g.First().GetSeverity().ToString(),
                    count = g.Count(),
                    elements = g.SelectMany(w => w.GetFailingElements()).Select(Compat.IdValue).Distinct().Take(50).ToList(),
                })
                .OrderByDescending(g => g.count)
                .Take(limit)
                .ToList();
            return new { total = all.Count, groups };
        }

        private static object Audit(Document doc)
        {
            // worksets
            List<string> worksets = null;
            if (doc.IsWorkshared)
                worksets = new FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).Select(w => w.Name).ToList();

            // in-place families
            var inPlace = new FilteredElementCollector(doc).OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>()
                .Where(fi => fi.Symbol?.Family?.IsInPlace == true)
                .Select(fi => new { id = Compat.IdValue(fi.Id), family = fi.Symbol.Family.Name, category = Compat.CategoryName(fi) })
                .ToList();

            // CAD: imported (bad) vs linked
            var imports = new FilteredElementCollector(doc).OfClass(typeof(ImportInstance)).Cast<ImportInstance>().ToList();
            var cadImported = imports.Where(i => !i.IsLinked).Select(i => new { id = Compat.IdValue(i.Id), name = i.Name }).ToList();

            // Revit links + path type
            var links = new List<object>();
            foreach (RevitLinkType lt in new FilteredElementCollector(doc).OfClass(typeof(RevitLinkType)).Cast<RevitLinkType>())
            {
                string pathType = null;
                try
                {
                    if (ExternalFileUtils.IsExternalFileReference(doc, lt.Id))
                        pathType = ExternalFileUtils.GetExternalFileReference(doc, lt.Id).PathType.ToString();
                }
                catch { }
                links.Add(new { name = lt.Name, path_type = pathType, loaded = RevitLinkType.IsLoaded(doc, lt.Id) });
            }

            // views / sheets
            var allViews = new FilteredElementCollector(doc).OfClass(typeof(View)).Cast<View>().ToList();
            var templates = allViews.Count(v => v.IsTemplate);
            var sheets = allViews.OfType<ViewSheet>().ToList();
            var placed = new HashSet<long>(new FilteredElementCollector(doc).OfClass(typeof(Viewport)).Cast<Viewport>()
                .Select(vp => Compat.IdValue(vp.ViewId)));
            var placeable = allViews.Where(v => !v.IsTemplate && !(v is ViewSheet) && v.CanBePrinted &&
                                                v.ViewType != ViewType.ProjectBrowser && v.ViewType != ViewType.SystemBrowser &&
                                                v.ViewType != ViewType.Schedule && v.ViewType != ViewType.Internal).ToList();
            int notOnSheets = placeable.Count(v => !placed.Contains(Compat.IdValue(v.Id)));

            int modelGroups = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_IOSModelGroups)
                .WhereElementIsNotElementType().GetElementCount();
            int designOptions = new FilteredElementCollector(doc).OfClass(typeof(DesignOption)).GetElementCount();

            double? sizeMb = null;
            try
            {
                if (!string.IsNullOrEmpty(doc.PathName) && File.Exists(doc.PathName))
                    sizeMb = Math.Round(new FileInfo(doc.PathName).Length / 1048576.0, 1);
            }
            catch { }

            return new
            {
                file_name = App.DocFileName(doc),
                file_size_mb = sizeMb,
                is_workshared = doc.IsWorkshared,
                worksets,
                warnings_total = doc.GetWarnings().Count,
                in_place_families = new { count = inPlace.Count, items = inPlace.Take(100).ToList() },
                cad_imported = new { count = cadImported.Count, items = cadImported.Take(100).ToList() },
                cad_linked = imports.Count(i => i.IsLinked),
                revit_links = links,
                views = new { total = allViews.Count - templates - sheets.Count, templates, not_on_sheets = notOnSheets },
                sheets = sheets.Count,
                model_groups = modelGroups,
                design_options = designOptions,
            };
        }

        private static object ViewsAndSheets(Document doc, Dictionary<string, object> a)
        {
            string kind = (Args.Str(a, "kind", "all") ?? "all").ToLowerInvariant();
            var result = new Dictionary<string, object>();
            var all = new FilteredElementCollector(doc).OfClass(typeof(View)).Cast<View>().ToList();
            if (kind == "all" || kind == "views")
            {
                result["views"] = all.Where(v => !(v is ViewSheet) && v.ViewType != ViewType.ProjectBrowser &&
                                                 v.ViewType != ViewType.SystemBrowser && v.ViewType != ViewType.Internal)
                    .Select(v => new
                    {
                        id = Compat.IdValue(v.Id),
                        name = v.Name,
                        type = v.ViewType.ToString(),
                        is_template = v.IsTemplate,
                        template = v.ViewTemplateId == ElementId.InvalidElementId ? null : doc.GetElement(v.ViewTemplateId)?.Name,
                    }).ToList();
            }
            if (kind == "all" || kind == "sheets")
            {
                result["sheets"] = all.OfType<ViewSheet>().Select(s => new
                {
                    id = Compat.IdValue(s.Id),
                    number = s.SheetNumber,
                    name = s.Name,
                    is_placeholder = s.IsPlaceholder,
                    views = s.GetAllPlacedViews().Count,
                }).OrderBy(s => s.number).ToList();
            }
            return result;
        }

        private static object Selection(UIDocument uidoc)
        {
            Document doc = uidoc.Document;
            return uidoc.Selection.GetElementIds().Select(id => doc.GetElement(id)).Where(e => e != null)
                .Select(e => Summary(doc, e)).ToList();
        }

        // ───────────────────────── view-only ─────────────────────────
        private static object ShowElements(UIDocument uidoc, Dictionary<string, object> a)
        {
            Document doc = uidoc.Document;
            var ids = Args.StrList(a, "element_ids").Select(s => Compat.Resolve(doc, s)).Where(e => e != null)
                .Select(e => e.Id).ToList();
            if (ids.Count == 0) throw new ArgumentException("No valid elements in 'element_ids'");
            uidoc.Selection.SetElementIds(ids);
            uidoc.ShowElements(ids);
            bool isolated = false;
            if (Args.Bool(a, "isolate", false) && doc.ActiveView != null)
            {
                using (var t = new Transaction(doc, "BIM Hub · temporary isolate"))
                {
                    t.Start();
                    doc.ActiveView.IsolateElementsTemporary(ids);
                    t.Commit();
                    isolated = true;
                }
            }
            return new { shown = ids.Count, isolated, view = doc.ActiveView?.Name };
        }

        // ───────────────────────── export ─────────────────────────
        private static object ExportIfc(Document doc, Dictionary<string, object> a)
        {
            string folder = Args.Required(a, "output_folder");
            string fileName = Args.Str(a, "file_name") ?? Path.GetFileNameWithoutExtension(App.DocFileName(doc)) + "-IFC";
            if (fileName.EndsWith(".ifc", StringComparison.OrdinalIgnoreCase)) fileName = fileName.Substring(0, fileName.Length - 4);
            Directory.CreateDirectory(folder);

            var options = new IFCExportOptions();
            string ver = Args.Str(a, "ifc_version");
            if (!string.IsNullOrEmpty(ver))
            {
                if (!Enum.TryParse(ver, true, out IFCVersion v))
                    throw new ArgumentException($"Unknown ifc_version '{ver}'. Options: {string.Join(", ", Enum.GetNames(typeof(IFCVersion)))}");
                options.FileVersion = v;
            }
            string viewId = Args.Str(a, "view_id");
            if (!string.IsNullOrEmpty(viewId)) options.FilterViewId = Compat.Resolve(doc, viewId)?.Id ?? ElementId.InvalidElementId;

            bool ok;
            // IFC export needs an open transaction in many versions; roll it back so the model is untouched.
            using (var t = new Transaction(doc, "BIM Hub · IFC export"))
            {
                t.Start();
                ok = doc.Export(folder, fileName, options);
                t.RollBack();
            }
            string full = Path.Combine(folder, fileName + ".ifc");
            return new { ok, file = full, exists = File.Exists(full), ifc_version = options.FileVersion.ToString() };
        }

        /// <summary>
        /// NWC for coordination, written to the folder agreed in the project (the MCP layer resolves it).
        /// Shared coordinates, element properties converted, links excluded (each discipline exports its own model).
        /// </summary>
        private static object ExportNwc(Document doc, Dictionary<string, object> a)
        {
            if (!OptionalFunctionalityUtils.IsNavisworksExporterAvailable())
                throw new InvalidOperationException("Navisworks NWC exporter for Revit is not installed on this PC " +
                                                    "(install 'Navisworks Exporters' for this Revit version).");
            string folder = Args.Required(a, "output_folder");
            string fileName = Args.Str(a, "file_name") ?? Path.GetFileNameWithoutExtension(App.DocFileName(doc));
            if (fileName.EndsWith(".nwc", StringComparison.OrdinalIgnoreCase)) fileName = fileName.Substring(0, fileName.Length - 4);
            Directory.CreateDirectory(folder);

            var opt = new NavisworksExportOptions
            {
                ExportLinks = false,
                Coordinates = NavisworksCoordinates.Shared,
                ConvertElementProperties = true,
                ExportRoomGeometry = false,
                ExportScope = NavisworksExportScope.Model,
            };
            string viewName = Args.Str(a, "view_name");
            if (!string.IsNullOrEmpty(viewName))
            {
                View3D v = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>()
                    .FirstOrDefault(x => !x.IsTemplate && string.Equals(x.Name, viewName, StringComparison.OrdinalIgnoreCase));
                if (v == null) throw new ArgumentException($"3D view '{viewName}' not found");
                opt.ExportScope = NavisworksExportScope.View;
                opt.ViewId = v.Id;
            }
            doc.Export(folder, fileName, opt);
            string full = Path.Combine(folder, fileName + ".nwc");
            return new
            {
                file = full,
                exists = File.Exists(full),
                size_mb = File.Exists(full) ? Math.Round(new FileInfo(full).Length / 1048576.0, 1) : (double?)null,
                scope = opt.ExportScope.ToString(),
                coordinates = "Shared",
            };
        }

        // ───────────────────────── write ─────────────────────────
        /// <summary>
        /// All-or-nothing: if any value fails, the whole transaction is rolled back and every error is reported.
        /// Strings for Double parameters go through SetValueString (display units, e.g. "2400 mm");
        /// numbers for Double parameters are Revit internal units (feet, radians…).
        /// Only INSTANCE parameters are written — editing a type would silently change every instance.
        /// </summary>
        private static object SetParameters(Document doc, Dictionary<string, object> a)
        {
            var ids = Args.StrList(a, "element_ids");
            var values = Args.Obj(a, "values");
            if (ids.Count == 0 || values == null || values.Count == 0)
                throw new ArgumentException("'element_ids' and 'values' are required");
            string tname = Args.Str(a, "transaction") ?? "BIM Hub · set parameters";
            if (tname.Length > 120) tname = tname.Substring(0, 120);

            var errors = new List<object>();
            var changed = new List<object>();
            using (var t = new Transaction(doc, tname))
            {
                t.Start();
                foreach (string sid in ids)
                {
                    Element e = Compat.Resolve(doc, sid);
                    if (e == null) { errors.Add(new { id = sid, error = "element not found" }); continue; }
                    foreach (var kv in values)
                    {
                        Parameter p = e.LookupParameter(kv.Key);
                        if (p == null) { errors.Add(new { id = sid, parameter = kv.Key, error = "instance parameter not found" }); continue; }
                        if (p.IsReadOnly) { errors.Add(new { id = sid, parameter = kv.Key, error = "read-only" }); continue; }
                        string before = ParamValue(p);
                        string err = Assign(p, kv.Value);
                        if (err != null) errors.Add(new { id = sid, parameter = kv.Key, error = err });
                        else changed.Add(new { id = Compat.IdValue(e.Id), parameter = kv.Key, before, after = ParamValue(p) });
                    }
                }
                if (errors.Count > 0) { t.RollBack(); return new { committed = false, errors, attempted = changed.Count }; }
                t.Commit();
            }
            return new { committed = true, transaction = tname, changed };
        }

        private static string Assign(Parameter p, object v)
        {
            try
            {
                switch (p.StorageType)
                {
                    case StorageType.String:
                        return p.Set(v == null ? "" : Convert.ToString(v, CultureInfo.InvariantCulture)) ? null : "Set returned false";
                    case StorageType.Integer:
                        if (v is string si && !int.TryParse(si, out _))
                            return p.SetValueString(si) ? null : "SetValueString returned false";
                        return p.Set(Convert.ToInt32(v, CultureInfo.InvariantCulture)) ? null : "Set returned false";
                    case StorageType.Double:
                        if (v is string sd) return p.SetValueString(sd) ? null : $"could not parse '{sd}' in display units";
                        return p.Set(Convert.ToDouble(v, CultureInfo.InvariantCulture)) ? null : "Set returned false";
                    case StorageType.ElementId:
                        return p.Set(Compat.MakeId(Convert.ToInt64(v, CultureInfo.InvariantCulture))) ? null : "Set returned false";
                    default:
                        return "unsupported storage type";
                }
            }
            catch (Exception ex) { return ex.Message; }
        }

        // ───────────────────────── helpers ─────────────────────────
        private static object Summary(Document doc, Element e)
        {
            string level = null;
            try
            {
                if (e.LevelId != null && e.LevelId != ElementId.InvalidElementId) level = doc.GetElement(e.LevelId)?.Name;
                else level = e.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)?.AsValueString()
                             ?? e.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)?.AsValueString();
            }
            catch { }
            Element type = null;
            try { type = doc.GetElement(e.GetTypeId()); } catch { }
            return new
            {
                id = Compat.IdValue(e.Id),
                unique_id = e.UniqueId,
                category = Compat.CategoryName(e),
                name = e.Name,
                type = type?.Name,
                family = (type as ElementType)?.FamilyName,
                level,
            };
        }

        private static bool Matches(Document doc, Element e, Dictionary<string, object> filter)
        {
            Element type = null;
            foreach (var kv in filter)
            {
                Parameter p = e.LookupParameter(kv.Key);
                if (p == null)
                {
                    type = type ?? doc.GetElement(e.GetTypeId());
                    p = type?.LookupParameter(kv.Key);
                }
                if (p == null) return false;
                string want = Convert.ToString(kv.Value, CultureInfo.InvariantCulture) ?? "";
                string have = ParamValue(p) ?? "";
                if (!string.Equals(have, want, StringComparison.OrdinalIgnoreCase)) return false;
            }
            return true;
        }

        private static List<object> Params(Element e, HashSet<string> only)
        {
            var list = new List<KeyValuePair<string, object>>();
            foreach (Parameter p in e.Parameters)
            {
                string name = p.Definition?.Name;
                if (name == null) continue;
                if (only.Count > 0 && !only.Contains(name)) continue;
                list.Add(new KeyValuePair<string, object>(name, new
                {
                    name,
                    value = ParamValue(p),
                    raw = Raw(p),
                    storage = p.StorageType.ToString(),
                    read_only = p.IsReadOnly,
                    shared = p.IsShared,
                    has_value = p.HasValue,
                }));
            }
            return list.OrderBy(x => x.Key, StringComparer.OrdinalIgnoreCase).Select(x => x.Value).ToList();
        }

        internal static string ParamValue(Parameter p)
        {
            try
            {
                if (p.StorageType == StorageType.String) return p.AsString();
                return p.AsValueString() ?? Raw(p)?.ToString();
            }
            catch { return null; }
        }

        private static object Raw(Parameter p)
        {
            try
            {
                switch (p.StorageType)
                {
                    case StorageType.Double: return p.AsDouble();
                    case StorageType.Integer: return p.AsInteger();
                    case StorageType.ElementId: return Compat.IdValue(p.AsElementId());
                    case StorageType.String: return p.AsString();
                    default: return null;
                }
            }
            catch { return null; }
        }

        private static double? Feet(Element e, BuiltInParameter bip)
        {
            Parameter p = e.get_Parameter(bip);
            return p == null ? (double?)null : Math.Round(p.AsDouble() * Compat.FeetToMetres, 4);
        }

        private static double? AngleDeg(Element e, BuiltInParameter bip)
        {
            Parameter p = e.get_Parameter(bip);
            return p == null ? (double?)null : Math.Round(p.AsDouble() * 180.0 / Math.PI, 6);
        }
    }
}

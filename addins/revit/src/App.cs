using System;
using System.IO;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;

namespace BIMHub.Revit
{
    /// <summary>
    /// Entry point. Starts an HTTP listener on http://localhost:8766/ (env BIMHUB_REVIT_PORT to change)
    /// and runs every request on Revit's API thread through an ExternalEvent.
    ///   GET  /health                        → { ok, app, version, document, port }
    ///   POST /command {command, args}       → { ok: true, result } | { ok: false, error }
    /// Contract: mcp-layer/BRIDGE_PROTOCOL.md in the BIM Hub.
    /// </summary>
    public class App : IExternalApplication
    {
        public const string AddinVersion = "1.0.0";
        internal static int Port = 8766;
        internal static string VersionNumber = "";
        internal static volatile string ActiveDocument = "";
        internal static volatile string LastRequest = "";
        internal static readonly string LogPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "BIMHub", "revit-bridge.log");

        private HttpBridge _http;

        public Result OnStartup(UIControlledApplication app)
        {
            try
            {
                VersionNumber = app.ControlledApplication.VersionNumber;
                if (int.TryParse(Environment.GetEnvironmentVariable("BIMHUB_REVIT_PORT"), out int p)) Port = p;

                Dispatcher.Initialize();                       // ExternalEvent must be created in API context
                app.ViewActivated += OnViewActivated;
                app.ControlledApplication.DocumentClosed += (s, e) => ActiveDocument = "";

                _http = new HttpBridge(Port);
                _http.Start();
                CreateRibbon(app);
                Log($"BIM Hub bridge {AddinVersion} started on port {Port} (Revit {VersionNumber})");
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log("Startup failed: " + ex);
                return Result.Failed;
            }
        }

        public Result OnShutdown(UIControlledApplication app)
        {
            try { _http?.Stop(); } catch { }
            return Result.Succeeded;
        }

        private static void OnViewActivated(object sender, ViewActivatedEventArgs e)
        {
            ActiveDocument = DocFileName(e.Document);
        }

        internal static string DocFileName(Document doc)
        {
            if (doc == null) return "";
            if (!string.IsNullOrEmpty(doc.PathName))
            {
                try { return Path.GetFileName(doc.PathName); } catch { }
            }
            return doc.Title ?? "";
        }

        private static void CreateRibbon(UIControlledApplication app)
        {
            try
            {
                RibbonPanel panel = app.CreateRibbonPanel("BIM Hub");
                var data = new PushButtonData("BIMHubStatus", "Bridge\nStatus",
                    typeof(App).Assembly.Location, typeof(StatusCommand).FullName)
                {
                    ToolTip = "BIM Hub MCP bridge: port, active document and last request."
                };
                panel.AddItem(data);
            }
            catch (Exception ex) { Log("Ribbon: " + ex.Message); }
        }

        internal static void Log(string msg)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(LogPath));
                File.AppendAllText(LogPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {msg}{Environment.NewLine}");
            }
            catch { /* logging must never break Revit */ }
        }
    }

    [Transaction(TransactionMode.ReadOnly)]
    public class StatusCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData data, ref string message, ElementSet elements)
        {
            TaskDialog.Show("BIM Hub Bridge",
                $"Listening on http://localhost:{App.Port}/\n" +
                $"Revit {App.VersionNumber} · add-in {App.AddinVersion}\n" +
                $"Active document: {App.DocFileName(data.Application.ActiveUIDocument?.Document)}\n" +
                $"Last request: {App.LastRequest}\n\nLog: {App.LogPath}");
            return Result.Succeeded;
        }
    }
}

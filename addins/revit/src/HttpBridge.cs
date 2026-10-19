using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;

namespace BIMHub.Revit
{
    /// <summary>Localhost-only HTTP endpoint (BRIDGE_PROTOCOL.md). Never touches the Revit API directly.</summary>
    internal sealed class HttpBridge
    {
        private readonly int _port;
        private HttpListener _listener;
        private Thread _thread;
        private static readonly TimeSpan CommandTimeout = TimeSpan.FromSeconds(
            int.TryParse(Environment.GetEnvironmentVariable("BIMHUB_REVIT_TIMEOUT_S"), out int t) ? t : 120);

        public HttpBridge(int port) { _port = port; }

        public void Start()
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add($"http://localhost:{_port}/");
            _listener.Start();
            _thread = new Thread(Loop) { IsBackground = true, Name = "BIMHub-HttpBridge" };
            _thread.Start();
        }

        public void Stop()
        {
            try { _listener?.Stop(); _listener?.Close(); } catch { }
        }

        private void Loop()
        {
            while (_listener != null && _listener.IsListening)
            {
                HttpListenerContext ctx;
                try { ctx = _listener.GetContext(); }
                catch (HttpListenerException) { break; }
                catch (ObjectDisposedException) { break; }
                // one worker per request; the Dispatcher serialises the actual Revit work
                ThreadPool.QueueUserWorkItem(_ => Handle(ctx));
            }
        }

        private static void Handle(HttpListenerContext ctx)
        {
            string path = (ctx.Request.Url?.AbsolutePath ?? "/").TrimEnd('/').ToLowerInvariant();
            try
            {
                if (path == "/health" || path == "")
                {
                    Respond(ctx, 200, new Dictionary<string, object>
                    {
                        ["ok"] = true,
                        ["app"] = "Revit",
                        ["version"] = App.VersionNumber,
                        ["addin_version"] = App.AddinVersion,
                        ["document"] = App.ActiveDocument,
                        ["port"] = App.Port,
                    });
                    return;
                }
                if (path != "/command" || ctx.Request.HttpMethod != "POST")
                {
                    Respond(ctx, 404, new { ok = false, error = $"unknown route {ctx.Request.HttpMethod} {path}" });
                    return;
                }

                string text;
                using (var sr = new StreamReader(ctx.Request.InputStream, ctx.Request.ContentEncoding ?? Encoding.UTF8))
                    text = sr.ReadToEnd();
                Dictionary<string, object> body = string.IsNullOrWhiteSpace(text)
                    ? new Dictionary<string, object>() : Json.ParseObject(text);
                string command = Args.Required(body, "command");
                var args = Args.Obj(body, "args") ?? new Dictionary<string, object>();

                App.LastRequest = $"{DateTime.Now:HH:mm:ss} {command}";
                App.Log("→ " + command);
                object result = Dispatcher.Run(command, args, CommandTimeout);
                Respond(ctx, 200, new Dictionary<string, object> { ["ok"] = true, ["result"] = result });
            }
            catch (Exception ex)
            {
                Exception root = ex.InnerException ?? ex;
                App.Log($"✗ {path}: {root.GetType().Name}: {root.Message}");
                try
                {
                    Respond(ctx, 200, new Dictionary<string, object>
                    {
                        ["ok"] = false,
                        ["error"] = $"{root.GetType().Name}: {root.Message}",
                    });
                }
                catch { /* client gone */ }
            }
        }

        private static void Respond(HttpListenerContext ctx, int status, object payload)
        {
            byte[] data = Encoding.UTF8.GetBytes(Json.Serialize(payload));
            ctx.Response.StatusCode = status;
            ctx.Response.ContentType = "application/json; charset=utf-8";
            ctx.Response.ContentLength64 = data.Length;
            using (Stream o = ctx.Response.OutputStream) o.Write(data, 0, data.Length);
        }
    }
}

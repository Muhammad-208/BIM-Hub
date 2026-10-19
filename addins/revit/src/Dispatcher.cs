using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using Autodesk.Revit.UI;

namespace BIMHub.Revit
{
    /// <summary>
    /// Moves work from the HTTP thread onto Revit's API thread.
    /// The HTTP thread enqueues a job, raises the ExternalEvent and waits; Revit runs every queued job
    /// when it is idle. If Revit is busy (modal dialog, long command) the caller gets a timeout error.
    /// </summary>
    internal static class Dispatcher
    {
        private sealed class Job
        {
            public string Command;
            public Dictionary<string, object> Args;
            public object Result;
            public Exception Error;
            public readonly ManualResetEventSlim Done = new ManualResetEventSlim(false);
        }

        private sealed class Handler : IExternalEventHandler
        {
            public void Execute(UIApplication uiapp)
            {
                while (Queue.TryDequeue(out Job job))
                {
                    try { job.Result = Commands.Run(uiapp, job.Command, job.Args); }
                    catch (Exception ex) { job.Error = ex; }
                    finally { job.Done.Set(); }
                }
            }

            public string GetName() => "BIM Hub bridge";
        }

        private static readonly ConcurrentQueue<Job> Queue = new ConcurrentQueue<Job>();
        private static ExternalEvent _event;

        public static void Initialize()
        {
            _event = ExternalEvent.Create(new Handler());
        }

        public static object Run(string command, Dictionary<string, object> args, TimeSpan timeout)
        {
            if (_event == null) throw new InvalidOperationException("Bridge not initialized");
            var job = new Job { Command = command, Args = args ?? new Dictionary<string, object>() };
            Queue.Enqueue(job);
            ExternalEventRequest r = _event.Raise();
            if (r == ExternalEventRequest.Denied || r == ExternalEventRequest.TimedOut)
                App.Log($"ExternalEvent.Raise returned {r}; job stays queued");
            if (!job.Done.Wait(timeout))
                throw new TimeoutException(
                    $"Revit did not process '{command}' within {timeout.TotalSeconds:0}s. " +
                    "Close any open dialog / finish the running command in Revit, then retry.");
            if (job.Error != null) throw job.Error;
            return job.Result;
        }
    }
}

# BIM Hub bridge protocol (desktop add-in side)

Any add-in (C# for Revit / Navisworks / Civil 3D, Python for Dynamo, …) that serves these two endpoints on localhost works with the `bimhub` MCP servers.

| Endpoint | Request | Response |
|---|---|---|
| `GET /health` | — | `{"ok": true, "app": "Revit", "version": "2027", "document": "<active file name>"}` |
| `POST /command` | `{"command": "list_elements", "args": {...}}` | `{"ok": true, "result": <any JSON>}` or `{"ok": false, "error": "message for the agent"}` |

Default ports: Navisworks **8765** (your existing add-in), Revit **8766**, Civil 3D **8767** — change in `config/servers.yaml`.

Requirements
- **API thread**: Revit/Navisworks API calls must run on the main thread — queue requests to an ExternalEvent (Revit) / Idle handler (Navisworks), and answer the HTTP request when done.
- **Transactions**: one write command = one named transaction. Use the `transaction` arg as its name.
- **`document` in /health must be the real file name** — the MCP layer derives the model's discipline from the ISO 19650 role field to enforce write scopes.
- **Element ids**: accept both ElementId (int as string) and UniqueId; return both.
- Bind to localhost only. With .NET `HttpListener` use the prefix `http://localhost:<port>/` (no admin rights needed) and keep `localhost` (not 127.0.0.1) in `servers.yaml`.
- Reference implementation: `addins/revit` (C#, Revit 2020–2027).

Already-built add-in with different routes? Don't change it — map routes in `config/bridges/<app>.yaml`:
```yaml
run_clash_test:    {method: POST, path: "/api/clash/run"}
get_clash_results: {method: GET,  path: "/api/clash/results"}
```

Commands used by the servers: see the `app.call("<command>", …)` lines in `src/bimhub/servers/*.py`.

// BIM Hub Studio desktop shell: starts the Python backend (sidecar) on 127.0.0.1:8800,
// shows the React UI, and stops the backend when the app exits.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct Backend(Mutex<Option<CommandChild>>);

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let cmd = app
                .shell()
                .sidecar("bimhub-studio")
                .expect("sidecar bimhub-studio missing from the bundle")
                .args(["--port", "8800"]);
            let (_events, child) = cmd.spawn().expect("could not start the BIM Hub backend");
            app.manage(Backend(Mutex::new(Some(child))));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building BIM Hub Studio");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            if let Some(state) = handle.try_state::<Backend>() {
                if let Some(child) = state.0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        }
    });
}

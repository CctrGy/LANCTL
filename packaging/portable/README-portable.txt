LANCTL GUI EXPERIMENTAL - NOT STABLE - 0.3.4-alpha.1
=================================================

Run LANCTL.exe, lanip.exe, lanwire.exe, lanrack.exe, lanaccess.exe or lanmon.exe
from this directory. LANMON provides direct monitoring commands. All tools store
mutable data in data/lanctl beside the executables. Each active project owns its
physical inventory in its workspace's physical/idf.db, included in the VLF.
The historical physical database remains
separate until explicitly imported with project import-physical. LANIP keeps its
logical and monitoring databases separate. The portable package does not modify PATH, ProgramData, the
registry, services, firewall rules, or SSH/HTTPS settings merely by opening a launcher. Preserve data/lanctl
when replacing the executable during an update.

To open the graphical center without creating a console, open lanctl-window.exe.
For a GUI shortcut to another launcher, use lanctl-window.exe lanwire (or lanip,
lanrack, lanaccess, lanmon). Keep the working directory set to this portable folder.
From an existing terminal, LANCTL.exe --gui remains supported.
You can also run lanip.exe, lanwire.exe, lanrack.exe, lanaccess.exe or lanmon.exe
with --gui. Windows x64 and Microsoft WebView2 Runtime are required.
Without arguments LANCTL uses the saved startup preference (CLI by default).
This is a testing prototype. Use copies of projects and preserve data/lanctl.

Optional Clink completion: run .\prepare.ps1 from a normal-user PowerShell,
or LANCTL.exe completions install. This registers only this directory's clink
folder for the current user, if Clink is detected. Re-running is safe.
Before moving/removing the portable directory, run .\prepare.ps1 -RemoveClink
or LANCTL.exe completions uninstall. Other script folders are not removed.
If Clink is installed only through a custom per-user path, use a normal CMD
with Clink and clink installscripts / clink uninstallscripts for that folder.

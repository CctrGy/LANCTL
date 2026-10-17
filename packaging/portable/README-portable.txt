LANCTL GUI EXPERIMENTAL - NOT STABLE - 0.3.4-alpha.1
=================================================

Run LANCTL.exe, lanip.exe, lanwire.exe, lanrack.exe, lanaccess.exe or lanmon.exe
from this directory. LANMON provides direct monitoring commands. All tools store
mutable data in data/lanctl beside the executables. LANWIRE owns physical/idf.db while LANIP
keeps its logical and monitoring databases separate. The portable package does not modify PATH, ProgramData, the
registry, services, firewall rules, or SSH/HTTPS settings. Preserve data/lanctl
when replacing the executable during an update.

To open the experimental graphical center, run LANCTL.exe --gui.
You can also run lanip.exe, lanwire.exe, lanrack.exe, lanaccess.exe or lanmon.exe
with --gui. Windows x64 and Microsoft WebView2 Runtime are required.
Without arguments the saved startup preference is used (TUI by default).
This is a testing prototype. Use copies of projects and preserve data/lanctl.

LANCTL portable
===============

Run LANCTL.exe, lanip.exe, lanwire.exe, lanrack.exe, lanaccess.exe, lanmon.exe
or landemo.exe from this
directory. LANMON provides direct monitoring commands; LANDEMO creates the
reproducible presentation walkthrough. All tools store
mutable data in data/lanctl beside the executables. LANWIRE owns physical/idf.db while LANIP
keeps its logical and monitoring databases separate. The portable package does not modify PATH, ProgramData, the
registry, services, firewall rules, or SSH/HTTPS settings. Preserve data/lanctl
when replacing the executable during an update.

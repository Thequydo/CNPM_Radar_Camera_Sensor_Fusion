Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\CNPM_Project"
WshShell.Run "python C:\CNPM_Project\main.py", 0, False

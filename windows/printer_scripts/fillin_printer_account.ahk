SetTitleMatchMode, 2

WinTitle := "SHARP MX-M465N PCL6 Printing Preferences"

WinWait, %WinTitle%


Control, Check,, Button30, %WinTitle%
ControlSetText, Edit2, %1%, %WinTitle%
ControlSetText, Edit3, %2%, %WinTitle%
Control, Check,, Button40, %WinTitle%

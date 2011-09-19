C:\Python27\python.exe setup.py py2exe

rmdir /S /Q dist\tcl\tcl8.5\tzdata dist\tcl\tk8.5\demos dist\tcl\tk8.5\images dist\tcl\tcl8.5\encoding
del   /S /Q dist\w9xpopen.exe

upx dist\*.exe dist\*.dll

pause
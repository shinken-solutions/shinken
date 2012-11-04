option explicit
Dim args: args = WScript.Arguments.Count

If args < 1 then
  WScript.Echo "usage: cscript.exe dounzip.vbs zipfile"
  WScript.Quit
end If

Dim objArgs: Set objArgs = WScript.Arguments

Dim zipfolder: zipfolder = objArgs(0)
Dim zipfoldername: zipfoldername = zipfolder & ".zip"
Dim oFSO: Set oFSO = CreateObject("Scripting.FileSystemObject")
If Not oFSO.FolderExists(zipfolder) Then oFSO.CreateFolder zipfolder
wscript.echo "Zipfoldername = "& zipfoldername
wscript.echo "foldername = " & zipfolder
dounzip zipfoldername, zipfolder

Sub doUnzip(sZipFolder, sDest)
   Dim oShell
   Dim oZF        ' this must be Variant
   Dim oD         ' this must be Variant
   oZF = sZipFolder
   oD = sDest
   Set oShell = CreateObject("Shell.Application")
   'Extract the files from the zip into the folder
   oShell.NameSpace(oD).CopyHere oShell.NameSpace(oZF).Items
End Sub
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
zipfoldername = oFSO.GetAbsolutePathName(zipfoldername)
wscript.echo "Zipfoldername = "& zipfoldername
zipfolder = oFSO.GetAbsolutePathName(zipfolder)
wscript.echo "foldername = " & zipfolder
dounzip zipfoldername, zipfolder

Sub doUnzip(sZipFolder, sDest)
   Dim oShell, objSource, objTarget, objItems
   Dim oZF        ' this must be Variant
   Dim oD         ' this must be Variant
   oZF = sZipFolder
   oD = sDest
   Set oShell = CreateObject("Shell.Application")
   'Extract the files from the zip into the folder
   Set objTarget = oShell.NameSpace(oD)
   set objSource = oShell.NameSpace(oZF)
   Set objItems = objSource.Items()
   objTarget.CopyHere objItems, 256
End Sub
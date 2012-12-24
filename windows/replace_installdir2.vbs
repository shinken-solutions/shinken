' installation of shinken Arbiter Service using installutil....
' (c) 2012 October, By VEOSOFT, Jean-françois BUTKIEWICZ
' This script is for IT admins only. If you do not have experience or
' knowledge fundation to install manually shinken on a windows host, please use the 
' integrated installation of Shinken using the setup.exe program delivered by
' VEOSOFT. This kind of installation perform the same tasks but without any request
' using command line.
' This script is delivered upon Alfresco GPL licence.
Const ForReading = 1, ForWriting = 2
 
Dim shell, args, fso
Set shell = WScript.CreateObject("WScript.Shell")
Set fso   = WScript.CreateObject("Scripting.FileSystemObject")
Set args  = Wscript.Arguments

if args.count <> 3 then 
	wscript.echo "Arguments number not equal to 3 :"
	wscript.echo "replace-installdir must be used with 3 args"
	wscript.echo "File to be checked"
	wscript.echo "string to be found"
	wscript.echo "new string"
	wscript.quit 1
end if

Dim filetocheck: filetocheck = args(0)
Dim stringtofind: stringtofind = args(1)
Dim newstring: newstring = args(2)
' First of all, change the long name to the short name of the file to not be worried by spaces
' in the newstring - set to %CD% in the shinken installation....
newstring = GetShortPath(newstring)
newstring = Replace(newstring, "\", "\\")

If (fso.FileExists(filetocheck)) Then
	Dim fileloaded: fileloaded = ReadAllTextFile(filetocheck)
	' process loop - to change all the string found
	Dim Tempstring: TempString = fileloaded
	do
		fileloaded = ReplaceString(stringtofind,fileloaded,newstring)
		if TempString <> fileloaded then
			TempString = fileloaded
		else 
			Exit do
		end if
	loop while TempString = fileloaded
	WriteTextFile filetocheck, fileloaded 
else
	Wscript.echo "The file " & filetocheck & " is not found ! Please check the filesystem."
	wscript.quit 1
end if

Function GetShortPath(fullpath)
	' explore the fullpath to each directory...
	Dim returnvalue: returnvalue = ""
	Dim tempfolder, tempfolderpath
	tempfolderpath = ""
	
	on error resume next
	Err.clear
	Dim slashpos: slashpos = instr(fullpath,"\")
	do while slashpos <> 0
		if tempfolderpath <> "" then
			tempfolderpath = tempfolder & "\" & mid(fullpath,1,slashpos-1)
		else
			tempfolderpath = tempfolder & mid(fullpath,1,slashpos-1)
		end if
		fullpath = mid(fullpath,slashpos+1)
		if (len(tempfolderpath) = 2) and (instr(tempfolderpath,":") > 0) then
			returnvalue = tempfolderpath
		else
			set tempfolder = fso.GetFolder(tempfolderpath)
			if err.Number <> 0 then
				wscript.echo "Error raised on getfolder to reach the short name of the path"
				Wscript.quit 9
			end if
			if returnvalue <> "" then
				returnvalue = returnvalue & "\" & tempfolder.ShortName
			else
				returnvalue = returnvalue & tempfolder.ShortName
			end if
		end if
		slashpos = instr(fullpath,"\")
	loop
	' last bloc of path
	if tempfolderpath <> "" then
		tempfolderpath = tempfolderpath & "\" & fullpath
	else
		tempfolderpath = fullpath
	end if
	set tempfolder = fso.GetFolder(tempfolderpath)
	if err.Number <> 0 then
		wscript.echo "Error raised on getfolder to reach the short name of the path"
		Wscript.quit 9
	end if
	if returnvalue <> "" then
		returnvalue = returnvalue & "\" & tempfolder.ShortName
	else
		returnvalue = returnvalue & tempfolder.ShortName
	end if
	GetShortPath = returnvalue
	
End Function

Function ReadAllTextFile (filename)
   Dim f: Set f = fso.OpenTextFile(filename, ForReading)
   ReadAllTextFile = f.ReadAll
   f.Close
End Function

Function WriteTextFile (filename, content)
   Dim f: Set f = fso.OpenTextFile(filename, ForWriting)
   f.Write content
   f.Close
End Function

Function ReplaceString(patrn, originStr, replStr)
  Dim regEx: Set regEx = New RegExp 
  regEx.Pattern = patrn 
  regEx.IgnoreCase = True 
  ReplaceString = regEx.Replace(originStr, replStr) 
End Function

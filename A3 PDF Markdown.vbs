Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "Virtual environment was not found. Run setup first: uv sync --python 3.11.15", 48, "A3 PDF Markdown"
    WScript.Quit 1
End If

shell.CurrentDirectory = root
shell.Run """" & pythonw & """ -m a3_pdf_markdown.app.main", 0, False


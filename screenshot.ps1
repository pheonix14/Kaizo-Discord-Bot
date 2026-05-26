Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$Width = [System.Windows.Forms.SystemInformation]::VirtualScreen.Width
$Height = [System.Windows.Forms.SystemInformation]::VirtualScreen.Height
$Left = [System.Windows.Forms.SystemInformation]::VirtualScreen.Left
$Top = [System.Windows.Forms.SystemInformation]::VirtualScreen.Top
$Bitmap = New-Object System.Drawing.Bitmap $Width, $Height
$Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
$Graphics.CopyFromScreen($Left, $Top, 0, 0, $Bitmap.Size)
$Bitmap.Save("c:\Users\acer\Desktop\xtreme\screenshot.png", [System.Drawing.Imaging.ImageFormat]::Png)
$Graphics.Dispose()
$Bitmap.Dispose()

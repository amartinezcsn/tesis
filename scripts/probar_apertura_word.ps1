param([Parameter(Mandatory = $true)][string]$Folder)
$ErrorActionPreference = 'Continue'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    Get-ChildItem -LiteralPath $Folder -Filter '*.docx' | Sort-Object Name | ForEach-Object {
        try {
            $d = $word.Documents.Open($_.FullName, $false, $true)
            Write-Output ("OK " + $_.Name + " pages=" + $d.ComputeStatistics(2))
            $d.Close(0)
        }
        catch {
            Write-Output ("FAIL " + $_.Name + " :: " + $_.Exception.Message)
        }
    }
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

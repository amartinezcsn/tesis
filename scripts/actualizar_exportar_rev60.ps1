param(
    [Parameter(Mandatory = $true)][string]$DocxPath,
    [Parameter(Mandatory = $true)][string]$PdfPath
)

$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null

try {
    $document = $word.Documents.Open($DocxPath, $false, $false)
    foreach ($toc in $document.TablesOfContents) {
        [void]$toc.Update()
    }
    foreach ($tof in $document.TablesOfFigures) {
        [void]$tof.Update()
    }
    $document.Repaginate()
    [void]$document.Fields.Update()
    $document.Repaginate()
    [void]$document.Fields.Update()
    $document.Save()
    $document.ExportAsFixedFormat($PdfPath, 17, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('Fields: ' + $document.Fields.Count)
    Write-Output ('TOCs: ' + $document.TablesOfContents.Count)
    Write-Output ('FiguresLists: ' + $document.TablesOfFigures.Count)
}
finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

param([string]$DocxPath,[string]$PdfPath)
$ErrorActionPreference='Stop'
$wordExport=New-Object -ComObject Word.Application
$wordExport.Visible=$false
$wordExport.DisplayAlerts=0
try {
    $documentExport=$wordExport.Documents.Open($DocxPath,$false,$false,$false)
    $documentExport.Repaginate()
    foreach($tocExport in $documentExport.TablesOfContents){$tocExport.Update()}
    foreach($tofExport in $documentExport.TablesOfFigures){$tofExport.Update()}
    $documentExport.Repaginate()
    $documentExport.Save()
    $documentExport.ExportAsFixedFormat($PdfPath,17,$false)
    Write-Output ('Pages: '+$documentExport.ComputeStatistics(2))
    $documentExport.Close(0)
} finally {
    $wordExport.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordExport)
}

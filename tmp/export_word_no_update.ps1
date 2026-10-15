param([string]$DocxPath,[string]$PdfPath)
$ErrorActionPreference='Stop'
$wordExport=New-Object -ComObject Word.Application
$wordExport.Visible=$false
$wordExport.DisplayAlerts=0
try {
    $documentExport=$wordExport.Documents.Open($DocxPath,$false,$true,$false)
    $documentExport.Repaginate()
    $documentExport.ExportAsFixedFormat($PdfPath,17,$false)
    Write-Output ('Pages: '+$documentExport.ComputeStatistics(2))
    $documentExport.Close(0)
} finally {
    $wordExport.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordExport)
}

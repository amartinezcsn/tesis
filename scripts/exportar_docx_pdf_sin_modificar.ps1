param(
    [Parameter(Mandatory = $true)][string]$DocxPath,
    [Parameter(Mandatory = $true)][string]$PdfPath
)

$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $document = $word.Documents.Open(
        $DocxPath,
        $false,
        $true,
        $false,
        '',
        '',
        $false,
        '',
        '',
        0,
        0,
        $false,
        $true,
        0,
        $false,
        ''
    )
    $document.Repaginate()
    $document.ExportAsFixedFormat($PdfPath, 17, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    $document.Close(0)
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

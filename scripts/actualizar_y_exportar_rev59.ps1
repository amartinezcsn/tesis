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
        $false,
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
    foreach ($story in $document.StoryRanges) {
        $range = $story
        while ($null -ne $range) {
            if ($range.Fields.Count -gt 0) {
                [void]$range.Fields.Update()
            }
            $range = $range.NextStoryRange
        }
    }
    [void]$document.Fields.Update()
    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($PdfPath, 17, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('Fields: ' + $document.Fields.Count)
    $document.Close(0)
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

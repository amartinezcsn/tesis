param(
    [string]$DocxPath = 'C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx',
    [string]$PdfPath = 'C:\Python\tesis\tmp\rev58_render\TESIS_SEP2026_Rev58_QA.pdf'
)

$ErrorActionPreference = 'Stop'
$wdExportFormatPDF = 17
$wdPageBreak = 7
$wdAdjustedPage = 1

function Normalize-Ascii([string]$Value) {
    $decomposed = $Value.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object Text.StringBuilder
    foreach ($character in $decomposed.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($character) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($character)
        }
    }
    return $builder.ToString().ToUpperInvariant().Trim()
}

function Find-Paragraph {
    param($Document, [string]$Text)
    $needle = Normalize-Ascii $Text
    foreach ($paragraph in $Document.Paragraphs) {
        $value = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        if ((Normalize-Ascii $value) -eq $needle) { return $paragraph }
    }
    throw "Paragraph not found: $Text"
}

function Clear-Between {
    param($Document, [string]$StartText, [string]$EndText)
    $start = Find-Paragraph $Document $StartText
    $end = Find-Paragraph $Document $EndText
    $range = $Document.Range($start.Range.End, $end.Range.Start)
    $range.Text = ''
}

function Get-Headings {
    param($Document)
    $summary = Find-Paragraph $Document 'RESUMEN'
    $items = New-Object Collections.Generic.List[object]
    foreach ($paragraph in $Document.Paragraphs) {
        if ($paragraph.Range.Start -lt $summary.Range.Start) { continue }
        $level = [int]$paragraph.OutlineLevel
        if ($level -lt 1 -or $level -gt 3) { continue }
        $text = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        if (-not $text) { continue }
        $number = ($paragraph.Range.ListFormat.ListString -replace '[\r\a]', '').Trim()
        if ($number -and -not $text.StartsWith($number)) { $text = $number + ' ' + $text }
        $items.Add([pscustomobject]@{
            Text = $text
            Level = $level
            Page = $paragraph.Range.Information($wdAdjustedPage)
        })
    }
    return $items
}

function Get-Captions {
    param($Document)
    $summary = Find-Paragraph $Document 'RESUMEN'
    $items = New-Object Collections.Generic.List[object]
    foreach ($paragraph in $Document.Paragraphs) {
        if ($paragraph.Range.Start -le $summary.Range.Start) { continue }
        $text = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        if ($text -match '^(Figura|Tabla|Imagen)\s+\d+\s*[\.\-]') {
            $items.Add([pscustomobject]@{
                Text = $text
                Level = 1
                Page = $paragraph.Range.Information($wdAdjustedPage)
            })
        }
    }
    return $items
}

function Insert-StaticList {
    param($Document, [string]$StartText, [string]$EndText, $Items, [bool]$UsePages)
    Clear-Between $Document $StartText $EndText
    $start = Find-Paragraph $Document $StartText
    $range = $Document.Range($start.Range.End, $start.Range.End)
    $lines = New-Object Collections.Generic.List[string]
    foreach ($item in $Items) {
        $page = if ($UsePages) { [string]$item.Page } else { '000' }
        $indent = if ($item.Level -eq 1) { '' } elseif ($item.Level -eq 2) { '    ' } else { '        ' }
        $lines.Add($indent + $item.Text + "`t" + $page)
    }
    $range.InsertAfter(($lines -join "`r") + "`r")
    $end = Find-Paragraph $Document $EndText
    $end.Range.InsertBreak($wdPageBreak)
}

$pdfDirectory = Split-Path -Parent $PdfPath
New-Item -ItemType Directory -Force -Path $pdfDirectory | Out-Null

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $document = $word.Documents.Open($DocxPath, $false, $false)
    foreach ($control in $document.ContentControls) {
        try { $control.LockContents = $false } catch { }
        try { $control.LockContentControl = $false } catch { }
    }
    while ($document.TablesOfContents.Count -gt 0) {
        $document.TablesOfContents.Item(1).Range.Delete()
    }

    # Clean legacy results and rename the second index.
    Clear-Between $document 'INDICE' 'TABLAS, IMAGENES Y ECUACIONES'
    Clear-Between $document 'TABLAS, IMAGENES Y ECUACIONES' 'RESUMEN'
    $figureHeading = Find-Paragraph $document 'TABLAS, IMAGENES Y ECUACIONES'
    $figureHeading.Range.Text = ([char]0x00CD) + 'NDICE DE TABLAS Y FIGURAS' + "`r"

    $headings = Get-Headings $document
    $captions = Get-Captions $document
    Insert-StaticList $document 'INDICE' 'INDICE DE TABLAS Y FIGURAS' $headings $false
    Insert-StaticList $document 'INDICE DE TABLAS Y FIGURAS' 'RESUMEN' $captions $false
    $document.Repaginate()

    # Two stable passes: line counts remain fixed while page numbers are refreshed.
    for ($pass = 1; $pass -le 2; $pass++) {
        $headings = Get-Headings $document
        $captions = Get-Captions $document
        Insert-StaticList $document 'INDICE' 'INDICE DE TABLAS Y FIGURAS' $headings $true
        Insert-StaticList $document 'INDICE DE TABLAS Y FIGURAS' 'RESUMEN' $captions $true
        $document.Repaginate()
    }

    foreach ($field in $document.Fields) {
        try { $field.Update() | Out-Null } catch { }
    }
    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($PdfPath, $wdExportFormatPDF, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('Headings: ' + $headings.Count)
    Write-Output ('Captions: ' + $captions.Count)
    Write-Output ('Saved: ' + $DocxPath)
    Write-Output ('PDF: ' + $PdfPath)
    $document.Close(0)
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

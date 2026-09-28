param(
    [string]$DocxPath = 'C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx',
    [string]$PdfPath = 'C:\Python\tesis\tmp\rev58_render\TESIS_SEP2026_Rev58_QA.pdf'
)

$ErrorActionPreference = 'Stop'
$missing = [Type]::Missing
$wdExportFormatPDF = 17
$wdPageBreak = 7

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
    $Document.Range($start.Range.End, $end.Range.Start).Delete()
}

function Get-CaptionsAfterSummary {
    param($Document)
    $summary = Find-Paragraph $Document 'RESUMEN'
    $items = New-Object Collections.Generic.List[object]
    foreach ($paragraph in $Document.Paragraphs) {
        if ($paragraph.Range.Start -le $summary.Range.Start) { continue }
        $text = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        if ($text -match '^(Figura|Tabla|Imagen)\s+\d+\s*[\.\-]') {
            $items.Add([pscustomobject]@{ Text = $text; Page = $paragraph.Range.Information(3) })
        }
    }
    return $items
}

function Insert-FigureList {
    param($Document, $Items, [bool]$UsePages)
    $heading = Find-Paragraph $Document 'INDICE DE TABLAS Y FIGURAS'
    $summary = Find-Paragraph $Document 'RESUMEN'
    $Document.Range($heading.Range.End, $summary.Range.Start).Delete()
    $heading = Find-Paragraph $Document 'INDICE DE TABLAS Y FIGURAS'
    $range = $Document.Range($heading.Range.End, $heading.Range.End)
    $lines = New-Object Collections.Generic.List[string]
    foreach ($item in $Items) {
        $page = if ($UsePages) { [string]$item.Page } else { '000' }
        $lines.Add($item.Text + "`t" + $page)
    }
    $range.InsertAfter(($lines -join "`r") + "`r")
    $summary = Find-Paragraph $Document 'RESUMEN'
    $summary.Range.InsertBreak($wdPageBreak)
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

    # Rebuild the main TOC from heading styles.
    Clear-Between $document 'INDICE' 'TABLAS, IMAGENES Y ECUACIONES'
    $indexHeading = Find-Paragraph $document 'INDICE'
    $tocRange = $document.Range($indexHeading.Range.End, $indexHeading.Range.End)
    $toc = $document.TablesOfContents.Add($tocRange, $true, 1, 3, $true, $missing, $true, $true, $true, $true, $true, $true)
    $toc.Update() | Out-Null

    # Replace the broken figure/table field with a deterministic static list.
    $figureHeading = Find-Paragraph $document 'TABLAS, IMAGENES Y ECUACIONES'
    $figureHeading.Range.Text = ([char]0x00CD) + 'NDICE DE TABLAS Y FIGURAS' + "`r"
    $initialCaptions = Get-CaptionsAfterSummary $document
    Insert-FigureList $document $initialCaptions $false
    $document.Repaginate()

    $pagedCaptions = Get-CaptionsAfterSummary $document
    Insert-FigureList $document $pagedCaptions $true
    $document.Repaginate()

    foreach ($tocItem in $document.TablesOfContents) {
        $tocItem.Update() | Out-Null
        $tocItem.UpdatePageNumbers() | Out-Null
    }
    foreach ($field in $document.Fields) {
        try { $field.Update() | Out-Null } catch { }
    }
    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($PdfPath, $wdExportFormatPDF, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('TOCs: ' + $document.TablesOfContents.Count)
    Write-Output ('Captions: ' + $pagedCaptions.Count)
    Write-Output ('Saved: ' + $DocxPath)
    Write-Output ('PDF: ' + $PdfPath)
    $document.Close(0)
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

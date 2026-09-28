param(
    [string]$DocxPath = 'C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx',
    [string]$PdfPath = 'C:\Python\tesis\tmp\rev58_render\TESIS_SEP2026_Rev58_QA.pdf'
)

$ErrorActionPreference = 'Stop'
$wdFieldTOC = 13
$wdCollapseEnd = 0
$wdExportFormatPDF = 17

function Find-ParagraphByExactText {
    param($Document, [string]$Text)
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
    $needle = Normalize-Ascii $Text
    foreach ($paragraph in $Document.Paragraphs) {
        $value = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        if ((Normalize-Ascii $value) -eq $needle) {
            return $paragraph
        }
    }
    throw "Paragraph not found: $Text"
}

function Replace-SectionWithField {
    param(
        $Document,
        [string]$HeadingText,
        [string]$NextHeadingText,
        [string]$FieldCode
    )
    $heading = Find-ParagraphByExactText -Document $Document -Text $HeadingText
    $next = Find-ParagraphByExactText -Document $Document -Text $NextHeadingText
    $deleteRange = $Document.Range($heading.Range.End, $next.Range.Start)
    $deleteRange.Delete()

    $heading = Find-ParagraphByExactText -Document $Document -Text $HeadingText
    $insertRange = $Document.Range($heading.Range.End, $heading.Range.End)
    $field = $Document.Fields.Add($insertRange, $wdFieldTOC, $FieldCode, $true)
    $field.Update() | Out-Null
}

$pdfDirectory = Split-Path -Parent $PdfPath
New-Item -ItemType Directory -Force -Path $pdfDirectory | Out-Null

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $document = $word.Documents.Open($DocxPath, $false, $false)

    Replace-SectionWithField -Document $document -HeadingText 'INDICE' -NextHeadingText 'TABLAS, IMAGENES Y ECUACIONES' -FieldCode '\o "1-3" \h \z \u'
    Replace-SectionWithField -Document $document -HeadingText 'TABLAS, IMAGENES Y ECUACIONES' -NextHeadingText 'RESUMEN' -FieldCode '\h \z \t "Caption,1"'

    foreach ($field in $document.Fields) {
        try { $field.Update() | Out-Null } catch { }
    }
    foreach ($toc in $document.TablesOfContents) {
        $toc.Update() | Out-Null
        $toc.UpdatePageNumbers() | Out-Null
    }

    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($PdfPath, $wdExportFormatPDF, $false)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('Fields: ' + $document.Fields.Count)
    Write-Output ('Saved: ' + $DocxPath)
    Write-Output ('PDF: ' + $PdfPath)
    $document.Close(0)
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

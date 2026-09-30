param(
    [string]$SourcePath = 'C:\Python\tesis\documentacion\TESIS_SEP2026_Rev60_(ZUJ)_Final.docx',
    [string]$OutputPath = 'C:\Python\tesis\documentacion\TESIS_SEP2026_Rev61_(ZUJ)_Final.docx',
    [string]$PdfPath = 'C:\Python\tesis\tmp\rev61_render\TESIS_SEP2026_Rev61_QA_word.pdf',
    [string]$LogPath = 'C:\Python\tesis\tmp\rev61_render\crear_rev61.log'
)

$ErrorActionPreference = 'Stop'

function Get-CleanParagraphText {
    param($Paragraph)
    return (($Paragraph.Range.Text -replace '[\r\a]', '').Trim())
}

function Find-ParagraphExact {
    param($Document, [string]$Text)
    foreach ($paragraph in $Document.Paragraphs) {
        if ((Get-CleanParagraphText $paragraph) -eq $Text) {
            return $paragraph
        }
    }
    throw "No se encontro el parrafo: $Text"
}

function Find-MarkerRange {
    param($Document, [string]$Marker)
    $range = $Document.Content.Duplicate
    $find = $range.Find
    $find.ClearFormatting()
    $find.Text = $Marker
    $find.Forward = $true
    $find.Wrap = 0
    if (-not $find.Execute()) {
        throw "No se encontro el marcador temporal: $Marker"
    }
    return $range
}

function Set-IndexHeadingFormat {
    param($Paragraph)
    $Paragraph.Range.ParagraphFormat.Reset()
    $Paragraph.Range.Style = -1
    $Paragraph.OutlineLevel = 10
    $Paragraph.Range.Font.Name = 'Arial'
    $Paragraph.Range.Font.Size = 12
    $Paragraph.Range.Font.Bold = 1
    $Paragraph.Range.Font.Color = 0
    $Paragraph.Range.ParagraphFormat.Alignment = 1
    $Paragraph.Range.ParagraphFormat.SpaceBefore = 0
    $Paragraph.Range.ParagraphFormat.SpaceAfter = 6
    $Paragraph.Range.ParagraphFormat.PageBreakBefore = 0
    $Paragraph.Range.ParagraphFormat.KeepWithNext = -1
}

function Set-ListCompactFormat {
    param($Toc)
    $range = $Toc.Range
    $range.Font.Name = 'Arial'
    $range.Font.Size = 9
    $range.Font.Bold = 0
    $range.Font.Color = 0
    $range.ParagraphFormat.SpaceBefore = 0
    $range.ParagraphFormat.SpaceAfter = 0
    $range.ParagraphFormat.LineSpacingRule = 0
}

$outputDirectory = Split-Path -Parent $OutputPath
$pdfDirectory = Split-Path -Parent $PdfPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $pdfDirectory | Out-Null
[System.IO.File]::WriteAllText($LogPath, "inicio`r`n")
function Write-Log([string]$Message) {
    [System.IO.File]::AppendAllText($LogPath, $Message + "`r`n")
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null

try {
    Write-Log 'abriendo fuente'
    $document = $word.Documents.Open($SourcePath, $false, $false)
    Write-Log 'guardando copia inicial'
    $document.SaveAs2($OutputPath, 16)

    Write-Log 'localizando encabezados'
    $indexHeading = Find-ParagraphExact $document 'ÍNDICE'
    $summaryHeading = Find-ParagraphExact $document 'RESUMEN'

    # Elimina el indice manual y el indice combinado, conservando sus encabezados extremos.
    $frontRange = $document.Range($indexHeading.Range.End, $summaryHeading.Range.Start)
    $frontRange.Text = ''
    Write-Log 'bloque frontal eliminado'

    # Inserta tres zonas independientes. Los saltos de pagina quedan dentro de la zona
    # de indices, por lo que RESUMEN siempre comienza despues del indice de imagenes.
    $insertRange = $document.Range($indexHeading.Range.End, $indexHeading.Range.End)
    $pageBreak = [char]12
    $insertText = '[[MAIN_TOC]]' + "`r" + $pageBreak + 'ÍNDICE DE TABLAS' + "`r" + '[[TABLE_TOC]]' + "`r" + $pageBreak + 'ÍNDICE DE IMÁGENES' + "`r" + '[[IMAGE_TOC]]' + "`r"
    $insertRange.InsertAfter($insertText)
    Write-Log 'marcadores temporales insertados'

    Set-IndexHeadingFormat (Find-ParagraphExact $document 'ÍNDICE DE TABLAS')
    Set-IndexHeadingFormat (Find-ParagraphExact $document 'ÍNDICE DE IMÁGENES')
    foreach ($markerText in @('[[MAIN_TOC]]', '[[TABLE_TOC]]', '[[IMAGE_TOC]]')) {
        $markerParagraph = Find-ParagraphExact $document $markerText
        $markerParagraph.Range.ParagraphFormat.Reset()
        $markerParagraph.Range.Style = -1
        $markerParagraph.OutlineLevel = 10
        $markerParagraph.Range.ParagraphFormat.PageBreakBefore = 0
    }

    # Crea entradas TC invisibles y marcadores estables en cada leyenda real.
    $summaryHeading = Find-ParagraphExact $document 'RESUMEN'
    $tableCount = 0
    $figureCount = 0
    $captionParagraphs = @($document.Paragraphs)
    Write-Log ('parrafos enumerados: ' + $captionParagraphs.Count)
    foreach ($paragraph in $captionParagraphs) {
        if ($paragraph.Range.Start -le $summaryHeading.Range.Start) {
            continue
        }
        $caption = Get-CleanParagraphText $paragraph
        $kind = $null
        $tableId = $null
        if ($caption -match '^Tabla\s+\d+\.') {
            $kind = 'Tabla'
            $tableId = 'T'
            $tableCount++
            $bookmarkName = ('idxTabla{0:D3}' -f $tableCount)
        }
        elseif ($caption -match '^Figura\s+\d+\.') {
            $kind = 'Figura'
            $tableId = 'F'
            $figureCount++
            $bookmarkName = ('idxFigura{0:D3}' -f $figureCount)
        }
        else {
            continue
        }

        $bookmarkRange = $paragraph.Range.Duplicate
        $bookmarkRange.End = $bookmarkRange.End - 1
        if ($document.Bookmarks.Exists($bookmarkName)) {
            $document.Bookmarks.Item($bookmarkName).Delete()
        }
        [void]$document.Bookmarks.Add($bookmarkName, $bookmarkRange)

        $escapedCaption = $caption.Replace('"', "'")
        $fieldRange = $paragraph.Range.Duplicate
        $fieldRange.Collapse(1)
        $fieldCode = ('TC "{0}" \f {1} \l 1' -f $escapedCaption, $tableId)
        [void]$document.Fields.Add($fieldRange, -1, $fieldCode, $false)
    }

    if ($tableCount -eq 0 -or $figureCount -eq 0) {
        throw "No se detectaron suficientes leyendas: tablas=$tableCount figuras=$figureCount"
    }
    Write-Log ("leyendas preparadas: tablas=$tableCount figuras=$figureCount")

    # Los indices se agregan en orden inverso para que cada marcador exista una sola vez
    # cuando Word expanda el campo anterior. Todos los marcadores usan nivel de cuerpo.
    $figureRange = Find-MarkerRange $document '[[IMAGE_TOC]]'
    $figureRange.Text = ''
    $figureRange.Collapse(1)
    $figureToc = $document.TablesOfContents.Add($figureRange, $false, 1, 1, $true, 'F', $true, $true, '', $true, $true, $false)
    Write-Log 'indice de imagenes agregado'

    $tableRange = Find-MarkerRange $document '[[TABLE_TOC]]'
    $tableRange.Text = ''
    $tableRange.Collapse(1)
    $tableToc = $document.TablesOfContents.Add($tableRange, $false, 1, 1, $true, 'T', $true, $true, '', $true, $true, $false)
    Write-Log 'indice de tablas agregado'

    # Tabla de contenido principal basada en estilos de titulo 1 a 3.
    $mainRange = Find-MarkerRange $document '[[MAIN_TOC]]'
    $mainRange.Text = ''
    $mainRange.Collapse(1)
    $mainToc = $document.TablesOfContents.Add($mainRange, $true, 1, 3, $false, '', $true, $true, '', $true, $true, $true)
    Write-Log 'TOC principal agregado'

    Set-ListCompactFormat $tableToc
    Set-ListCompactFormat $figureToc

    # Guarda los campos antes de actualizarlos y evita una actualizacion global de todos
    # los campos, que puede desestabilizar documentos extensos con muchas ecuaciones.
    Write-Log ('TOC registrados: ' + $document.TablesOfContents.Count)
    $document.Save()
    Write-Log 'estructura con campos guardada'
    $document.Repaginate()
    for ($index = $document.TablesOfContents.Count; $index -ge 1; $index--) {
        $toc = $document.TablesOfContents.Item($index)
        [void]$toc.Update()
        Write-Log ('TOC actualizado: ' + $index)
    }
    $document.Repaginate()
    for ($index = $document.TablesOfContents.Count; $index -ge 1; $index--) {
        $toc = $document.TablesOfContents.Item($index)
        [void]$toc.UpdatePageNumbers()
    }
    $document.Save()
    Write-Log 'documento guardado'
    $document.ExportAsFixedFormat($PdfPath, 17, $false)
    Write-Log 'PDF exportado'

    Write-Output ('Output: ' + $OutputPath)
    Write-Output ('PDF: ' + $PdfPath)
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
    Write-Output ('TOCs: ' + $document.TablesOfContents.Count)
    Write-Output ('Tables indexed: ' + $tableCount)
    Write-Output ('Figures indexed: ' + $figureCount)
    Write-Output ('Bookmarks: ' + $document.Bookmarks.Count)
}
catch {
    Write-Log ('ERROR: ' + $_.Exception.Message)
    Write-Log $_.ScriptStackTrace
    throw
}
finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

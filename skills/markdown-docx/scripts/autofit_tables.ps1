[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$word = $null
$document = $null
$tables = $null
$wordPidsBefore = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$ownsWordProcess = $false
$exitCode = 1
$tableCount = 0

function Release-ComObject {
    param([object]$Value)
    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

try {
    $resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
    if ([System.IO.Path]::GetExtension($resolvedInput) -ine '.docx') {
        throw "Input must be a DOCX file: $resolvedInput"
    }

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.ScreenUpdating = $false

    try { $word.AutomationSecurity = 3 } catch { }
    try { $word.Options.SaveNormalPrompt = $false } catch { }
    try { $word.Options.UpdateLinksAtOpen = $false } catch { }
    try { $word.Options.ConfirmConversions = $false } catch { }

    for ($attempt = 0; $attempt -lt 20 -and -not $ownsWordProcess; $attempt++) {
        Start-Sleep -Milliseconds 100
        $newWordProcesses = @(
            Get-Process WINWORD -ErrorAction SilentlyContinue |
                Where-Object { $_.Id -notin $wordPidsBefore }
        )
        $ownsWordProcess = $newWordProcesses.Count -gt 0
    }

    # FileName, ConfirmConversions, ReadOnly, AddToRecentFiles.
    $document = $word.Documents.Open($resolvedInput, $false, $false, $false)
    $tables = $document.Tables
    $tableCount = [int]$tables.Count

    for ($index = 1; $index -le $tableCount; $index++) {
        $table = $null
        try {
            $table = $tables.Item($index)
            # wdAutoFitContent = 1, followed by wdAutoFitWindow = 2.
            $table.AutoFitBehavior(1)
            $table.AutoFitBehavior(2)
        } finally {
            Release-ComObject -Value $table
        }
    }

    if ($tableCount -gt 0) {
        $document.Save()
    }
    Write-Output "Auto-fitted $tableCount table(s): content, then window."
    $exitCode = 0
} catch {
    [Console]::Error.WriteLine($_.Exception.ToString())
} finally {
    if ($null -ne $tables) {
        Release-ComObject -Value $tables
        $tables = $null
    }

    if ($null -ne $document) {
        try {
            $saveDocumentChanges = 0
            $document.Close([ref]$saveDocumentChanges)
        } catch {
            [Console]::Error.WriteLine("Document close failed: $($_.Exception.Message)")
            $exitCode = 1
        }
        Release-ComObject -Value $document
        $document = $null
    }

    if ($null -ne $word) {
        try {
            if ($null -ne $word.NormalTemplate) {
                $word.NormalTemplate.Saved = $true
            }
        } catch { }
        if ($ownsWordProcess) {
            try {
                $saveWordChanges = 0
                $word.Quit([ref]$saveWordChanges)
            } catch {
                [Console]::Error.WriteLine("Word quit failed: $($_.Exception.Message)")
                $exitCode = 1
            }
        } else {
            [Console]::Error.WriteLine(
                'Word process ownership was not proven; released COM without calling Quit.'
            )
        }
        Release-ComObject -Value $word
        $word = $null
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

exit $exitCode

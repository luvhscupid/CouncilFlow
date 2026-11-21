[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Status,
    [switch]$Update,
    [switch]$Uninstall,
    [switch]$DryRun,
    [switch]$CheckRemote,
    [switch]$UpdateRemote,
    [switch]$Rollback,
    [switch]$EnableAutomatic,
    [switch]$DisableAutomatic
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'CouncilFlow bootstrap requires PowerShell 7 or later (pwsh). No files were changed.' }
$actions = @()
foreach ($name in @('Install','Status','Update','Uninstall','CheckRemote','UpdateRemote','Rollback','EnableAutomatic','DisableAutomatic')) {
    if ((Get-Variable -Name $name -ValueOnly).IsPresent) { $actions += $name }
}
$modes = $actions.Count
if ($modes -gt 1) { throw 'Choose one bootstrap action; -DryRun may modify actions that support it.' }
if ($modes -eq 0) { $Status = $true }

$script:RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$script:UserHome = if ($env:COUNCILFLOW_BOOTSTRAP_HOME) {
    [IO.Path]::GetFullPath($env:COUNCILFLOW_BOOTSTRAP_HOME)
} elseif ($env:USERPROFILE) {
    [IO.Path]::GetFullPath($env:USERPROFILE)
} else {
    [IO.Path]::GetFullPath($HOME)
}
$script:ManifestPath = Join-Path $script:UserHome '.councilflow\bootstrap.json'
$script:LauncherRoot = Join-Path $script:UserHome '.councilflow\launcher'

function Get-FileHashHex([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-TreeHash([string]$Path) {
    $root = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $files = @(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.Extension -ne '.pyc' } | Sort-Object { $_.FullName.Substring($root.Length) })
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
            $line = [Text.Encoding]::UTF8.GetBytes($relative + "`0" + (Get-FileHashHex $file.FullName) + "`n")
            [void]$sha.TransformBlock($line, 0, $line.Length, $line, 0)
        }
        [void]$sha.TransformFinalBlock([byte[]]::new(0), 0, 0)
        return ([BitConverter]::ToString($sha.Hash)).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Get-SourceHash($Entry) {
    if ($Entry.kind -eq 'directory') { return Get-TreeHash $Entry.source }
    return Get-FileHashHex $Entry.source
}

function Get-Entries {
    param([string]$SourceRoot = $script:RepoRoot)
    $entries = @(
        [pscustomobject]@{ id='skill'; kind='directory'; source=(Join-Path $SourceRoot '.agents\skills\council-flow'); destination=(Join-Path $script:UserHome '.agents\skills\council-flow') }
    )
    if ((Get-Command claude -ErrorAction SilentlyContinue) -and
        (Test-Path (Join-Path $SourceRoot 'plugins\councilflow\.claude-plugin\plugin.json'))) {
        $entries += [pscustomobject]@{ id='claude-plugin'; kind='directory'; source=(Join-Path $SourceRoot 'plugins\councilflow'); destination=(Join-Path $script:UserHome '.claude\skills\councilflow') }
    }
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $SourceRoot '.codex\agents') -Filter 'council-*.toml' -File) {
        $entries += [pscustomobject]@{ id=('role-' + $file.BaseName); kind='file'; source=$file.FullName; destination=(Join-Path $script:UserHome ('.codex\agents\' + $file.Name)) }
    }
    return $entries
}

function Read-Manifest {
    if (-not (Test-Path -LiteralPath $script:ManifestPath -PathType Leaf)) { return @{ version=1; source=$script:RepoRoot; installs=@(); launcher=@() } }
    $data = Get-Content -LiteralPath $script:ManifestPath -Raw | ConvertFrom-Json
    if ($data.version -ne 1 -or $data.source -ne $script:RepoRoot) { throw "Refusing unexpected bootstrap manifest: $script:ManifestPath" }
    foreach ($field in @('active_source','active_commit','previous_source','previous_commit','update_result','launcher')) {
        if (-not $data.PSObject.Properties[$field]) { $data | Add-Member -MemberType NoteProperty -Name $field -Value $null }
    }
    return $data
}

function Get-LauncherEntries {
    return @(
        [pscustomobject]@{ name='bootstrap.ps1'; source=(Join-Path $PSScriptRoot 'bootstrap.ps1'); destination=(Join-Path $script:LauncherRoot 'bootstrap.ps1') },
        [pscustomobject]@{ name='remote-update.ps1'; source=(Join-Path $PSScriptRoot 'remote-update.ps1'); destination=(Join-Path $script:LauncherRoot 'remote-update.ps1') }
    )
}

function Get-LauncherConflicts($Manifest) {
    $conflicts = @()
    foreach ($entry in Get-LauncherEntries) {
        if (-not (Test-Path -LiteralPath $entry.destination)) { continue }
        $hash = Get-FileHashHex $entry.destination
        $record = @($Manifest.launcher | Where-Object name -eq $entry.name | Select-Object -First 1)
        if ($record.Count -and $hash -eq $record[0].installed_hash) { continue }
        if (-not $record.Count -and $hash -eq (Get-FileHashHex $entry.source)) { continue }
        $conflicts += $entry.name
    }
    return $conflicts
}

function Sync-Launcher($Manifest) {
    $records = @()
    foreach ($entry in Get-LauncherEntries) {
        if ($DryRun) { Write-Host "DRY-RUN copy managed launcher $($entry.source) -> $($entry.destination)" }
        else {
            New-Item -ItemType Directory -Force -Path $script:LauncherRoot | Out-Null
            $temp = $entry.destination + '.next'
            Copy-Item -LiteralPath $entry.source -Destination $temp -Force
            Move-Item -LiteralPath $temp -Destination $entry.destination -Force
        }
        $hash = if ($DryRun) { Get-FileHashHex $entry.source } else { Get-FileHashHex $entry.destination }
        $records += [pscustomobject]@{ name=$entry.name; source=$entry.source; destination=$entry.destination; installed_hash=$hash }
    }
    if (-not $DryRun) { $Manifest.launcher = $records }
}

function Save-Manifest($Manifest) {
    $dir = Split-Path -Parent $script:ManifestPath
    if ($DryRun) { Write-Host "DRY-RUN create/update manifest $script:ManifestPath"; return }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $script:ManifestPath -Encoding utf8
}

function Test-ExactLink($Entry, $Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item -or -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $false }
    $target = $item.Target
    if (-not $target) { return $false }
    try { return ([IO.Path]::GetFullPath($target) -eq [IO.Path]::GetFullPath($Entry.source)) } catch { return $false }
}

function New-DirectoryLink([string]$Path, [string]$Target) {
    New-Item -ItemType Junction -Path $Path -Target $Target | Out-Null
}

function Test-EntryCollision($Entry, $Manifest) {
    if (-not (Test-Path -LiteralPath $Entry.destination)) { return $false }
    if (Test-ExactLink $Entry $Entry.destination) { return $false }
    $record = $Manifest.installs | Where-Object { $_.id -eq $Entry.id } | Select-Object -First 1
    $isReparse = ((Get-Item -LiteralPath $Entry.destination -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)
    if (-not $isReparse) {
        $existingHash = if ($Entry.kind -eq 'directory') { Get-TreeHash $Entry.destination } else { Get-FileHashHex $Entry.destination }
        if (-not $record -and $existingHash -eq (Get-SourceHash $Entry)) { return $false }
        if ($record -and $record.mode -eq 'copy' -and $record.destination -eq $Entry.destination -and $existingHash -eq $record.installed_hash) { return $false }
    }
    return $true
}

function Install-Entry($Entry, $Manifest) {
    $record = $Manifest.installs | Where-Object { $_.id -eq $Entry.id } | Select-Object -First 1
    $parent = Split-Path -Parent $Entry.destination
    if (-not (Test-Path -LiteralPath $parent)) {
        if ($DryRun) { Write-Host "DRY-RUN create directory $parent" } else { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    }
    if (Test-Path -LiteralPath $Entry.destination) {
        if (Test-ExactLink $Entry $Entry.destination) {
            Write-Host "LINKED $($Entry.id): $($Entry.destination)"
            if ($record) { $record.source_hash = Get-SourceHash $Entry }
            else { $Manifest.installs += @{ id=$Entry.id; kind=$Entry.kind; source=$Entry.source; destination=$Entry.destination; mode='link'; source_hash=(Get-SourceHash $Entry) } }
            return
        }
        if (-not $record -and -not ((Get-Item -LiteralPath $Entry.destination -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $existingHash = if ($Entry.kind -eq 'directory') { Get-TreeHash $Entry.destination } else { Get-FileHashHex $Entry.destination }
            if ($existingHash -eq (Get-SourceHash $Entry)) {
                $Manifest.installs += @{ id=$Entry.id; kind=$Entry.kind; source=$Entry.source; destination=$Entry.destination; mode='copy'; source_hash=$existingHash; installed_hash=$existingHash }
                Write-Host "ADOPTED IDENTICAL COPY $($Entry.id) (safe hash-tracked refresh enabled)"
                return
            }
        }
        if ($record -and $record.mode -eq 'copy' -and $record.destination -eq $Entry.destination) {
            $currentHash = if ($Entry.kind -eq 'directory') { Get-TreeHash $Entry.destination } else { Get-FileHashHex $Entry.destination }
            if ($currentHash -ne $record.installed_hash) { throw "Collision: managed copy was locally changed; refusing update: $($Entry.destination)" }
            if ($DryRun) { Write-Host "DRY-RUN refresh managed copy $($Entry.destination)"; return }
            if ($Entry.kind -eq 'directory') { Remove-Item -LiteralPath $Entry.destination -Recurse -Force; Copy-Item -LiteralPath $Entry.source -Destination $Entry.destination -Recurse }
            else { Copy-Item -LiteralPath $Entry.source -Destination $Entry.destination -Force }
            $record.source_hash = Get-SourceHash $Entry
            $record.installed_hash = if ($Entry.kind -eq 'directory') { Get-TreeHash $Entry.destination } else { Get-FileHashHex $Entry.destination }
            Write-Host "UPDATED managed copy $($Entry.id)"
            return
        }
        throw "Collision: destination exists and is not this installation: $($Entry.destination)"
    }
    if ($DryRun) { Write-Host "DRY-RUN link/copy $($Entry.source) -> $($Entry.destination)"; return }
    try {
        if ($Entry.kind -eq 'directory') { New-DirectoryLink $Entry.destination $Entry.source }
        else { New-Item -ItemType SymbolicLink -Path $Entry.destination -Target $Entry.source | Out-Null }
        $mode = 'link'
    } catch {
        if ($Entry.kind -eq 'directory') { Copy-Item -LiteralPath $Entry.source -Destination $Entry.destination -Recurse }
        else { Copy-Item -LiteralPath $Entry.source -Destination $Entry.destination }
        $mode = 'copy'
    }
    $installedHash = if ($mode -eq 'copy') { if ($Entry.kind -eq 'directory') { Get-TreeHash $Entry.destination } else { Get-FileHashHex $Entry.destination } } else { $null }
    $Manifest.installs += @{ id=$Entry.id; kind=$Entry.kind; source=$Entry.source; destination=$Entry.destination; mode=$mode; source_hash=(Get-SourceHash $Entry); installed_hash=$installedHash }
    Write-Host "$($mode.ToUpperInvariant()) $($Entry.id): $($Entry.destination)"
}

function Show-Status($Manifest) {
    Write-Host "Source: $script:RepoRoot"
    Write-Host "Commit: $(& git -C $script:RepoRoot rev-parse HEAD 2>$null)"
    if ($Manifest.active_commit) { Write-Host "Installed version: $($Manifest.active_commit)" }
    if ($Manifest.active_source) { Write-Host "Installed source: $($Manifest.active_source)" }
    $gitStatus = & git -C $script:RepoRoot status --porcelain 2>$null
    if ($gitStatus) { Write-Host 'Checkout: DIRTY (remote updates are not applied by this bootstrap)' }
    else { Write-Host 'Checkout: clean' }
    if (-not $Manifest.installs.Count) { Write-Host 'Install: not registered'; return }
    foreach ($record in $Manifest.installs) {
        $entryRoot = if ($Manifest.active_source) { $Manifest.active_source } else { $script:RepoRoot }
        $entry = Get-Entries $entryRoot | Where-Object id -eq $record.id | Select-Object -First 1
        if (-not $entry -or -not (Test-Path -LiteralPath $record.destination)) { Write-Host "MISSING $($record.id)"; continue }
        if ($record.mode -eq 'link' -and (Test-ExactLink $entry $record.destination)) { Write-Host "LINKED $($record.id) -> $($entry.source)" }
        elseif ($record.mode -eq 'copy') {
            $hash = if ($record.kind -eq 'directory') { Get-TreeHash $record.destination } else { Get-FileHashHex $record.destination }
            if ($hash -eq $record.installed_hash) { Write-Host "MANAGED COPY $($record.id) (current; -Update refreshes it)" }
            else { Write-Host "CHANGED MANAGED COPY $($record.id): preserved until reviewed" }
        }
        else { Write-Host "COLLISION/CHANGED $($record.id): $($record.destination)" }
    }
    foreach ($record in $Manifest.launcher) {
        $hash = if (Test-Path -LiteralPath $record.destination) { Get-FileHashHex $record.destination } else { '' }
        if ($hash -eq $record.installed_hash) { Write-Host "MANAGED UPDATER $($record.name): current" }
        else { Write-Host "CHANGED UPDATER $($record.name): preserved" }
    }
}

$manifest = Read-Manifest
if ($Status) { Show-Status $manifest; exit 0 }
if ($CheckRemote -or $UpdateRemote -or $Rollback) {
    $helperArgs = @('-RepoRoot', $script:RepoRoot, '-UserHome', $script:UserHome)
    if ($UpdateRemote) { $helperArgs += '-Activate' }
    if ($Rollback) { $helperArgs += '-Rollback' }
    if ($DryRun) { $helperArgs += '-DryRun' }
    & (Join-Path $PSScriptRoot 'remote-update.ps1') @helperArgs
    if (-not $?) { exit 1 }
    exit 0
}
if ($EnableAutomatic) {
    $taskName = 'CouncilFlow-Remote-Update'
    if (@($manifest.launcher).Count -lt 2 -and -not $DryRun) { throw 'Run -Install first to prepare the hash-tracked managed updater.' }
    $scriptPath = Join-Path $script:LauncherRoot 'remote-update.ps1'
    $taskCommand = "-NoProfile -File `"$scriptPath`" -RepoRoot `"$($manifest.source)`" -UserHome `"$script:UserHome`" -Activate"
    if ($DryRun) { Write-Host "DRY-RUN register daily Task Scheduler task '$taskName' for user $env:USERNAME"; Write-Host "PowerShell arguments: $taskCommand"; exit 0 }
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw "Task '$taskName' already exists; refusing to replace it." }
    $action = New-ScheduledTaskAction -Execute (Get-Process -Id $PID).Path -Argument $taskCommand
    $trigger = New-ScheduledTaskTrigger -Daily -At 3:00am
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description 'Opt-in CouncilFlow fast-forward update check and validated activation.' | Out-Null
    Write-Host "Registered '$taskName'. Disable with -DisableAutomatic."
    exit 0
}
if ($DisableAutomatic) {
    $taskName = 'CouncilFlow-Remote-Update'
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task) { Write-Host 'Automatic update task is not registered.'; exit 0 }
    $expectedScript = Join-Path $script:LauncherRoot 'remote-update.ps1'
    $ownsTask = @($task.Actions | Where-Object { $_.Arguments -like "*`"$expectedScript`"* -Activate*" }).Count -gt 0
    if (-not $ownsTask) { throw "Task '$taskName' does not match this bootstrap; refusing removal." }
    if ($DryRun) { Write-Host "DRY-RUN unregister owned task '$taskName'"; exit 0 }
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    exit 0
}
if ($Install -or $Update) {
    $sourceRoot = if ($manifest.active_source) { $manifest.active_source } else { $script:RepoRoot }
    $entries = @(Get-Entries $sourceRoot)
    $errors = @($entries | Where-Object { Test-EntryCollision $_ $manifest })
    $launcherErrors = @(Get-LauncherConflicts $manifest)
    foreach ($entry in $errors) { Write-Host "COLLISION $($entry.id): existing destination will be preserved: $($entry.destination)" }
    foreach ($name in $launcherErrors) { Write-Host "COLLISION managed updater ${name}: existing destination will be preserved" }
    if ($DryRun) {
        foreach ($entry in $entries) { if ($entry.id -notin @($errors | ForEach-Object id)) { Install-Entry $entry $manifest } }
        if (-not $launcherErrors.Count) { Sync-Launcher $manifest }
    }
    elseif ($errors.Count -or $launcherErrors.Count) { throw "No installation changes made. Resolve collisions first: $((@($errors | ForEach-Object id) + $launcherErrors) -join ', ')" }
    else { foreach ($entry in $entries) { Install-Entry $entry $manifest }; Sync-Launcher $manifest }
    if (-not $manifest.active_source) {
        $manifest.active_source = $script:RepoRoot
        $manifest.active_commit = & git -C $script:RepoRoot rev-parse HEAD 2>$null
    }
    Save-Manifest $manifest
    Write-Host 'Local synchronization uses links where supported. Remote updates require -CheckRemote or -UpdateRemote.'
    exit 0
}
if ($Uninstall) {
    $autoTask = if (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) { Get-ScheduledTask -TaskName 'CouncilFlow-Remote-Update' -ErrorAction SilentlyContinue } else { $null }
    if ($autoTask) { throw "Disable the verified CouncilFlow scheduled task with -DisableAutomatic before uninstall." }
    $remaining = @()
    $remainingLauncher = @()
    foreach ($record in @($manifest.installs)) {
        $entryRoot = if ($manifest.active_source) { $manifest.active_source } else { $script:RepoRoot }
        $entry = Get-Entries $entryRoot | Where-Object id -eq $record.id | Select-Object -First 1
        if (-not (Test-Path -LiteralPath $record.destination)) { continue }
        if ($record.mode -eq 'link' -and $entry -and (Test-ExactLink $entry $record.destination)) {
            if ($DryRun) { Write-Host "DRY-RUN remove link $($record.destination)" }
            elseif ($record.kind -eq 'directory') { [IO.Directory]::Delete($record.destination, $false) }
            else { Remove-Item -LiteralPath $record.destination -Force }
        } elseif ($record.mode -eq 'copy') {
            $actual = if ($record.kind -eq 'directory') { Get-TreeHash $record.destination } else { Get-FileHashHex $record.destination }
            if ($actual -ne $record.installed_hash) { Write-Host "PRESERVED changed managed copy: $($record.destination)"; $remaining += $record; continue }
            if ($DryRun) { Write-Host "DRY-RUN remove managed copy $($record.destination)" }
            elseif ($record.kind -eq 'directory') { Remove-Item -LiteralPath $record.destination -Recurse -Force }
            else { Remove-Item -LiteralPath $record.destination -Force }
        } else { Write-Host "PRESERVED unrecognized destination: $($record.destination)"; $remaining += $record }
    }
    foreach ($record in @($manifest.launcher)) {
        if (-not (Test-Path -LiteralPath $record.destination)) { continue }
        if ((Get-FileHashHex $record.destination) -ne $record.installed_hash) { Write-Host "PRESERVED changed managed updater: $($record.destination)"; $remainingLauncher += $record; continue }
        if ($DryRun) { Write-Host "DRY-RUN remove managed updater $($record.destination)" }
        else { Remove-Item -LiteralPath $record.destination -Force }
    }
    if (-not $DryRun -and (Test-Path -LiteralPath $script:ManifestPath)) {
        if ($remaining.Count -or $remainingLauncher.Count) { $manifest.installs = $remaining; $manifest.launcher = $remainingLauncher; Save-Manifest $manifest }
        else { Remove-Item -LiteralPath $script:ManifestPath -Force }
    }
    exit 0
}

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$UserHome,
    [switch]$Activate,
    [switch]$Rollback,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'CouncilFlow remote updates require PowerShell 7 or later (pwsh). No update was attempted.' }
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot)
$UserHome = [IO.Path]::GetFullPath($UserHome)
$DataRoot = Join-Path $UserHome '.councilflow'
$ManifestPath = Join-Path $DataRoot 'bootstrap.json'
$HistoryPath = Join-Path $DataRoot 'update-history.json'
$LockPath = Join-Path $DataRoot 'remote-update.lock'
$Upstream = 'https://github.com/luvhscupid/CouncilFlow.git'
$script:LockStream = $null
$script:ManagedVersion = $null

function Invoke-Git([string]$WorkingDirectory, [string[]]$Arguments, [switch]$AllowFailure) {
    $previous = Get-Location
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $output = @(& git @Arguments 2>&1)
        $code = $LASTEXITCODE
    } finally { Set-Location $previous }
    if ($code -ne 0 -and -not $AllowFailure) { throw "git $($Arguments -join ' ') failed ($code): $($output -join ' ')" }
    return [pscustomobject]@{ Code=$code; Output=($output -join "`n").Trim() }
}

function Get-FileHashHex([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-TreeHash([string]$Path) {
    $root = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $files = @(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.Extension -ne '.pyc' } | Sort-Object { $_.FullName.Substring($root.Length) })
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
            $line = [Text.Encoding]::UTF8.GetBytes($relative + "`0" + (Get-FileHashHex $file.FullName) + "`n")
            [void]$sha.TransformBlock($line, 0, $line.Length, $line, 0)
        }
        [void]$sha.TransformFinalBlock([byte[]]::new(0),0,0)
        return ([BitConverter]::ToString($sha.Hash)).Replace('-','').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Get-Entries([string]$Root) {
    $items = @(
        [pscustomobject]@{ id='skill'; kind='directory'; source=(Join-Path $Root '.agents\skills\council-flow'); destination=(Join-Path $UserHome '.agents\skills\council-flow') }
    )
    if ((Get-Command claude -ErrorAction SilentlyContinue) -and
        (Test-Path (Join-Path $Root 'plugins\councilflow\.claude-plugin\plugin.json'))) {
        $items += [pscustomobject]@{ id='claude-plugin'; kind='directory'; source=(Join-Path $Root 'plugins\councilflow'); destination=(Join-Path $UserHome '.claude\skills\councilflow') }
    }
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $Root '.codex\agents') -Filter 'council-*.toml' -File) {
        $items += [pscustomobject]@{ id=('role-' + $file.BaseName); kind='file'; source=$file.FullName; destination=(Join-Path $UserHome ('.codex\agents\' + $file.Name)) }
    }
    return $items
}

function Get-InstalledHash($Entry) {
    if ($Entry.kind -eq 'directory') { return Get-TreeHash $Entry.destination }
    return Get-FileHashHex $Entry.destination
}

function Get-LinkTarget([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item -or -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $null }
    if ($item.Target) { return [IO.Path]::GetFullPath($item.Target) }
    return $null
}

function Read-Manifest {
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'CouncilFlow is not installed through this bootstrap; refusing remote activation.' }
    $data = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($data.version -ne 1 -or $data.source -ne $RepoRoot -or -not $data.installs.Count) { throw 'Bootstrap manifest is not recognized or has no managed installations.' }
    foreach ($field in @('active_source','active_commit','previous_source','previous_commit','update_result')) {
        if (-not $data.PSObject.Properties[$field]) { $data | Add-Member -MemberType NoteProperty -Name $field -Value $null }
    }
    $launcher = @($data.launcher | Where-Object name -eq 'remote-update.ps1' | Select-Object -First 1)
    if ($launcher.Count -and [IO.Path]::GetFullPath($PSCommandPath) -eq [IO.Path]::GetFullPath($launcher[0].destination)) {
        if ((Get-FileHashHex $PSCommandPath) -ne $launcher[0].installed_hash) { throw 'Managed updater was modified; scheduled update refused.' }
    }
    return $data
}

function Write-History([string]$Result, [string]$Commit, [string]$Detail) {
    $entry = [pscustomobject]@{ time_utc=[DateTime]::UtcNow.ToString('o'); upstream=$Upstream; branch='main'; commit=$Commit; result=$Result; detail=$Detail }
    $history = @()
    if (Test-Path -LiteralPath $HistoryPath) { $history = @(Get-Content -LiteralPath $HistoryPath -Raw | ConvertFrom-Json) }
    $history = @($entry) + $history | Select-Object -First 50
    if (-not $DryRun) { $history | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $HistoryPath -Encoding utf8 }
    return $entry
}

function Test-OwnedInstall($Manifest) {
    $entries = @(Get-Entries $Manifest.active_source)
    foreach ($entry in $entries) {
        $record = $Manifest.installs | Where-Object id -eq $entry.id | Select-Object -First 1
        if (-not $record -or -not (Test-Path -LiteralPath $entry.destination)) { throw "Installation is incomplete at $($entry.destination)." }
        if ($record.mode -eq 'link') {
            $target = Get-LinkTarget $entry.destination
            if (-not $target -or $target -ne [IO.Path]::GetFullPath($record.source)) { throw "Managed link was changed or replaced: $($entry.destination) (target='$target'; expected='$($record.source)')" }
        } elseif ($record.mode -eq 'copy') {
            if ((Get-InstalledHash $entry) -ne $record.installed_hash) { throw "Managed copy was modified; refusing update: $($entry.destination)" }
        } else { throw "Unknown managed installation mode at $($entry.destination)." }
    }
    if ($Manifest.installs.Count -ne $entries.Count) { throw 'Managed installation set differs from current role/package inventory.' }
}

function Get-RemoteCommit {
    $lines = (Invoke-Git $UserHome @('ls-remote','--symref',$Upstream,'HEAD','refs/heads/main')).Output -split "`n"
    $head = $lines | Where-Object { $_ -match '^ref: refs/heads/([^ ]+)\s+HEAD$' } | Select-Object -First 1
    if (-not $head -or $head -notmatch 'refs/heads/main') { throw 'Upstream default branch is not the pinned main branch.' }
    $commitLine = $lines | Where-Object { $_ -match '^[0-9a-f]{40,64}\s+refs/heads/main$' } | Select-Object -First 1
    if (-not $commitLine) { throw 'Pinned upstream branch main is missing or unreadable.' }
    return ($commitLine -split '\s+')[0]
}

function Test-Candidate([string]$Path, [string]$ExpectedCommit) {
    $branch = (Invoke-Git $Path @('branch','--show-current')).Output
    if ($branch -ne 'main') { throw "Candidate branch changed unexpectedly: $branch" }
    $origin = (Invoke-Git $Path @('remote','get-url','origin')).Output.TrimEnd('/')
    if ($origin -ne $Upstream.TrimEnd('/')) { throw 'Candidate origin does not match the configured CouncilFlow upstream.' }
    $commit = (Invoke-Git $Path @('rev-parse','HEAD')).Output
    if ($commit -ne $ExpectedCommit) { throw 'Fetched commit does not match the verified upstream main commit.' }
    $clean = (Invoke-Git $Path @('status','--porcelain','--untracked-files=all')).Output
    if ($clean) { throw 'Candidate managed checkout is dirty; activation refused.' }
    if (-not (Test-Path (Join-Path $Path '.agents\skills\council-flow\SKILL.md')) -or
        -not (Test-Path (Join-Path $Path '.agents\skills\council-flow\scripts\planner_contract.py'))) {
        throw 'Candidate lacks the installed CouncilFlow Planner package.'
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Python is required to validate a remote candidate.' }
    $old = Get-Location
    try { Set-Location -LiteralPath $Path; $test = @(& $python.Source -m unittest tests.test_skill_files tests.test_contracts tests.test_dispatch_lifecycle tests.test_planner_contract -q 2>&1); $testCode = $LASTEXITCODE }
    finally { Set-Location $old }
    if ($testCode -ne 0) { throw "Candidate validation failed: $($test -join ' ')" }
    if ((Get-Command claude -ErrorAction SilentlyContinue) -and
        (Test-Path (Join-Path $Path 'plugins\councilflow\.claude-plugin\plugin.json'))) {
        $validation = @(& claude plugin validate (Join-Path $Path 'plugins\councilflow') 2>&1)
        if ($LASTEXITCODE -ne 0) { throw "Claude package validation failed: $($validation -join ' ')" }
    }
    return $commit
}

function New-Snapshot([string]$Root, [string]$Commit) {
    $safe = if ($Commit) { $Commit.Substring(0,[Math]::Min(12,$Commit.Length)) } else { 'unknown' }
    $snapshot = Join-Path (Join-Path $DataRoot 'versions') ("rollback-$safe-" + [Guid]::NewGuid().ToString('N'))
    foreach ($relative in @('.agents\skills\council-flow','.codex\agents','plugins\councilflow')) {
        $src = Join-Path $Root $relative
        if (-not (Test-Path -LiteralPath $src)) { continue }
        $dst = Join-Path $snapshot $relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Recurse
    }
    return $snapshot
}

function New-StagedEntry($Entry, [string]$Id) {
    $parent = Split-Path -Parent $Entry.destination
    $temp = Join-Path $parent ('.councilflow-next-' + $Id)
    $backup = Join-Path $parent ('.councilflow-previous-' + $Id)
    if (Test-Path $temp) { throw "Temporary path already exists: $temp" }
    if (Test-Path $backup) { throw "Rollback path already exists: $backup" }
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $mode = 'link'
    try {
        if ($Entry.kind -eq 'directory') { New-Item -ItemType Junction -Path $temp -Target $Entry.source | Out-Null }
        else { New-Item -ItemType SymbolicLink -Path $temp -Target $Entry.source | Out-Null }
    } catch {
        $mode = 'copy'
        if ($Entry.kind -eq 'directory') { Copy-Item -LiteralPath $Entry.source -Destination $temp -Recurse }
        else { Copy-Item -LiteralPath $Entry.source -Destination $temp }
    }
    return [pscustomobject]@{ Entry=$Entry; Temp=$temp; Backup=$backup; Mode=$mode }
}

function Remove-Path([string]$Path, [string]$Kind) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($Kind -eq 'directory') {
        if ((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($Path,$false) }
        else { Remove-Item -LiteralPath $Path -Recurse -Force }
    } else { Remove-Item -LiteralPath $Path -Force }
}

function Activate-Source([string]$SourceRoot, [string]$Commit, $Manifest) {
    Test-OwnedInstall $Manifest
    $oldSource = $Manifest.active_source
    $oldCommit = $Manifest.active_commit
    $newEntries = @(Get-Entries $SourceRoot)
    $managedInventory = @($Manifest.installs | ForEach-Object {
        '{0}|{1}|{2}' -f $_.id, $_.kind, [IO.Path]::GetFullPath($_.destination)
    } | Sort-Object)
    $candidateInventory = @($newEntries | ForEach-Object {
        '{0}|{1}|{2}' -f $_.id, $_.kind, [IO.Path]::GetFullPath($_.destination)
    } | Sort-Object)
    if ([string]::Join("`n", $managedInventory) -ne [string]::Join("`n", $candidateInventory)) {
        throw 'Candidate installation inventory differs from the managed installation; refusing to add, remove, or replace destinations.'
    }
    if ($oldSource -eq $RepoRoot) { $oldSource = New-Snapshot $oldSource $oldCommit }
    if ($DryRun) {
        foreach ($entry in $newEntries) { Write-Host "DRY-RUN replace $($entry.destination) with $($entry.source)" }
        return
    }
    $staged = @()
    $swapped = @()
    $committed = $false
    $manifestBackup = $ManifestPath + '.previous'
    try {
        foreach ($entry in $newEntries) { $staged += New-StagedEntry $entry ([Guid]::NewGuid().ToString('N')) }
        foreach ($item in $staged) {
            Move-Item -LiteralPath $item.Entry.destination -Destination $item.Backup
            try { Move-Item -LiteralPath $item.Temp -Destination $item.Entry.destination }
            catch { Move-Item -LiteralPath $item.Backup -Destination $item.Entry.destination; throw }
            $swapped += $item
        }
        $Manifest.previous_source = $oldSource
        $Manifest.previous_commit = $oldCommit
        $Manifest.active_source = $SourceRoot
        $Manifest.active_commit = $Commit
        $updatedRecords = @()
        foreach ($item in $staged) {
            $sourceHash = if ($item.Entry.kind -eq 'directory') { Get-TreeHash $item.Entry.source } else { Get-FileHashHex $item.Entry.source }
            $installedHash = if ($item.Mode -eq 'copy') { Get-InstalledHash $item.Entry } else { $null }
            $updatedRecords += [pscustomobject]@{ id=$item.Entry.id; kind=$item.Entry.kind; source=$item.Entry.source; destination=$item.Entry.destination; mode=$item.Mode; source_hash=$sourceHash; installed_hash=$installedHash }
        }
        $Manifest.installs = $updatedRecords
        $Manifest.update_result = 'activated'
        $tmpManifest = $ManifestPath + '.next'
        $Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $tmpManifest -Encoding utf8
        if (Test-Path $manifestBackup) { throw "Manifest rollback path already exists: $manifestBackup" }
        Move-Item -LiteralPath $ManifestPath -Destination $manifestBackup
        try { Move-Item -LiteralPath $tmpManifest -Destination $ManifestPath }
        catch { Move-Item -LiteralPath $manifestBackup -Destination $ManifestPath; throw }
        $committed = $true
        foreach ($item in $staged) { try { Remove-Path $item.Backup $item.Entry.kind } catch { Write-Warning "Kept recovery path $($item.Backup): $($_.Exception.Message)" } }
        Remove-Item -LiteralPath $manifestBackup -Force -ErrorAction SilentlyContinue
    } catch {
        if (-not $committed) {
            for ($index = $swapped.Count - 1; $index -ge 0; $index--) {
                $item = $swapped[$index]
                Remove-Path $item.Entry.destination $item.Entry.kind
                if (Test-Path $item.Backup) { Move-Item -LiteralPath $item.Backup -Destination $item.Entry.destination }
            }
            if ((Test-Path $manifestBackup) -and -not (Test-Path $ManifestPath)) { Move-Item -LiteralPath $manifestBackup -Destination $ManifestPath }
        }
        foreach ($item in $staged) { Remove-Path $item.Temp $item.Entry.kind }
        throw
    }
}

try {
    New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
    try { $script:LockStream = [IO.File]::Open($LockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None) }
    catch { throw 'Another CouncilFlow remote update is running (or a stale lock needs manual review).' }
    if (-not $Activate -and -not $Rollback) {
        $commit = Get-RemoteCommit
        Write-Host "Upstream: $Upstream`nBranch: main`nCandidate commit: $commit"
        Write-History 'checked' $commit 'pinned main branch checked; no activation'
        exit 0
    }
    $manifest = Read-Manifest

    if ($Rollback) {
        if (-not $manifest.previous_source -or -not (Test-Path $manifest.previous_source)) { throw 'No preserved previous version is available.' }
        $previous = $manifest.previous_source
        if (-not (Test-Path (Join-Path $previous '.agents\skills\council-flow\SKILL.md'))) { throw 'Preserved rollback source is incomplete.' }
        if ($DryRun) { Write-Host "DRY-RUN validate and restore $previous"; exit 0 }
        Activate-Source $previous $manifest.previous_commit $manifest
        Write-History 'rolled_back' $manifest.active_commit "restored $previous"
        exit 0
    }

    $versions = Join-Path $DataRoot 'versions'
    $staging = Join-Path $DataRoot 'staging'
    New-Item -ItemType Directory -Force -Path $versions,$staging | Out-Null
    $commit = Get-RemoteCommit
    $current = $manifest.active_commit
    if ($current -eq $commit -and $manifest.active_source -ne $RepoRoot) {
        if (Test-Path (Join-Path $manifest.active_source '.git')) {
            $branchNow = (Invoke-Git $manifest.active_source @('branch','--show-current')).Output
            $headNow = (Invoke-Git $manifest.active_source @('rev-parse','HEAD')).Output
            $dirtyNow = (Invoke-Git $manifest.active_source @('status','--porcelain','--untracked-files=all')).Output
            if ($branchNow -ne 'main' -or $headNow -ne $commit -or $dirtyNow) { throw 'Installed managed checkout changed; refusing to treat it as current.' }
        }
        Write-History 'current' $commit 'installed version already matches verified upstream main'
        Write-Host "Already current at $commit"
        exit 0
    }
    $candidate = Join-Path $versions $commit
    $stage = Join-Path $staging ($commit + '-' + [Guid]::NewGuid().ToString('N'))
    if ($manifest.active_source -ne $RepoRoot -and (Test-Path (Join-Path $manifest.active_source '.git'))) {
        $dirty = (Invoke-Git $manifest.active_source @('status','--porcelain','--untracked-files=all')).Output
        if ($dirty) { throw 'Active managed checkout is dirty; remote activation refused.' }
    }
    if (-not (Test-Path $candidate)) {
        $clone = Invoke-Git $staging @('clone','--no-hardlinks','--branch','main','--single-branch',$Upstream,$stage)
        $null = $clone
    }
    if (-not (Test-Path $candidate)) { $candidate = $stage }
    $verified = Test-Candidate $candidate $commit
    if ($current -and $current -ne $commit) {
        $ancestor = Invoke-Git $candidate @('merge-base','--is-ancestor',$current,$commit) -AllowFailure
        if ($ancestor.Code -ne 0) { throw 'Candidate is not a fast-forward of the installed version.' }
    }
    if ((Get-RemoteCommit) -ne $commit) { throw 'Upstream main changed during validation; no activation performed.' }
    Write-History 'validated' $commit 'candidate passed branch, origin, fast-forward, checkout, and deterministic test checks'
    if ($DryRun) { Write-Host "DRY-RUN activate verified main commit $commit from $candidate"; exit 0 }
    if ($candidate -eq $stage) { Move-Item -LiteralPath $stage -Destination (Join-Path $versions $commit); $candidate = Join-Path $versions $commit }
    Activate-Source $candidate $verified $manifest
    Write-History 'activated' $commit "active source $candidate"
} catch {
    try { Write-History 'failed' $null $_.Exception.Message | Out-Null } catch { }
    Write-Error $_
    exit 1
} finally {
    if ($script:LockStream) { $script:LockStream.Dispose(); Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue }
}

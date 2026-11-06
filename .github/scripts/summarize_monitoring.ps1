param([string]$LogPath, [string]$OutputDirectory)
$records = @()
if (Test-Path $LogPath) { $records = @(Get-Content $LogPath -Encoding UTF8 | Where-Object {$_.Trim()} | ForEach-Object { $_ | ConvertFrom-Json }) }
$ordered = @($records | Sort-Object request_start_utc)
$gaps = @()
for($i=1; $i -lt $ordered.Count; $i++){ $gaps += (([DateTime]$ordered[$i].request_start_utc)-([DateTime]$ordered[$i-1].request_start_utc)).TotalSeconds }
$phases = @('pre','deploying','post')
$lines = @('# Deployment monitoring summary','', '| Item | Result |','|---|---:|')
$lines += "| Service | http://127.0.0.1:8000/api/predict |"
$startTime = if($ordered.Count){$ordered[0].request_start_utc}else{'UNVERIFIED'}; $endTime = if($ordered.Count){$ordered[-1].request_end_utc}else{'UNVERIFIED'}
$lines += "| Monitoring start | $startTime |"; $lines += "| Monitoring end | $endTime |"
$successCount=@($ordered|Where-Object {$_.success -eq $true}).Count; $failedCount=@($ordered|Where-Object {$_.success -ne $true}).Count; $httpErrorCount=@($ordered|Where-Object {$_.status_code -lt 200 -or $_.status_code -ge 300}).Count
$lines += "| Total requests | $($ordered.Count) |"; $lines += "| Successful | $successCount |"; $lines += "| Failed | $failedCount |"
$lines += "| HTTP errors | $httpErrorCount |"; $lines += "| Max response ms | $(if($ordered){[math]::Round((($ordered | Measure-Object duration_ms -Maximum).Maximum),2)}else{0}) |"
$lines += "| Max request gap s | $(if($gaps){[math]::Round(($gaps | Measure-Object -Maximum).Maximum,2)}else{0}) |"
foreach($phase in $phases){$r=@($ordered|Where-Object phase -eq $phase);$one=$r|Select-Object -First 1;if($one){$representative="status $($one.status_code), model $($one.model_version), $($one.duration_ms)ms"}else{$representative='UNVERIFIED'};$lines += "| $phase requests | $($r.Count) (success $(@($r|Where-Object {$_.success -eq $true}).Count); $representative) |"}
$versions=@($ordered|Where-Object model_version|Select-Object -ExpandProperty model_version -Unique)
$lines += "| Model versions observed | $($versions -join ', ') |"; $lines += "| Observed-range no-gap result | $(if($ordered.Count -gt 0 -and (($ordered|Where-Object {-not $_.success}).Count -eq 0)){'PASS'}else{'FAIL/UNVERIFIED'}) |"
$lines += ''; $lines += 'No absolute zero-downtime guarantee is claimed; this result applies only to the recorded request window.'
New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
$lines | Set-Content (Join-Path $OutputDirectory 'summary.md') -Encoding UTF8
$summary=[ordered]@{service='http://127.0.0.1:8000/api/predict'; total_requests=$ordered.Count; successful=$successCount; failed=$failedCount; http_errors=$httpErrorCount; max_response_ms=$(if($ordered){[math]::Round((($ordered|Measure-Object duration_ms -Maximum).Maximum),2)}else{0}); max_gap_seconds=$(if($gaps){[math]::Round(($gaps|Measure-Object -Maximum).Maximum,2)}else{0}); model_versions=$versions; phases=$phases}
$summary | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $OutputDirectory 'summary.json') -Encoding UTF8

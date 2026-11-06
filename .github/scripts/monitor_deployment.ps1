param(
  [string]$BaseUrl,
  [string]$LogPath,
  [string]$PhasePath,
  [string]$StopPath
)
$ErrorActionPreference = 'SilentlyContinue'
$messages = @(
  '[SPAM] Free coupon event. Click the link to claim now.',
  '[NORMAL] The team meeting is scheduled for 10 PM today.',
  '[SPAM] Urgent loan approval. Contact us for a free consultation.',
  '[NORMAL] Your parcel has arrived. Please check the front door.'
)
$index = 0
while (-not (Test-Path $StopPath)) {
  $phase = if (Test-Path $PhasePath) { (Get-Content $PhasePath -Raw).Trim() } else { 'unknown' }
  $text = $messages[$index % $messages.Count]; $index++
  $start = [DateTime]::UtcNow
  $status = 0; $success = $false; $version = $null; $requestError = $null; $returned = $false
  try {
    $body = @{text=$text} | ConvertTo-Json -Compress
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
    $response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$BaseUrl/api/predict" -ContentType 'application/json; charset=utf-8' -Body $bodyBytes -TimeoutSec 5
    $status = [int]$response.StatusCode
    $data = $response.Content | ConvertFrom-Json
    $version = $data.model_version; $returned = ($null -ne $data.label -and $null -ne $data.score); $success = ($status -eq 200 -and $returned)
  } catch {
    $requestError = $_.Exception.Message
    if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
  }
  $end = [DateTime]::UtcNow
  $record = [ordered]@{request_start_utc=$start.ToString('o'); request_end_utc=$end.ToString('o'); duration_ms=[math]::Round(($end-$start).TotalMilliseconds,2); status_code=$status; success=$success; response_shape_valid=$returned; model_version=$version; phase=$phase; text=$text; error=$requestError}
  ($record | ConvertTo-Json -Compress) | Add-Content -Path $LogPath -Encoding UTF8
  Start-Sleep -Seconds 1
}

param(
  [string]$To,
  [string]$Cc,
  [string]$Bcc,
  [string]$Subject,
  [string]$Body
)

function Encode([string]$s) {
  if ([string]::IsNullOrEmpty($s)) { return "" }
  [System.Uri]::EscapeDataString($s)
}

function Normalize([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return "" }
  ($s -split ',' | % { $_.Trim() }) -join ','
}

$stdinJson = $null
try {
  $raw = [Console]::In.ReadToEnd()
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    $stdinJson = $raw | ConvertFrom-Json -ErrorAction Stop
  }
} catch {}

if ($stdinJson) {
  $To      = $stdinJson.to
  $Cc      = $stdinJson.cc
  $Bcc     = $stdinJson.bcc
  $Subject = $stdinJson.subject
  $Body    = $stdinJson.body
}

if (-not $Subject) { $Subject = "Quick demo from Rose — autonomous email draft" }
if (-not $Body) {
  $Body = "Hi there,`r`n`r`nThis is a quick demo drafted autonomously by Rose.`r`n— Rose"
}

$To  = Normalize $To
$Cc  = Normalize $Cc
$Bcc = Normalize $Bcc
$Body = $Body -replace "`r?`n","`r`n"

$base = "https://outlook.office.com/?path=/mail/action/compose"
$q = @()
if ($To)  { $q += "to=$(Encode $To)" }
if ($Cc)  { $q += "cc=$(Encode $Cc)" }
if ($Bcc) { $q += "bcc=$(Encode $Bcc)" }
$q += "subject=$(Encode $Subject)"
$q += "body=$(Encode $Body)"

$url = $base + "&" + ($q -join "&")

Start-Process $url | Out-Null
@{ mission="draft_email_web"; status="launched"; url=$url } | ConvertTo-Json -Compress | Write-Output
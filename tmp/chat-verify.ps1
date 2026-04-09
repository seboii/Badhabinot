$ErrorActionPreference = "Stop"

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $params = @{ Method = $Method; Uri = $Url; Headers = $Headers }
    if ($null -ne $Body) {
        $params['ContentType'] = 'application/json'
        $params['Body'] = ($Body | ConvertTo-Json -Depth 10)
    }

    try {
        return Invoke-RestMethod @params
    } catch {
        $response = $_.Exception.Response
        if ($null -eq $response) { throw }
        $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
        $bodyText = $reader.ReadToEnd()
        throw "HTTP $($response.StatusCode.value__) $Method $Url failed. Response: $bodyText"
    }
}

$gateway = "http://localhost:8080"
$user1Email = "chat.user1@badhabinot.local"
$user2Email = "chat.user2@badhabinot.local"
$pwd = "Badhabinot!2026"

function Get-Token([string]$email,[string]$displayName){
    try {
        $resp = Invoke-JsonRequest -Method Post -Url "$gateway/api/v1/auth/register" -Body @{ email=$email; password=$pwd; display_name=$displayName; timezone="Europe/Istanbul"; locale="tr-TR" }
        return $resp.access_token
    } catch {
        $resp = Invoke-JsonRequest -Method Post -Url "$gateway/api/v1/auth/login" -Body @{ email=$email; password=$pwd }
        return $resp.access_token
    }
}

$token1 = Get-Token $user1Email "Chat User 1"
$token2 = Get-Token $user2Email "Chat User 2"

$h1 = @{ Authorization = "Bearer $token1" }
$h2 = @{ Authorization = "Bearer $token2" }

$first = Invoke-JsonRequest -Method Post -Url "$gateway/api/v1/monitoring/chat" -Headers $h1 -Body @{ conversation_id=""; message="Summarize my day briefly." }
$second = Invoke-JsonRequest -Method Post -Url "$gateway/api/v1/monitoring/chat" -Headers $h1 -Body @{ conversation_id=$first.conversation_id; message="Any follow-up suggestion?" }
$history = Invoke-RestMethod -Method Get -Uri "$gateway/api/v1/monitoring/chat/history?conversation_id=$($first.conversation_id)&limit=20" -Headers $h1

$crossUserCheck = "FAILED"
try {
    [void](Invoke-RestMethod -Method Get -Uri "$gateway/api/v1/monitoring/chat/history?conversation_id=$($first.conversation_id)&limit=20" -Headers $h2)
    $crossUserCheck = "FAILED: cross-user access unexpectedly succeeded"
} catch {
    $crossUserCheck = $_.Exception.Message
}

$result = [PSCustomObject]@{
    conversation_id = $first.conversation_id
    first_answer_present = [bool]$first.answer
    second_answer_present = [bool]$second.answer
    history_message_count = @($history.messages).Count
    history_has_assistant = [bool](@($history.messages | Where-Object { $_.role -eq "assistant" }).Count -gt 0)
    cross_user_check = $crossUserCheck
}

$result | ConvertTo-Json -Depth 5

param(
    [string]$GatewayBaseUrl = "http://localhost:8080",
    [string]$Email = "demo.user@badhabinot.local",
    [string]$Password = "Badhabinot!2026",
    [string]$DisplayName = "Demo User"
)

$ErrorActionPreference = "Stop"
$sampleFrameScript = Join-Path $PSScriptRoot "generate_sample_frame.py"

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $params = @{
        Method = $Method
        Uri = $Url
        Headers = $Headers
    }

    if ($null -ne $Body) {
        $params["ContentType"] = "application/json"
        $params["Body"] = ($Body | ConvertTo-Json -Depth 8)
    }

    try {
        return Invoke-RestMethod @params
    }
    catch {
        $response = $_.Exception.Response
        if ($null -eq $response) {
            throw
        }

        $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        throw "HTTP $($response.StatusCode.value__) $Method $Url failed. Response: $responseBody"
    }
}

Write-Host "Checking public health endpoints..."
$gatewayHealth = Invoke-RestMethod -Method Get -Uri "$GatewayBaseUrl/actuator/health"
if ($gatewayHealth.status -ne "UP") {
    throw "Gateway is not healthy."
}

$sampleFrame = python $sampleFrameScript | ConvertFrom-Json

Write-Host "Registering or logging in demo user..."
$authPayload = @{
    email = $Email
    password = $Password
}

try {
    $tokenResponse = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/auth/register" -Body @{
        email = $Email
        password = $Password
        display_name = $DisplayName
        timezone = "Europe/Istanbul"
        locale = "tr-TR"
    }
}
catch {
    $tokenResponse = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/auth/login" -Body $authPayload
}

$headers = @{
    Authorization = "Bearer $($tokenResponse.access_token)"
}

Write-Host "Applying consent and settings..."
[void](Invoke-JsonRequest -Method Put -Url "$GatewayBaseUrl/api/v1/users/me/consents" -Headers $headers -Body @{
    privacy_policy_accepted = $true
    camera_monitoring_accepted = $true
    remote_inference_accepted = $true
})

[void](Invoke-JsonRequest -Method Put -Url "$GatewayBaseUrl/api/v1/users/me/settings" -Headers $headers -Body @{
    sensitivity = "MEDIUM"
    water_goal_ml = 2500
    water_interval_min = 60
    exercise_interval_min = 60
    quiet_hours_enabled = $false
    quiet_hours_start = "22:00"
    quiet_hours_end = "08:00"
    model_mode = "API"
    notifications_enabled = $true
})

Write-Host "Starting session..."
$session = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/monitoring/sessions/start" -Headers $headers -Body @{
    client_surface = "desktop"
    device_type = "laptop"
}

Write-Host "Logging hydration..."
$hydration = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/monitoring/hydration/log" -Headers $headers -Body @{
    amount_ml = 250
    source = "smoke_test"
    session_id = $session.session_id
}

Write-Host "Sending sample analysis frame..."
$analysis = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/monitoring/analyze" -Headers $headers -Body @{
    session_id = $session.session_id
    frame_id = "smoke-frame-001"
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    image_base64 = $sampleFrame.image_base64
    image_content_type = $sampleFrame.image_content_type
}

Write-Host "Fetching dashboard..."
$dashboard = Invoke-RestMethod -Method Get -Uri "$GatewayBaseUrl/api/v1/monitoring/dashboard" -Headers $headers

Write-Host "Fetching events..."
$events = Invoke-RestMethod -Method Get -Uri "$GatewayBaseUrl/api/v1/monitoring/events?limit=5" -Headers $headers

Write-Host "Fetching daily report..."
$report = Invoke-RestMethod -Method Get -Uri "$GatewayBaseUrl/api/v1/monitoring/reports/daily" -Headers $headers

Write-Host "Querying grounded chat..."
$chat = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/monitoring/chat" -Headers $headers -Body @{
    conversation_id = ""
    message = "Summarize my hydration and whether any risky behavior was detected today."
}

Write-Host "Stopping session..."
$stopped = Invoke-JsonRequest -Method Post -Url "$GatewayBaseUrl/api/v1/monitoring/sessions/$($session.session_id)/stop" -Headers $headers

[PSCustomObject]@{
    user_email = $Email
    session_id = $session.session_id
    analysis_id = $analysis.analysis_id
    behavior_type = $analysis.behavior_type
    posture_state = $analysis.posture_state
    hydration_amount_ml = $hydration.amount_ml
    event_count = @($events).Count
    report_date = $report.report_date
    report_analyses_completed = $report.analyses_completed
    report_hydration_progress_ml = $report.hydration_progress_ml
    chat_answer = $chat.answer
    dashboard_monitoring_active = $dashboard.monitoring_active
    stopped_status = $stopped.status
} | Format-List

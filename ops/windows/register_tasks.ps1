param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path
)

function Convert-ToDateTime {
    param([Parameter(Mandatory=$true)][string]$TimeText)
    # Accept "8:00pm" / "08:00 PM" / "20:00"
    $styles = @('h:mmtt','hh:mm tt','H:mm')
    foreach ($fmt in $styles) {
        try { return [datetime]::ParseExact($TimeText, $fmt, $null) } catch {}
    }
    throw "Cannot parse time '$TimeText'. Try '8:00pm' or '20:00'."
}

function Register-RoseMissionTask {
    param(
        [Parameter(Mandatory=$true)][string]$TaskName,
        [Parameter(Mandatory=$true)][string]$MissionRelPath,
        [ValidateSet("Daily","Weekly")][string]$ScheduleType,
        [Parameter(Mandatory=$true)][string]$AtTime,
        [string[]]$DaysOfWeek
    )

    $At = Convert-ToDateTime -TimeText $AtTime

    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -NoProfile -File `"$RepoRoot\ops\windows\run_mission.ps1`" -MissionPath `"$RepoRoot\$MissionRelPath`""

    if ($ScheduleType -eq "Weekly") {
        if (-not $DaysOfWeek) { throw "Weekly schedule requires -DaysOfWeek" }
        $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DaysOfWeek -At $At
    } else {
        $Trigger = New-ScheduledTaskTrigger -Daily -At $At
    }

    # PS 5.1: use LogonType Interactive (NOT InteractiveToken)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:UserName -RunLevel Highest -LogonType Interactive

    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -Compatibility Win8

    $Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings

    Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
    Write-Host "Registered task: $TaskName"
}

# Example tasks (edit times as you like)
Register-RoseMissionTask -TaskName "Rose_Inbox_Triage" -MissionRelPath "ops\missions\inbox_triage.yml" -ScheduleType "Weekly" -AtTime "8:00am" -DaysOfWeek Wednesday
Register-RoseMissionTask -TaskName "Rose_File_Cabinet" -MissionRelPath "ops\missions\file_cabinet.yml" -ScheduleType "Daily" -AtTime "7:00am"
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path   
)

function Register-RoseMissionTask {
    param(
        [Parameter(Mandatory=$true)][string]$TaskName,
        [Parameter(Mandatory=$true)][string]$MissionRelPath,
        [Parameter(Mandatory=$true)][string]$ScheduleType, # Daily | Weekly
        [Parameter(Mandatory=$true)][string]$AtTime, # "HH:mm (ex. 8:00pm)"
        [string[]]$DaysOfWeek
    )

    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$RepoRoot\ops\windows\run_mission.ps1`" -MissionPath `"$RepoRoot\$MissionRelPath`""
    

    if ($ScheduleType -eq "Weekly") {
        $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DaysOfWeek -At $AtTime
    } else {
        $Trigger = New-ScheduledTaskTrigger -Daily -At %$AtTime
    }
    
    $Principal = New-ScheduledTaskPrincipal -UserId $env:UserName -RunLevel Highest -LogonType InteractiveToken

    $Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Compatibility Win8)

    Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
    Write-Host "Registered task: $TaskName"
}

# Example Registered Tasks
Register-RoseMissionTask -TaskName "Rose_Inbox_Triage" -MissionRelPath "ops\missions\inbox_triage.yml" -ScheduleType "Weekly" -AtTime "8:00am" -DaysOfWeek Wednesday
Register-RoseMissionTask -TaskName "Rose_File_Cabinet" -MissionRelPath "ops\missions\file_cabinet.yml" -ScheduleType "Daily" -AtTime "9:00am"
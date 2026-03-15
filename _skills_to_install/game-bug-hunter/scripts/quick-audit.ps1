param(
    [string]$Root = "."
)

$patterns = @(
    "scene",
    "mode_name",
    "return_scene",
    "cooldown",
    "card_timer",
    "plant_select",
    "restart",
    "result",
    "pause",
    "open_battle_menu",
    "imitater",
    "potato"
)

foreach ($p in $patterns) {
    Write-Host "==== pattern: $p ===="
    rg -n $p $Root
}


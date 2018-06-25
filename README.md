# SteamDustman
Removes hidden games from your Steam account.  

This is particularly useful if you are like me and used to hoard giveaways, and have since realized how *pointless* that was.  
However, you do need to have [hidden](https://www.reddit.com/r/pcmasterrace/comments/6k0v3i/tip_hide_games_in_your_steam_library/) those games in your library.

## Dependencies / What You Need
- `sharedconfig.vdf`: this is the file Steam uses to store your categories and can be found at `$STEAM/userdata/$UID/7/remote/sharedconfig.vdf`, where $STEAM is the Steam install directory and $UID is your numeric Steam user ID [[1]](https://gaming.stackexchange.com/a/131804)
- `SteamCMD`: this is Valve's command-line Steam [client](https://developer.valvesoftware.com/wiki/SteamCMD)
- `Python 3` and `pip3`
- The excellent `Requests` [package](http://docs.python-requests.org/en/master/), which deals with HTTP requests
- The `vdf` [package](https://github.com/ValvePython/vdf), which deals with Valve's `*.vdf` files

Now, launch `SteamCMD` and generate a file containing all your licenses on Steam by:  
`$ steamcmd +login USERNAME +licenses_print +quit > licenses.txt`  
or:  
`$ ./steamcmd.sh +login USERNAME +licenses_print +quit > licenses.txt`  

Log in to https://help.steampowered.com/ and use your browser's [developer](https://developer.mozilla.org/en-US/docs/Tools/Storage_Inspector#Cookies) [tools](https://developers.google.com/web/tools/chrome-devtools/manage-data/cookies) to find the values to the following cookies names:
- `sessionid`
- `steamLogin`
- `steamLoginSecure`

Finally,  
`$ python3 Dustman.py <path_to_sharedconfig_vdf> <steam_lib_licenses_file> <sessionid> <steam_login> <steam_login_secure>`  
and your hidden games will be gone.

## Logging
A log will be generated at `dustman.log` in your current directory. Among other things, it records all the removed packages with more than one apps.

## Restoring
If, for any reason, you need to recover a removed app, you can do so at:  
`https://help.steampowered.com/en/wizard/HelpWithGame/?appid=<your_appid>`

## Limitation
As far as I know, you can only remove an entire package (which may contain multiple apps) at a time on the Steam help center. And since that's how this script removes games, you cannot cherrypick individual apps from a package for removal. Also, given this limitation, this script will not remove packages that contain both hidden and visible games.

## Warnings
Be aware that I make no promises that this script would work correctly, now or in the future. It is entirely possible that there are cases with all these undocumented resources that I have not encountered during development and failed to account for. And Valve could decide to modify the behavior of their remove-game endpoint.

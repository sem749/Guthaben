@echo off
rem Startet WebDriverAgent auf dem iPhone und leitet Port 8100 an den PC weiter.
rem Fenster offen lassen, solange der Bot laufen soll.
rem WDA_BUNDLE anpassen, falls "ios apps" eine andere Bundle-ID zeigt.
set WDA_BUNDLE=com.facebook.WebDriverAgentRunner.xctrunner

where ios >nul 2>nul || (echo go-ios ^(ios.exe^) nicht gefunden - siehe ANLEITUNG.md, Schritt 2 & pause & exit /b 1)

echo Entwickler-Image einbinden ...
ios image auto

echo Tunnel fuer iOS 17+ starten (bei aelteren iOS-Versionen egal) ...
start "iOS-Tunnel" ios tunnel start --userspace
timeout /t 5 >nul

echo WebDriverAgent starten ...
start "WebDriverAgent" ios runwda --bundleid=%WDA_BUNDLE% --testrunnerbundleid=%WDA_BUNDLE% --xctestconfig=WebDriverAgentRunner.xctest
timeout /t 8 >nul

echo Port 8100 weiterleiten. Jetzt in einem zweiten Fenster: python bot.py verbindung
ios forward 8100 8100

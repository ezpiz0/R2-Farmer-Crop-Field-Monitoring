@echo off
chcp 65001 > nul
echo ====================================
echo Pushing to GitHub
echo ====================================
echo.

echo [1/4] Checking git status...
git status

echo.
echo [2/4] Adding all changes...
git add .

echo.
echo [3/4] Creating commit...
git commit -m "feat: Complete project update - Added AI Agronomist, Dashboard, Field Management, Zoning, Enhanced UI/UX, Updated comprehensive README with all features"

echo.
echo [4/4] Pushing to GitHub...
git push origin main

echo.
echo ====================================
echo Done!
echo ====================================
pause


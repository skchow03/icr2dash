ICR2DASH - Cockpit Overlay for Papyrus IndyCar Racing 2
Enhance your ICR2 gaming experience with ICR2DASH, an interactive dashboard overlay tool for ICR2, designed to work with DOSBox and Windy. It read real-time game data from the default cockpit view and draws a 1980s style analog dashboard to improve immersion when simulating the 1980s.

Version 3.4 - September 10, 2025
Version 3.3 - September 9, 2025
Version 3.1 - June 21, 2025
Version 2.0 - June 24, 2024

Compatibility: Tested on Windows 10 with ICR2 running in windowed mode in DOSBox ECE and DOSBox Staging. Version 3.1 added Dosbox-Rendition support.

For Rendition, if you have an Nvidia card, please set OpenGL GLI Compatibility to "Prefer compatible" and Vulkan/OpenGL Present to "Prefer layered on DXGI swap"

System Requirements
DOS version of ICR2 (INDYCAR.EXE or CART.EXE) running in windowed mode on DOSBox ECE or DOSBox Staging (other DOSBox versions have not been tested)
or Windows version of ICR2 (tested with Hatcher's Secondwind launcher)

Usage
Start ICR2DASH and keep it running in the background.
Launch DOSBox and ICR2 as usual (Note: Full-screen mode is not supported).
ICR2DASH will automatically close when you exit ICR2.

Troubleshooting
LCD Screen Reading: If the LCD screen isn't read correctly, press Ctrl-S during gameplay to capture a screenshot for adjustments in DASH_READER.INI.
Cockpit Alignment: Modify the ICR2DASH.INI for alignment which may vary depending on the version of ICR2.
Cockpit Detection: Adjust the detection settings in ICR2DASH.INI if the cockpit overlay isn't appearing correctly.
Dashboard shakes in Detroit tunnel: Push Ctrl-L to lock the dashboard. The program will continue to work properly as long as you don't move the window.

Refer to DEPENDENCIES for list of other Python libraries used in this project.

Thanks to GPLaps for help improving the cockpit textures.

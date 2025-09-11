# ICR2DASH - Cockpit Overlay for Papyrus IndyCar Racing 2

Enhance your ICR2 gaming experience with **ICR2DASH**, an interactive dashboard overlay tool for ICR2, designed to work with **DOSBox** and **Windy**.  
It reads real-time game data from the default cockpit view and draws a **1980s-style analog dashboard** to improve immersion when simulating the 1980s.

---

## Versions
- **3.4** – September 10, 2025  
- **3.3** – September 9, 2025  
- **3.1** – June 21, 2025 *(added DOSBox-Rendition support)*  
- **2.0** – June 24, 2024  

---

## Compatibility
Tested on **Windows 10** with ICR2 running in **windowed mode** in:
- DOSBox ECE  
- DOSBox Staging  

For **Rendition**, if you have an Nvidia card:
- Set **OpenGL GLI Compatibility** to *Prefer compatible*  
- Set **Vulkan/OpenGL Present** to *Prefer layered on DXGI swap*  

---

## System Requirements
- **DOS version of ICR2** (`INDYCAR.EXE` or `CART.EXE`) running in windowed mode on DOSBox ECE or DOSBox Staging  
  *(other DOSBox versions not tested)*  
- **Windows version of ICR2**, tested with **Hatcher's Secondwind launcher**  

---

## Usage
1. Configure `icr2dash.ini` for the particular version of ICR2 you are running
2. Start **ICR2DASH** and keep it running in the background.  
3. Launch DOSBox (or Windy) and ICR2 as usual.  
   > ⚠️ Full-screen mode is not supported.  
4. ICR2DASH will automatically close when you exit ICR2. Specify in `icr2dash.ini` the name of the window that will cause the app to stay open even when the driving window is gone (keepalive window).

---

## Troubleshooting
- **LCD screen not reading correctly** → Press **Ctrl+S** during gameplay to capture a screenshot. Adjust pixel mappings in `dash_reader.ini`.  
- **Cockpit misaligned** → Modify positioning offsets in `icr2dash.ini`. Alignment may vary by ICR2 version.  
- **Cockpit overlay not appearing** → Adjust cockpit detection points in `icr2dash.ini`.  
- **Dashboard shakes in Detroit tunnel** → Press **Ctrl+L** to lock the dashboard. It will remain stable as long as you don’t move the window.  

---

## Dependencies
See **DEPENDENCIES** file for the list of required Python libraries.  

---

## Credits
Special thanks to **GPLaps** for help improving the cockpit textures.  

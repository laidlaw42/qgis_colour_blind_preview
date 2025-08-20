# Colour Blind Preview

## Description

QGIS toolbar plugin that enable quick switching of the map Preview Mode for colour blind friendly map design.
Created using [Plugin Builder](https://plugins.qgis.org/plugins/pluginbuilder/).


## Setup

1. Download a zip of this repo
2. In QGIS, go to `Plugins > Manage and Install Plugins... > Install from zip`
3. Enable `Colour Blind Toggle` from the `Installed` tab


## Usage

1. Two icons appear in the toolbar (black square with no fill, and a red triangle) 
2. **Primary-click** applies the selected preview mode from the Settings dialog 
3. **Hover** over icons to see tooltips indicating the mode
4. **Secondary-click** opens the Settings dialog:
   - Modes: normal (disables preview mode), monochrome, achromatopsia, protanopia, deuteranopia, tritanopia
   - Enable/disable active highlights
   - Switch between text or icon options
   - Settings are persistent across sessions
5. Icons can be replaced with custom SVGs:
   - Locate the `qgis_colour_blind` in your plugins directory
   - Place your SVG icons in the `icons` folder and rename/replace the existing files as required

## Requirements
- QGIS 3.x (untested with Qt6)

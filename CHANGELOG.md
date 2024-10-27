<!--
=== UCSF ChimeraX Copyright ===
Copyright 2024 Regents of the University of California. All rights reserved.
The ChimeraX application is provided pursuant to the ChimeraX license
agreement, which covers academic and commercial uses. For more details, see
<https://www.rbvi.ucsf.edu/chimerax/docs/licensing.html>

You can also
redistribute and/or modify it under the terms of the GNU Lesser General
Public License version 2.1 as published by the Free Software Foundation.
For more details, see
<https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. ADDITIONAL LIABILITY
LIMITATIONS ARE DESCRIBED IN THE GNU LESSER GENERAL PUBLIC LICENSE
VERSION 2.1

This notice must be embedded in or attached to all copies, including partial
copies, of the software or any revisions or derivations thereof.
=== UCSF ChimeraX Copyright ===
-->

# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2023-10-23

### Added
- Initial stable release.
- Check model file size before creating augmentation. Prevents creating invalid empty augmentation when large models are open.
- Documentation files added for commands and tool in the help menu.
- `scholar removeUser` command. Will delete the user and all related data from ChimeraX.
- Tool will prompt to delete an invalid user if they are selected from existing users.

### Changed
- Adjusted logger message statuses.
- Make `filePath` argument in `scholar saveAugSession` an `OpenFileNameArg` which allows passing `browse` to open file explorer.
- `scholar augmentation` makes a sub call to `scholar saveAugSession` to capture the current session when the augmentation is first created.
- `scholar cleanLocal` updated to have optional `username` field. Not passing any username will clean files for all local users.
- Clean local in the context menu on the tool will target the logged in user. If the tool is in the login screen, all users will be targeted and a warning will appear asking for a confirmation to clean files across all users.
- Hide `scholar login` command from the log to prevent API token from being in the log. Related info/warning messages also no longer display a token. Adds security for bug reporting with included log.

### Fixed
- Raise `NonChimeraXError` for any Schol-AR server issues.
- More detailed error logging for network calls.
- If an augmentation file upload fails, log now describes which target field failed.
- Log suggests actions for complying with file size and upload requirements.
- Popup warns user about potential dangers when trying to update target image.

## [0.4.2] - August 2023
Works with ChimeraX ~=1.4

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- Concise log commands
- Add project title label on augmentation selection page

## [0.4.1] - August 2023
Works with ChimeraX ~=1.4

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- "scholar project" command projectType argument validity check
- "scholar augmentation" command augmentationType argument validity check

## [0.4.0] - August 2023
Works with ChimeraX ~=1.4

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- Update supported ChimeraX versions

## [0.3.3] - August 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- More python 3.5 support fixes

## [0.3.2] - August 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- Update to support python 3.5

## [0.3.1] - August 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- Updated file selection popup for file save buttons.
- Save Files Locally button now also saves QR image file.

## [0.2.1] - August 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- Login button label update
- Login page image update

## [0.2.0] - August 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeAllAugFiles, scholar storeModel, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR

### Release Notes
- scholar storeModel command. Stores model file at specified location.
- scholar storeAllAugFiles command. Stores model and target image file at specified folder.
- Image and text added to login page.
- View on Schol-AR button added in bottom navigation menu to open Schol-AR website
- "Store Target Image" button changed to "Store Files Locally" on augmentation edit page. The button now makes a call to the new scholar storeAllAugFiles command.
- Directions and QR labels added on preview pop out window.

## [0.1.0] - July 2023
Works with ChimeraX ~=1.1

### Details
- **bundle**: ChimeraX_ScholAR
- **command**: scholar augmentation, scholar cleanLocal, scholar downloadAugFiles, scholar downloadQR, scholar login, scholar openAugSession, scholar project, scholar saveAugSession, scholar storeQRImage, scholar storeTargetImage, scholar uploadAugFiles
- **tool**: ScholAR
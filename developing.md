# macOS apps need certificates

Following: https://github.com/txoof/codesign (which is also included under dev/pycodesign.py)

xcrun notarytool store-credentials {some name, must match keychain-profile in the pycodesign.ini} --apple-id {apple id (email)} --team-id {team_id}

Also add _Developer ID Application_ and _Developer ID Installer_ in xcode under certificates if they aren't there already.

## Example pycodesign.ini
```
[identification]
application_id = {Developer ID Application from `security find-identity -p basic -v`}
installer_id = {Developer ID Installer from `security find-identity -p basic -v`}
keychain-profile = {name from store-credentials}

[package_details]
package_name = fflipper
bundle_id = com.jonkeane.pacfflipperkagename
file_list = fflipper.app
installation_path = /Applications/
entitlements = ./entitlements.plist
version = 0.1.0
```
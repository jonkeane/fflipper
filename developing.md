# macOS apps need certificates

Following: https://github.com/txoof/codesign (which is also included under dev/pycodesign.py)


Also add _Developer ID Application_ and _Developer ID Installer_ in xcode under certificates if they aren't there already.

Finding IDs available by running `security find-identity -p basic -v`. There should be a few different identities, but we must store the one marked "Developer ID Application" as env var `MACOS_CODESIGN_DEV_ID` and the one marked "Developer ID Installer as env var `MACOS_CODESIGN_INSTALL_ID`. Might need to also make the keychain profile with:

```
xcrun notarytool store-credentials {some name, must match keychain-profile in the pycodesign.ini} --apple-id {apple id (email)} --team-id {team_id}
```

```
export MACOS_CODESIGN_DEV_ID=...
export MACOS_CODESIGN_INSTALL_ID=...
poetry run build
mkdir -p package
cp -R dist/fflipper.app package/fflipper.app
cp dev/entitlements.plist package/entitlements.plist
cp dev/pycodesign.ini package/pycodesign.ini
sed -i "" "s/{{MACOS_CODESIGN_DEV_ID}}/${MACOS_CODESIGN_DEV_ID}/g" package/pycodesign.ini
sed -i "" "s/{{MACOS_CODESIGN_INSTALL_ID}}/${MACOS_CODESIGN_INSTALL_ID}/g" package/pycodesign.ini
pushd package
../dev/pycodesign.py pycodesign.ini
```

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
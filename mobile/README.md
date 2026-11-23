# WebFluid Ocean for Android and iOS

This directory contains the Flutter app being prepared for release alongside WebFluid Ocean.
It opens the Ocean account dashboard, where the signed-in user can access their purchases,
merchant tools, chat and the other apps available to their account. The host defaults to
`https://ocean.webfluid.dev`.

The app lives in `mobile/` at the WebFluid Web project root. Its SDKs are local path dependencies
under the sibling `additives/` directory. Install the project’s Additives before running Flutter.
The legacy `all_sdks` identifiers below still participate in signing, links and SSO.

At start it asks for every permission the SDKs use — notifications (chat, payments, merchant
messages), the camera (QR codes, cards) and the gallery (uploads) — through
`UsersSDK.init(permissions: …)`, once per installation; the apps do not ask again afterwards.

## Run from the project root

```sh
cd mobile
flutter pub get
flutter run --dart-define=USERS_MOBILE_SECRET=<MOBILE_SECRET of the server's [auth] section>
```

Against a local server, forward the port and use the server's own origin:

```
adb reverse tcp:8000 tcp:8000
flutter run --dart-define=USERS_HOST=http://localhost:8000 --dart-define=USERS_INSECURE=true --dart-define=USERS_MOBILE_SECRET=<secret>
```

| Define                       | Default                              | Purpose                                              |
|------------------------------|--------------------------------------|------------------------------------------------------|
| `USERS_HOST`                 | `https://ocean.webfluid.dev`         | Server origin; also the Android app-link host        |
| `USERS_MOBILE_SECRET`        | —                                    | The server's `MOBILE_SECRET` (required)              |
| `USERS_INSECURE`             | `false`                              | Allow `http` and self-signed certificates            |
| `USERS_SIGNATURE`            | `dev.webfluid.all_sdks.example`      | App signature, listed in `USERS_MOBILE_SIGNATURES`   |
| `USERS_SSO_REDIRECT`         | `dev.webfluid.all-sdks.example:/sso` | SSO redirect (empty hides SSO)                       |
| `USERS_CONTACT`              | `pierre@growv-mail.org`              | Contact on the failure screen (empty hides it)       |
| `USERS_LANG`                 | system                               | `en` or `de`                                         |
| `USERS_THEME`                | `webfluid`                           | `webfluid` or the bundled `aurora`                   |
| `USERS_THEME_MODE`           | `system`                             | `system`, `light` or `dark`                          |
| `STRIPE_MERCHANT_IDENTIFIER` | —                                    | Apple Pay merchant id (empty: no Apple Pay)          |
| `STRIPE_TEST_ENVIRONMENT`    | `true`                               | Google Pay test environment                          |
| `USERS_FCM_*`                | —                                    | Push messages: `USERS_FCM_API_KEY`, `_APP_ID`, `_SENDER_ID`, `_PROJECT_ID`, or `USERS_FCM_NATIVE=true` for the native Firebase files |

## Host configuration

- `dev.webfluid.all_sdks.example` in `USERS_MOBILE_SIGNATURES` — first, if the camera should open
  this app from QR codes.
- `dev.webfluid.all-sdks.example:/sso` in `AUTH_PROVIDER_APP_REDIRECTS` for SSO.
- For camera app links: the SHA-256 fingerprint of the signing certificate for that build in `USERS_APP_LINK_FINGERPRINTS`
  (use the local debug certificate for development and the app signing certificate for distribution) and, for iOS, the team id in `USERS_APP_LINK_TEAM_ID`.
- Matching Stripe settings for the build environment. The merchant area needs the
  `STRIPE_CONNECT_ROLE`.
- For push messages (chat, payments, merchant messages): `USERS_PUSH_FCM_CREDENTIALS` of the same
  Firebase project.

## How it is configured

| Platform | Setting                                                                                                                                                                                                                                                                                         |
|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Android  | `applicationId` `dev.webfluid.all_sdks.example`, `MainActivity` is a `FlutterFragmentActivity` (Stripe), Material Components themes, core-library desugaring and the `ActionBroadcastReceiver` (notifications), `READ_MEDIA_IMAGES` / `READ_EXTERNAL_STORAGE` (≤ 32) for the gallery permission |
| Android  | App-link intent filter for `https://<USERS_HOST>/users/app/` (`autoVerify`), `users-sdk` scheme, SSO callback activity, Flutter deep linking off                                                                                                                                                |
| iOS      | Bundle id `dev.webfluid.all-sdks.example`, Associated Domains `applinks:$(APP_LINK_HOST)` (set in `Flutter/*.xcconfig`), URL types `users-sdk` and `dev.webfluid.all-sdks.example`, Flutter deep linking off                                                                                    |

The [Users SDK platform guide](../additives/users/flutter_sdk/.agents/references/platform-setup.md) describes the native configuration.

## Release builds

Build Android with `flutter build appbundle` and iOS on macOS with `flutter build ipa`.
The current Android release build type uses the debug signing configuration. Configure the
release signing identity before distributing an app bundle.
Pass the same host and mobile configuration as for `flutter run`, choosing the release signing,
push and payment settings for the intended host. Android launcher resources contain the rounded
WebFluid mark. The iOS AppIcon catalogue supplies opaque artwork for the system icon mask.

## Layout

```
lib/
├── main.dart          # init, registerApp for every SDK, authenticate/orchestrate loop
├── demo_config.dart   # dart-defines and appearance
└── aurora_theme.dart  # a second theme to switch to
```

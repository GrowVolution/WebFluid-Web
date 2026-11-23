import 'package:flutter/material.dart';
import 'package:users_sdk/users_sdk.dart';

import 'aurora_theme.dart';

abstract final class DemoConfig {
  static const String host = String.fromEnvironment('USERS_HOST', defaultValue: 'https://ocean.webfluid.dev');
  static const String mobileSecret = String.fromEnvironment('USERS_MOBILE_SECRET');
  static const String signature = String.fromEnvironment(
    'USERS_SIGNATURE',
    defaultValue: 'dev.webfluid.all_sdks.example',
  );
  static const String _ssoRedirect = String.fromEnvironment(
    'USERS_SSO_REDIRECT',
    defaultValue: 'dev.webfluid.all-sdks.example:/sso',
  );
  static const bool allowInsecure = bool.fromEnvironment('USERS_INSECURE');
  static const String _contact = String.fromEnvironment('USERS_CONTACT', defaultValue: 'pierre@growv-mail.org');
  static const String _language = String.fromEnvironment('USERS_LANG');
  static const String _theme = String.fromEnvironment('USERS_THEME');
  static const String _themeMode = String.fromEnvironment('USERS_THEME_MODE');
  static const String appScheme = 'dev.webfluid.all-sdks.example';
  static const String _merchantIdentifier = String.fromEnvironment('STRIPE_MERCHANT_IDENTIFIER');
  static const bool stripeTestEnvironment = bool.fromEnvironment('STRIPE_TEST_ENVIRONMENT', defaultValue: true);

  static String? get contact => _contact.isEmpty ? null : _contact;

  static String? get ssoRedirect => _ssoRedirect.isEmpty ? null : _ssoRedirect;

  static String? get merchantIdentifier => _merchantIdentifier.isEmpty ? null : _merchantIdentifier;

  static void applyAppearance() {
    UsersSDK.registerTheme(auroraTheme);

    if (_theme.isNotEmpty) UsersSDK.setTheme(_theme);
    if (_language.isNotEmpty) UsersSDK.setLang(_language);

    final mode = switch (_themeMode) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
    UsersSDK.setThemeMode(mode);
  }
}

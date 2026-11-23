import 'package:compliance_sdk/compliance_sdk.dart';
import 'package:flutter/widgets.dart';
import 'package:ocean_sdk/ocean_sdk.dart';
import 'package:stripe_connect_sdk/stripe_connect_sdk.dart';
import 'package:stripe_sdk/stripe_sdk.dart';
import 'package:users_admin_sdk/users_admin_sdk.dart';
import 'package:users_apps_sdk/users_apps_sdk.dart';
import 'package:users_chat_sdk/users_chat_sdk.dart';
import 'package:users_jwt_sdk/users_jwt_sdk.dart';
import 'package:users_sdk/users_sdk.dart';
import 'package:users_sdk_vodozemac/users_sdk_vodozemac.dart';

import 'app_config.dart';

Future<void> main() async {
  runApp(const UsersHost());
  if (!await setup()) return;

  UsersSDK.onReset = () => UsersSDK.toast(UsersSDK.tr('TRANSFER_DONE'), type: UsersToastType.info);

  AppConfig.applyAppearance();

  while (true) {
    final userId = await UsersSDK.authenticate();
    if (userId == 0) continue;

    try {
      await UsersSDK.orchestrate();
    } on UsersSessionExpiredException {
      UsersSDK.toast(UsersSDK.tr('SESSION_EXPIRED'), type: UsersToastType.warning);
    }
  }
}

@pragma('vm:entry-point')
Future<bool> setup() async {
  final ready = await UsersSDK.init(
    AppConfig.host,
    mobileSecret: AppConfig.mobileSecret,
    allowInsecure: AppConfig.allowInsecure,
    contact: AppConfig.contact,
    signature: AppConfig.signature,
    ssoRedirect: AppConfig.ssoRedirect,
    push: UsersPushConfig.fromEnvironment(),
    ratchet: const VodozemacEngine(),
    background: setup,
    permissions: const [UsersPermission.notifications, UsersPermission.camera, UsersPermission.photos],
  );
  if (!ready) return false;

  final payments = StripePayments(
    sheet: StripePaymentSheet(
      merchantIdentifier: AppConfig.merchantIdentifier,
      urlScheme: AppConfig.appScheme,
      testEnvironment: AppConfig.stripeTestEnvironment,
    ),
  );
  const merchant = StripeMerchant();
  final billing = StripeApp(payments: payments);
  final connect = StripeConnect(merchant: merchant);
  final ocean = Ocean(billing: billing, connect: connect);

  UsersSDK.registerApp(UsersApps.id, const UsersApps());
  UsersSDK.registerApp(UsersAdmin.id, const UsersAdmin());
  UsersSDK.registerApp(UsersJwt.id, const UsersJwt());
  UsersSDK.registerApp(UsersChat.id, UsersChat(engine: const VodozemacEngine()));
  UsersSDK.registerApp(StripeApp.id, billing);
  UsersSDK.registerApp(StripeConnect.id, connect);
  UsersSDK.registerApp(Ocean.id, ocean);
  UsersSDK.registerApp(ComplianceApp.id, const ComplianceApp());
  return true;
}

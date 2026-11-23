import 'dart:ui';

import 'package:users_sdk/users_sdk.dart';

const UsersTheme auroraTheme = UsersTheme(
  name: 'aurora',
  light: UsersTriade(
    primary: UsersColorScale(
      Color(0xFF7B8CC4),
      Color(0xFF52639E),
      Color(0xFF34437A),
      Color(0xFF1C2855),
      Color(0xFF0C1433),
    ),
    secondary: UsersColorScale(
      Color(0xFFB09AE0),
      Color(0xFF8A6DCC),
      Color(0xFF6445AE),
      Color(0xFF412B80),
      Color(0xFF22154D),
    ),
    tertiary: UsersColorScale(
      Color(0xFF6FE3D2),
      Color(0xFF38BFB1),
      Color(0xFF198F84),
      Color(0xFF0C645C),
      Color(0xFF053D39),
    ),
  ),
  dark: UsersTriade(
    primary: UsersColorScale(
      Color(0xFF65739F),
      Color(0xFF414F7E),
      Color(0xFF28345F),
      Color(0xFF141D40),
      Color(0xFF070C22),
    ),
    secondary: UsersColorScale(
      Color(0xFF9580C7),
      Color(0xFF7155B0),
      Color(0xFF4F3491),
      Color(0xFF321F66),
      Color(0xFF190E3A),
    ),
    tertiary: UsersColorScale(
      Color(0xFF5CCFBF),
      Color(0xFF2EA99C),
      Color(0xFF147A70),
      Color(0xFF09544D),
      Color(0xFF03322E),
    ),
  ),
);

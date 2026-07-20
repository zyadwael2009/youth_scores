import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get dark => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.dark(
      primary: AppColors.aqua,
      secondary: AppColors.teal,
      surface: AppColors.cardBg,
      onPrimary: AppColors.darkBg,
      onSecondary: AppColors.darkBg,
      onSurface: AppColors.white,
      outline: AppColors.border,
    ),
    scaffoldBackgroundColor: AppColors.darkBg,
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.cardBg,
      foregroundColor: AppColors.aqua,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: AppColors.aqua,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
      iconTheme: IconThemeData(color: AppColors.aqua),
    ),
    cardTheme: CardThemeData(
      color: AppColors.cardBg,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: AppColors.border),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.cardBg,
      hintStyle: TextStyle(color: AppColors.hint),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: AppColors.aqua),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: AppColors.aqua, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    textTheme: TextTheme(
      titleLarge:  TextStyle(color: AppColors.aqua,  fontWeight: FontWeight.bold),
      titleMedium: TextStyle(color: AppColors.aqua,  fontWeight: FontWeight.w600),
      titleSmall:  TextStyle(color: AppColors.teal),
      bodyLarge:   TextStyle(color: AppColors.white),
      bodyMedium:  TextStyle(color: AppColors.teal),
      bodySmall:   TextStyle(color: AppColors.teal),
      labelLarge:  TextStyle(color: AppColors.aqua,  fontWeight: FontWeight.bold),
    ),
    bottomNavigationBarTheme: BottomNavigationBarThemeData(
      backgroundColor: AppColors.cardBg,
      selectedItemColor: AppColors.aqua,
      unselectedItemColor: AppColors.teal,
      type: BottomNavigationBarType.fixed,
      elevation: 8,
    ),
    dividerTheme: DividerThemeData(color: AppColors.border, thickness: 1),
    tabBarTheme: TabBarThemeData(
      labelColor: AppColors.aqua,
      unselectedLabelColor: AppColors.teal,
      indicatorColor: AppColors.aqua,
      dividerColor: AppColors.border,
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(color: AppColors.aqua),
    iconTheme: IconThemeData(color: AppColors.aqua),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: AppColors.aqua,
      foregroundColor: AppColors.darkBg,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.cardBg,
      selectedColor: AppColors.aqua.withValues(alpha: 0.2),
      labelStyle: TextStyle(color: AppColors.teal),
      secondaryLabelStyle: TextStyle(color: AppColors.darkBg),
      side: BorderSide(color: AppColors.border),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    ),
  );

  static ThemeData get light => ThemeData(
    useMaterial3: true,
    colorScheme: const ColorScheme.light(
      primary:     Color(0xFF0077A8),
      secondary:   Color(0xFF1B6A8E),
      surface:     Colors.white,
      onPrimary:   Colors.white,
      onSecondary: Colors.white,
      onSurface:   Color(0xFF0D1B2A),
      outline:     Color(0xFFBDD5E4),
    ),
    scaffoldBackgroundColor: const Color(0xFFF0F6FF),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: Color(0xFF0077A8),
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: Color(0xFF0077A8),
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
      iconTheme: IconThemeData(color: Color(0xFF0077A8)),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0xFFBDD5E4)),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      hintStyle: const TextStyle(color: Color(0xFF4A7F98)),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF0077A8)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFBDD5E4)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF0077A8), width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    textTheme: const TextTheme(
      titleLarge:  TextStyle(color: Color(0xFF0077A8), fontWeight: FontWeight.bold),
      titleMedium: TextStyle(color: Color(0xFF0077A8), fontWeight: FontWeight.w600),
      titleSmall:  TextStyle(color: Color(0xFF1B6A8E)),
      bodyLarge:   TextStyle(color: Color(0xFF0D1B2A)),
      bodyMedium:  TextStyle(color: Color(0xFF1B6A8E)),
      bodySmall:   TextStyle(color: Color(0xFF1B6A8E)),
      labelLarge:  TextStyle(color: Color(0xFF0077A8), fontWeight: FontWeight.bold),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: Colors.white,
      selectedItemColor:   Color(0xFF0077A8),
      unselectedItemColor: Color(0xFF1B6A8E),
      type: BottomNavigationBarType.fixed,
      elevation: 8,
    ),
    dividerTheme: const DividerThemeData(color: Color(0xFFBDD5E4), thickness: 1),
    tabBarTheme: const TabBarThemeData(
      labelColor:            Color(0xFF0077A8),
      unselectedLabelColor:  Color(0xFF1B6A8E),
      indicatorColor:        Color(0xFF0077A8),
      dividerColor:          Color(0xFFBDD5E4),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(color: Color(0xFF0077A8)),
    iconTheme: const IconThemeData(color: Color(0xFF0077A8)),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: Color(0xFF0077A8),
      foregroundColor: Colors.white,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Colors.white,
      selectedColor: const Color(0xFF0077A8).withValues(alpha: 0.15),
      labelStyle: const TextStyle(color: Color(0xFF1B6A8E)),
      secondaryLabelStyle: const TextStyle(color: Colors.white),
      side: const BorderSide(color: Color(0xFFBDD5E4)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    ),
  );
}

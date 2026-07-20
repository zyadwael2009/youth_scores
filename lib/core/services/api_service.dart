import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/config_model.dart';
import '../models/competition_data_model.dart';

class ApiService {
  static const _configUrl = 'https://youth-scores-data.vercel.app/api/config';
  static const _timeout   = Duration(seconds: 30);

  Future<ConfigData> fetchConfig() async {
    final cfg = await http.get(Uri.parse(_configUrl)).timeout(_timeout);
    if (cfg.statusCode != 200) {
      throw Exception('Config fetch failed: ${cfg.statusCode}');
    }
    final cfgJson   = json.decode(cfg.body) as Map<String, dynamic>;
    final dataUrl   = cfgJson['latestDataUrl'] as String?;
    if (dataUrl == null || dataUrl.isEmpty) {
      throw Exception('latestDataUrl missing in config');
    }
    final data = await http.get(Uri.parse(dataUrl)).timeout(_timeout);
    if (data.statusCode != 200) {
      throw Exception('Data fetch failed: ${data.statusCode}');
    }
    return ConfigData.fromJson(json.decode(data.body) as Map<String, dynamic>);
  }

  Future<CompetitionData> fetchCompetition(String url) async {
    final res = await http.get(Uri.parse(url)).timeout(_timeout);
    if (res.statusCode != 200) {
      throw Exception('Competition fetch failed: ${res.statusCode}');
    }
    return CompetitionData.fromJson(
      json.decode(res.body) as Map<String, dynamic>,
    );
  }

  /// Returns the raw JSON body string so callers can cache it without
  /// re-serialising the parsed model.
  Future<String> fetchCompetitionRaw(String url) async {
    final res = await http.get(Uri.parse(url)).timeout(_timeout);
    if (res.statusCode != 200) {
      throw Exception('Competition fetch failed: ${res.statusCode}');
    }
    return res.body;
  }
}

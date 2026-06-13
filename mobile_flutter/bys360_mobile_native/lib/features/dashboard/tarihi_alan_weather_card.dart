import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../core/theme/app_theme.dart';

class TarihiAlanWeatherCard extends StatefulWidget {
  const TarihiAlanWeatherCard({super.key});

  @override
  State<TarihiAlanWeatherCard> createState() => _TarihiAlanWeatherCardState();
}

class _TarihiAlanWeatherCardState extends State<TarihiAlanWeatherCard> {
  late Future<_TarihiAlanWeather> _future;

  @override
  void initState() {
    super.initState();
    _future = _loadWeather();
  }

  Future<void> _refresh() async {
    setState(() => _future = _loadWeather());
    await _future;
  }

  Future<_TarihiAlanWeather> _loadWeather() async {
    final uri = Uri.https('api.open-meteo.com', '/v1/forecast', {
      'latitude': '40.1847',
      'longitude': '26.3576',
      'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
      'daily': 'temperature_2m_max,temperature_2m_min',
      'timezone': 'Europe/Istanbul',
      'forecast_days': '1',
    });

    final response = await http.get(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Hava durumu servisine ulaşılamadı.');
    }

    final payload = jsonDecode(response.body) as Map<String, dynamic>;
    final current = Map<String, dynamic>.from(payload['current'] as Map);
    final daily = Map<String, dynamic>.from(payload['daily'] as Map);

    final maxList = List<dynamic>.from(daily['temperature_2m_max'] as List);
    final minList = List<dynamic>.from(daily['temperature_2m_min'] as List);
    final weatherCode = _asInt(current['weather_code']);

    return _TarihiAlanWeather(
      temperature: _asDouble(current['temperature_2m']),
      apparentTemperature: _asDouble(current['apparent_temperature']),
      humidity: _asInt(current['relative_humidity_2m']),
      windSpeed: _asDouble(current['wind_speed_10m']),
      maxTemperature: maxList.isEmpty ? null : _asDouble(maxList.first),
      minTemperature: minList.isEmpty ? null : _asDouble(minList.first),
      condition: _weatherText(weatherCode),
      icon: _weatherIcon(weatherCode),
      updatedAt: DateTime.tryParse('${current['time']}'),
    );
  }

  static double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse('$value') ?? 0;
  }

  static int _asInt(dynamic value) {
    if (value is num) return value.toInt();
    return int.tryParse('$value') ?? 0;
  }

  static String _weatherText(int code) {
    if (code == 0) return 'Açık';
    if ([1, 2, 3].contains(code)) return 'Parçalı bulutlu';
    if ([45, 48].contains(code)) return 'Sisli';
    if ([51, 53, 55, 56, 57].contains(code)) return 'Çiseleyen yağmur';
    if ([61, 63, 65, 66, 67].contains(code)) return 'Yağmurlu';
    if ([71, 73, 75, 77, 85, 86].contains(code)) return 'Kar yağışlı';
    if ([80, 81, 82].contains(code)) return 'Sağanak yağışlı';
    if ([95, 96, 99].contains(code)) return 'Gök gürültülü';
    return 'Hava durumu';
  }

  static IconData _weatherIcon(int code) {
    if (code == 0) return Icons.wb_sunny_outlined;
    if ([1, 2, 3].contains(code)) return Icons.cloud_queue_outlined;
    if ([45, 48].contains(code)) return Icons.foggy;
    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].contains(code)) {
      return Icons.water_drop_outlined;
    }
    if ([71, 73, 75, 77, 85, 86].contains(code)) return Icons.ac_unit_outlined;
    if ([95, 96, 99].contains(code)) return Icons.thunderstorm_outlined;
    return Icons.thermostat_outlined;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_TarihiAlanWeather>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const _WeatherShell(
            icon: Icons.cloud_sync_outlined,
            title: 'Tarihi Alan Hava Durumu',
            subtitle: 'Güncel hava bilgisi alınıyor',
            child: _WeatherLoadingRow(),
          );
        }

        if (snapshot.hasError || !snapshot.hasData) {
          return _WeatherShell(
            icon: Icons.cloud_off_outlined,
            title: 'Tarihi Alan Hava Durumu',
            subtitle: 'Gelibolu Tarihi Alan genel görünümü',
            trailing: IconButton(
              tooltip: 'Yenile',
              onPressed: _refresh,
              icon: const Icon(Icons.refresh, color: BYS360Colors.corporateRed),
            ),
            child: const Text(
              'Hava durumu şu anda alınamadı. Ana sayfa çalışmaya devam ediyor; biraz sonra tekrar deneyebilirsiniz.',
              style: TextStyle(color: BYS360Colors.mutedText, height: 1.35),
            ),
          );
        }

        final weather = snapshot.data!;
        return _WeatherShell(
          icon: weather.icon,
          title: 'Tarihi Alan Hava Durumu',
          subtitle: 'Gelibolu Tarihi Alan / Eceabat',
          trailing: IconButton(
            tooltip: 'Yenile',
            onPressed: _refresh,
            icon: const Icon(Icons.refresh, color: BYS360Colors.corporateRed),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${weather.temperature.round()}°',
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                          color: BYS360Colors.corporateRed,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 7),
                      child: Text(
                        weather.condition,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _WeatherChip(icon: Icons.thermostat_outlined, label: 'Hissedilen ${weather.apparentTemperature.round()}°'),
                  _WeatherChip(icon: Icons.air_outlined, label: 'Rüzgâr ${weather.windSpeed.round()} km/sa'),
                  _WeatherChip(icon: Icons.water_drop_outlined, label: 'Nem %${weather.humidity}'),
                  if (weather.maxTemperature != null && weather.minTemperature != null)
                    _WeatherChip(
                      icon: Icons.device_thermostat_outlined,
                      label: 'Bugün ${weather.minTemperature!.round()}° / ${weather.maxTemperature!.round()}°',
                    ),
                ],
              ),
              if (weather.updatedAt != null) ...[
                const SizedBox(height: 9),
                Text(
                  'Güncelleme: ${_formatTime(weather.updatedAt!)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  static String _formatTime(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}

class _TarihiAlanWeather {
  const _TarihiAlanWeather({
    required this.temperature,
    required this.apparentTemperature,
    required this.humidity,
    required this.windSpeed,
    required this.condition,
    required this.icon,
    required this.updatedAt,
    this.maxTemperature,
    this.minTemperature,
  });

  final double temperature;
  final double apparentTemperature;
  final int humidity;
  final double windSpeed;
  final double? maxTemperature;
  final double? minTemperature;
  final String condition;
  final IconData icon;
  final DateTime? updatedAt;
}

class _WeatherShell extends StatelessWidget {
  const _WeatherShell({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.child,
    this.trailing,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(BYS360Radii.xl),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.card,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: BYS360Colors.softRed,
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Icon(icon, color: BYS360Colors.corporateRed, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 2),
                    Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText)),
                  ],
                ),
              ),
              if (trailing != null) trailing!,
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

class _WeatherChip extends StatelessWidget {
  const _WeatherChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: BYS360Colors.pageBackground,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: BYS360Colors.cardBorder),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: BYS360Colors.corporateRed),
          const SizedBox(width: 6),
          Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _WeatherLoadingRow extends StatelessWidget {
  const _WeatherLoadingRow();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: [
        SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
        SizedBox(width: 10),
        Expanded(
          child: Text(
            'Tarihi Alan için güncel hava bilgisi hazırlanıyor.',
            style: TextStyle(color: BYS360Colors.mutedText),
          ),
        ),
      ],
    );
  }
}

// BYS360_MOBILE_V2_8_59_TARIHI_ALAN_WEATHER_CARD

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Reelix Debug',
      theme: ThemeData(primarySwatch: Colors.deepPurple),
      home: const ScannerStatusScreen(),
    );
  }
}

class ScannerStatusScreen extends StatefulWidget {
  const ScannerStatusScreen({super.key});

  @override
  State<ScannerStatusScreen> createState() => _ScannerStatusScreenState();
}

class _ScannerStatusScreenState extends State<ScannerStatusScreen> {
  static const platform = MethodChannel('com.reelix.reelix/scanner');

  bool _overlayGranted = false;
  bool _audioGranted = false;
  bool _notificationGranted = false;
  bool _scannerRunning = false;
  
  final TextEditingController _backendUrlController = TextEditingController(text: "http://192.168.0.x:8000");

  String? _lastResultMovie;
  String? _lastResultMusic;
  String? _lastProcessingTime;

  @override
  void initState() {
    super.initState();
    _checkPermissions();
    platform.setMethodCallHandler(_handleMethodCall);
  }
  
  Future<dynamic> _handleMethodCall(MethodCall call) async {
    if (call.method == 'onScanResult') {
      final args = Map<String, dynamic>.from(call.arguments);
      final List<String> frames = List<String>.from(args['frames'] ?? []);
      final String? audio = args['audio'];
      
      _uploadEvidence(frames, audio);
    }
  }

  Future<void> _uploadEvidence(List<String> frames, String? audio) async {
    final url = Uri.tryParse('${_backendUrlController.text}/recognize');
    if (url == null) return;
    
    setState(() {
      _lastResultMovie = "Uploading & Processing...";
      _lastResultMusic = "...";
      _lastProcessingTime = "...";
    });

    try {
      var request = http.MultipartRequest('POST', url);
      
      for (var framePath in frames) {
        request.files.add(await http.MultipartFile.fromPath('frames', framePath));
      }
      
      if (audio != null) {
        request.files.add(await http.MultipartFile.fromPath('audio', audio));
      }
      
      final startTime = DateTime.now();
      var response = await request.send();
      final roundTripMs = DateTime.now().difference(startTime).inMilliseconds;
      
      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        final json = jsonDecode(respStr);
        
        setState(() {
          _lastResultMovie = "State: ${json['movie']['state']}\nTitle: ${json['movie']['title'] ?? 'N/A'}\nVisual Score: ${json['movie']['visual_score']}\nOCR Score: ${json['movie']['ocr_score']}";
          _lastResultMusic = "State: ${json['music']['state']}\nTrack: ${json['music']['track'] ?? 'N/A'}\nScore: ${json['music']['score']}";
          _lastProcessingTime = "Backend Total: ${json['timing_ms']['total']} ms\nRound Trip: $roundTripMs ms";
        });
      } else {
        setState(() {
          _lastResultMovie = "Error: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _lastResultMovie = "Error: $e";
      });
    } finally {
      // Clean up temp files on Android
      await platform.invokeMethod('cleanupTemp');
    }
  }

  Future<void> _checkPermissions() async {
    try {
      final bool overlay = await platform.invokeMethod('checkOverlayPermission');
      final bool audio = await platform.invokeMethod('checkAudioPermission');
      final bool notif = await platform.invokeMethod('checkNotificationPermission');
      setState(() {
        _overlayGranted = overlay;
        _audioGranted = audio;
        _notificationGranted = notif;
      });
    } catch (e) {
      debugPrint("Failed to check permissions: $e");
    }
  }

  Future<void> _requestOverlay() async {
    try {
      final bool result = await platform.invokeMethod('requestOverlayPermission');
      setState(() => _overlayGranted = result);
    } catch (e) {
      debugPrint("Error requesting overlay: $e");
    }
  }

  Future<void> _requestAudio() async {
    try {
      final bool result = await platform.invokeMethod('requestAudioPermission');
      setState(() => _audioGranted = result);
    } catch (e) {
      debugPrint("Error requesting audio: $e");
    }
  }
  
  Future<void> _requestNotification() async {
    try {
      final bool result = await platform.invokeMethod('requestNotificationPermission');
      setState(() => _notificationGranted = result);
    } catch (e) {
      debugPrint("Error requesting notification: $e");
    }
  }

  Future<void> _startScanner() async {
    try {
      final bool result = await platform.invokeMethod('startScanner');
      if (result) {
        setState(() => _scannerRunning = true);
      }
    } catch (e) {
      debugPrint("Error starting scanner: $e");
    }
  }

  Future<void> _stopScanner() async {
    try {
      await platform.invokeMethod('stopScanner');
      setState(() => _scannerRunning = false);
    } catch (e) {
      debugPrint("Error stopping scanner: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reelix Scanner Debug')),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          TextField(
            controller: _backendUrlController,
            decoration: const InputDecoration(
              labelText: 'Backend URL',
              hintText: 'http://192.168.x.x:8000',
            ),
          ),
          const SizedBox(height: 16),
          _StatusRow(
            title: 'Overlay Permission',
            status: _overlayGranted ? 'GRANTED' : 'NOT GRANTED',
            statusColor: _overlayGranted ? Colors.green : Colors.red,
            onTap: _requestOverlay,
            actionLabel: 'Request',
          ),
          _StatusRow(
            title: 'Audio Permission',
            status: _audioGranted ? 'GRANTED' : 'NOT GRANTED',
            statusColor: _audioGranted ? Colors.green : Colors.red,
            onTap: _requestAudio,
            actionLabel: 'Request',
          ),
          _StatusRow(
            title: 'Notification Permission',
            status: _notificationGranted ? 'GRANTED' : 'NOT GRANTED',
            statusColor: _notificationGranted ? Colors.green : Colors.red,
            onTap: _requestNotification,
            actionLabel: 'Request',
          ),
          _StatusRow(
            title: 'Scanner Service',
            status: _scannerRunning ? 'RUNNING' : 'STOPPED',
            statusColor: _scannerRunning ? Colors.green : Colors.red,
            onTap: null,
          ),
          const SizedBox(height: 32),
          ElevatedButton(
            onPressed: (_overlayGranted && _audioGranted && _notificationGranted && !_scannerRunning)
                ? _startScanner
                : null,
            child: const Text('Start Scanner'),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _scannerRunning ? _stopScanner : null,
            child: const Text('Stop Scanner'),
          ),
          const SizedBox(height: 32),
          if (_lastResultMovie != null) ...[
            const Text("MOVIE / TV", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(_lastResultMovie!),
            const SizedBox(height: 16),
            const Text("MUSIC", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(_lastResultMusic!),
            const SizedBox(height: 16),
            const Text("PROCESSING", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(_lastProcessingTime!),
          ]
        ],
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String title;
  final String status;
  final Color statusColor;
  final VoidCallback? onTap;
  final String? actionLabel;

  const _StatusRow({
    required this.title,
    required this.status,
    required this.statusColor,
    this.onTap,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          Row(
            children: [
              Text(status, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
              if (onTap != null && actionLabel != null) ...[
                const SizedBox(width: 8),
                TextButton(onPressed: onTap, child: Text(actionLabel!)),
              ]
            ],
          )
        ],
      ),
    );
  }
}

# Adaptive Bitrate Streaming (ABR) Implementation Guide

## Overview

**Adaptive Bitrate Streaming (ABR)** automatically adjusts video quality based on the user's network conditions in real-time.

### How It Works

```
1. Server encodes multiple quality versions (480p, 720p, etc.)
2. Server creates master playlist with all versions
3. Player reads master playlist
4. Player measures network bandwidth
5. Player selects appropriate quality
6. **As bandwidth changes → player switches quality**
7. User sees smooth playback without buffering
```

## Backend (Already Implemented)

Your backend already serves the master playlist with multiple renditions:

```m3u8
#EXTM3U
#EXT-X-VERSION:3

# H.265 (HEVC) - Primary
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480,CODECS="hev1.1.6.L120"
480p/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720,CODECS="hev1.1.6.L120"
720p/index.m3u8

# H.264 - Fallback
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480,CODECS="avc1.42e01e,mp4a.40.2"
480p_h264/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720,CODECS="avc1.42e01e,mp4a.40.2"
720p_h264/index.m3u8
```

**The player automatically selects quality based on bandwidth!**

## Frontend Implementation

### Flutter + video_player + chewie

**Simplest approach - uses native HLS ABR:**

```dart
import 'package:chewie/chewie.dart';
import 'package:video_player/video_player.dart';

class VideoPlayerScreen extends StatefulWidget {
  final String masterPlaylistUrl;
  
  @override
  State<VideoPlayerScreen> createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  late VideoPlayerController _videoController;
  late ChewieController _chewieController;

  @override
  void initState() {
    super.initState();
    
    _videoController = VideoPlayerController.network(
      widget.masterPlaylistUrl,
      // R2 or CDN URL pointing to master.m3u8
    );
    
    _chewieController = ChewieController(
      videoPlayerController: _videoController,
      autoPlay: true,
      looping: false,
      // ABR enabled by default!
      // Player automatically switches quality
    );
  }

  @override
  Widget build(BuildContext context) {
    return Chewie(controller: _chewieController);
  }

  @override
  void dispose() {
    _videoController.dispose();
    _chewieController.dispose();
    super.dispose();
  }
}
```

**That's it!** Chewie + video_player handle ABR automatically.

### Flutter + HLS.js (Web)

For Flutter web, use HLS.js for advanced ABR control:

```dart
import 'package:flutter_web_plugins/flutter_web_plugins.dart';
import 'dart:html' as html;

class WebVideoPlayer extends StatefulWidget {
  final String masterPlaylistUrl;
  
  @override
  State<WebVideoPlayer> createState() => _WebVideoPlayerState();
}

class _WebVideoPlayerState extends State<WebVideoPlayer> {
  late html.VideoElement _videoElement;

  @override
  void initState() {
    super.initState();
    _initializeHls();
  }

  void _initializeHls() {
    _videoElement = html.querySelector('#video') as html.VideoElement;
    
    // Load HLS.js from CDN
    final script = html.ScriptElement()
      ..src = 'https://cdn.jsdelivr.net/npm/hls.js@latest'
      ..type = 'text/javascript'
      ..onLoad.listen((_) {
        _setupHls();
      });
    
    html.document.head?.append(script);
  }

  void _setupHls() {
    // HLS.js automatically handles ABR
    final hlsJs = html.window.getProperty('Hls');
    if (hlsJs != null) {
      final hls = hlsJs.callMethod('new', []);
      hls.callMethod('loadSource', [widget.masterPlaylistUrl]);
      hls.callMethod('attachMedia', [_videoElement]);
      
      // Optional: Listen to ABR events
      hls.callMethod('on', ['hlsManifestParsed', () {
        print('Manifest parsed - ABR enabled');
      }]);
      
      hls.callMethod('on', ['hlsLevelSwitching', (level) {
        print('Switched to quality level: $level');
      }]);
    }
  }

  @override
  Widget build(BuildContext context) {
    return html.VideoElement()
      ..id = 'video'
      ..controls = true
      ..width = 1280
      ..height = 720;
  }
}
```

### Native Android (ExoPlayer)

```kotlin
// build.gradle
dependencies {
    implementation 'com.google.android.exoplayer:exoplayer-hls:2.19.0'
}

// MainActivity.kt
class VideoActivity : AppCompatActivity() {
    private lateinit var player: SimpleExoPlayer

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_video)

        player = SimpleExoPlayer.Builder(this).build()
        
        val mediaItem = MediaItem.Builder()
            .setUri("https://r2-url/videos/123/master.m3u8")
            .build()
        
        player.setMediaItem(mediaItem)
        player.prepare()
        
        // ExoPlayer automatically handles HLS ABR!
        // Switches quality based on bandwidth
        
        val playerView = findViewById<PlayerView>(R.id.player_view)
        playerView.player = player
    }
}
```

### Native iOS (AVPlayer)

```swift
import AVKit

class VideoViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let masterURL = URL(string: "https://r2-url/videos/123/master.m3u8")!
        
        let playerItem = AVPlayerItem(url: masterURL)
        let player = AVPlayer(playerItem: playerItem)
        
        let playerViewController = AVPlayerViewController()
        playerViewController.player = player
        
        // AVPlayer automatically handles HLS ABR!
        // Watches network conditions and switches quality
        
        present(playerViewController, animated: true)
    }
}
```

## Advanced ABR Control

### Monitor Quality Switching

**Flutter:**
```dart
class VideoPlayerWithMonitoring extends StatefulWidget {
  @override
  State<VideoPlayerWithMonitoring> createState() => _State();
}

class _State extends State<VideoPlayerWithMonitoring> {
  String currentQuality = "Loading...";
  int currentBitrate = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Chewie(controller: _chewieController),
        
        // Display current quality
        Container(
          padding: EdgeInsets.all(16),
          child: Text(
            'Quality: $currentQuality\nBitrate: ${currentBitrate ~/ 1000} kbps',
            style: TextStyle(fontSize: 14, color: Colors.white),
          ),
        ),
      ],
    );
  }
}
```

### Control Quality Manually

**HLS.js Example:**
```javascript
const hls = new Hls();

// Get available qualities
hls.on(Hls.Events.MANIFEST_PARSED, function() {
    const levels = hls.levels;
    console.log('Available qualities:', levels.map(l => l.height + 'p'));
});

// Force specific quality
function setQuality(levelIndex) {
    hls.currentLevel = levelIndex;
}

// Lock quality (disable automatic switching)
function lockQuality(levelIndex) {
    hls.currentLevel = levelIndex;
    hls.levelLocked = true;
}

// Reset to auto
function autoQuality() {
    hls.levelLocked = false;
}
```

## Performance Tips

### 1. Optimize Segment Duration

**Current:** 6 seconds per segment

**Pros:** Faster quality switching
**Cons:** More HTTP requests

**Recommendation:** Keep at 6 seconds

### 2. Playlist Caching

Enable caching headers (already done in R2 config):
- Segments: `Cache-Control: public, max-age=31536000` (1 year)
- Master playlist: `Cache-Control: private, max-age=60` (1 minute)

### 3. Connection Awareness

Implement network-aware quality selection:

```dart
import 'package:connectivity_plus/connectivity_plus.dart';

class NetworkAwarePlayer {
  void adjustQualityForNetwork() {
    Connectivity().onConnectivityChanged.listen((result) {
      switch (result) {
        case ConnectivityResult.wifi:
          // Force 720p on WiFi
          print('WiFi - using 720p');
          break;
        case ConnectivityResult.mobile:
          // Allow automatic selection on mobile
          print('Mobile - auto ABR');
          break;
        case ConnectivityResult.none:
          print('No connection');
          break;
      }
    });
  }
}
```

### 4. Bandwidth Estimation

Most players estimate bandwidth from:
- Download time of segments
- Buffer fullness
- Network variability

**No backend changes needed!** Built into:
- Chewie/VideoPlayer
- HLS.js
- ExoPlayer
- AVPlayer

## Testing ABR

### Test on Different Connections

```bash
# Simulate slow connection
# Linux (tc command)
sudo tc qdisc add dev eth0 root tbf rate 500kbit burst 32kb latency 400ms

# Test with curl
curl -H "Range: bytes=0-1000000" https://r2-url/videos/123/480p/segment.ts

# Verify mobile hotspot or 4G
# Watch logs for quality switches
```

### Monitor in App

Add debug overlay:

```dart
class DebugVideoOverlay extends StatefulWidget {
  @override
  State<DebugVideoOverlay> createState() => _State();
}

class _State extends State<DebugVideoOverlay> {
  Timer? _updateTimer;
  String debugInfo = '';

  @override
  void initState() {
    super.initState();
    _updateTimer = Timer.periodic(Duration(seconds: 1), (_) {
      // Update debug info every second
      setState(() {
        // Get player stats
        debugInfo = '''
        Quality: 720p
        Bitrate: 1200 kbps
        Buffer: 8s
        Network: WiFi
        FPS: 30
        Dropped: 0
        ''';
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Video player
        YourVideoPlayer(),
        
        // Debug overlay
        Positioned(
          top: 16,
          right: 16,
          child: Container(
            padding: EdgeInsets.all(12),
            background: Colors.black54,
            child: Text(
              debugInfo,
              style: TextStyle(
                color: Colors.white,
                fontFamily: 'monospace',
                fontSize: 10,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
```

## Troubleshooting

### Issue: Not Switching Quality

**Cause:** Player doesn't support HLS or wrong codec

**Fix:**
```dart
// Use Chewie (supports HLS ABR)
ChewieController(
  videoPlayerController: _controller,
  allowedScreenSleep: false,
  allowFullScreen: true,
);

// Verify URL is accessible
// Verify master.m3u8 has all renditions
```

### Issue: Always on 480p

**Cause:** Network too slow

**Fix:**
```
1. Check network speed
2. Lower 480p bitrate if needed
3. Add 360p rendition for very slow networks
```

### Issue: Buffering on Quality Switch

**Cause:** Too small buffer

**Fix:**
```
Increase buffer:
- Chewie: bufferingConfiguration property
- HLS.js: config.bufferLengthDefault = 30
- ExoPlayer: setBufferDurationMillis(30000)
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│      Backend (Django + FFmpeg)          │
│  Encodes 480p + 720p renditions        │
│  Uploads to R2                          │
│  Serves master.m3u8                     │
└──────────────┬──────────────────────────┘
               │
               ▼
        master.m3u8 (R2)
        ├── 480p/index.m3u8 (800k)
        ├── 720p/index.m3u8 (1400k)
        └── segments (*.ts files)
               │
               ▼
    ┌──────────────────────────┐
    │   Flutter + video_player │
    │   + Chewie               │
    │                          │
    │ Reads master playlist    │
    │ Measures bandwidth       │
    │ Switches quality         │
    │ (NO CODE NEEDED!)        │
    └──────────────────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │   User sees smooth       │
    │   playback at optimal    │
    │   quality for their      │
    │   network speed          │
    └──────────────────────────┘
```

## Summary

✅ **Your backend already supports ABR!**
- Encodes multiple renditions (480p, 720p)
- Creates master playlist with all versions
- R2 serves files globally with fast delivery

✅ **Frontend just needs proper HLS player**
- Chewie + video_player (easiest, already works)
- HLS.js (web, advanced control)
- ExoPlayer (Android native, best)
- AVPlayer (iOS native, best)

✅ **ABR works automatically**
- No special code needed
- Player measures bandwidth
- Player switches quality
- User gets smooth playback

**Start with Chewie - you're done!**

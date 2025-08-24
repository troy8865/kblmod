<?php
header('Content-Type: text/plain; charset=utf-8');

// MOD her zaman aktif (Workers için optimize)
$isMod = true;

$url = "https://core-api.kablowebtv.com/api/channels";
$headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6ImE2OTliODNmLTgyNmItNGQ5OS05MzYxLWM4YTMxMzIxOGQ0NiIsInNnZCI6Ijg5NzQxZmVjLTFkMzMtNGMwMC1hZmNkLTNmZGFmZTBiNmEyZCIsInNwZ2QiOiIxNTJiZDUzOS02MjIwLTQ0MjctYTkxNS1iZjRiZDA2OGQ3ZTgiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NDUxNTI4MjUsImV4cCI6MTc0NTE1Mjg4NSwiaWF0IjoxNzQ1MTUyODI1fQ.OSlafRMxef4EjHG5t6TqfAQC7y05IiQjwwgf6yMUS9E"
];

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_HTTPHEADER => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_ENCODING => 'gzip'
]);

$response = curl_exec($ch);
if (curl_errno($ch)) die('API Hatası: ' . curl_error($ch));
curl_close($ch);

$data = json_decode($response, true);
if (!$data || !$data['IsSucceeded'] || !isset($data['Data']['AllChannels'])) {
    die('API Geçersiz Yanıt Verdi');
}

echo "#EXTM3U\n";

foreach ($data['Data']['AllChannels'] as $channel) {
    if (empty($channel['Name']) || empty($channel['StreamData']['HlsStreamUrl'])) continue;
    
    $group = $channel['Categories'][0]['Name'] ?? 'Genel';
    if ($group === "Bilgilendirme") continue;
    
    // Kanal Bilgileri
    echo sprintf(
        '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s" group-title="%s",%s',
        $channel['Id'] ?? '',
        str_replace('"', '', $channel['Name']),
        $channel['PrimaryLogoImageUrl'] ?? '',
        str_replace('"', '', $group),
        $channel['Name']
    ) . "\n";
    
    // Stream URL (MOD aktifse Workers'a yönlendir)
    if ($isMod) {
        if (preg_match('/live_turksat_sub[0-9]*\/([^\/]+?)(?:_stream|$|\/)/', $channel['StreamData']['HlsStreamUrl'], $matches)) {
            $id = $matches[1];
            echo "https://kablo-stream.koprulu.workers.dev/?id=" . urlencode($id) . "&extension=m3u8\n";
        } else {
            echo $channel['StreamData']['HlsStreamUrl'] . "\n";
        }
    } else {
        echo $channel['StreamData']['HlsStreamUrl'] . "\n";
    }
}
?>

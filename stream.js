async function streamAudio(text) {
    try {
        console.log('リクエスト開始:', text);
        const requestData = {
            text: text,
            streaming: true,
            format: 'wav',
            normalize: true
        };
        console.log('リクエストデータ:', requestData);

        const response = await fetch('https://kaiwa-stream.dev-livetoon.com/v1/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            },
            body: JSON.stringify(requestData)
        });

        console.log('レスポンスステータス:', response.status);
        console.log('レスポンスヘッダー:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('エラーレスポンス:', errorText);
            throw new Error(`Network response was not ok: ${response.status} ${errorText}`);
        }

        // Web Audio APIの設定
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const reader = response.body.getReader();
        
        console.log('ストリーミング開始');
        
        // 受信したチャンクを保持する配列
        const chunks = [];
        
        // ストリーミング受信処理
        while (true) {
            const {done, value} = await reader.read();
            
            if (done) {
                console.log('ストリーミング完了');
                break;
            }
            
            // チャンクを配列に追加
            chunks.push(value);
            console.log('チャンク受信:', value.length, 'bytes');
        }

        // 全チャンクを結合
        const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const audioData = new Uint8Array(totalLength);
        let offset = 0;
        for (const chunk of chunks) {
            audioData.set(chunk, offset);
            offset += chunk.length;
        }

        // 音声データをデコード
        const audioBuffer = await audioContext.decodeAudioData(audioData.buffer);
        
        // 音声の再生
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(0);
        
        console.log('再生開始');
    } catch (error) {
        console.error('エラー発生:', error);
    }
}

// 使用例
// streamAudio("こんにちは、これはテストです");
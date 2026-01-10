import { useState, useEffect } from 'react';

const LiveTranscription = () => {
  const [transcriptions, setTranscriptions] = useState<string[]>([]);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/transcription');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };

    ws.onclose = () => {
      console.log('Transcription WebSocket closed');
    };

    ws.onerror = (error) => {
      console.error('Transcription WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (lastMessage) {
      setTranscriptions(prev => [...prev, `${lastMessage.call_sid}: ${lastMessage.transcript}`]);
    }
  }, [lastMessage]);

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-white mb-4">Live Transcription</h2>
      <div className="max-h-96 overflow-y-auto">
        {transcriptions.map((transcript, index) => (
          <p key={index} className="text-white">{transcript}</p>
        ))}
      </div>
    </div>
  );
};

export default LiveTranscription;

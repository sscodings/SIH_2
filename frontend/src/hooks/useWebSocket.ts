import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useAppStore } from '../stores/useAppStore';

export function useWebSocket(topic: string = 'all', onEvent?: (event: string, data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const setWsConnected = useAppStore((s) => s.setWsConnected);
  const incrementUnreadAlerts = useAppStore((s) => s.incrementUnreadAlerts);
  const setNarration = useAppStore((s) => s.setNarration);

  useEffect(() => {
    let reconnectTimeout: any;
    const connect = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/events');
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          ws.send(JSON.stringify({ action: 'subscribe', topic }));
        };

        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            const { event: eventType, data } = parsed;

            if (onEvent) {
              onEvent(eventType, data);
            }

            if (eventType === 'new_complaint') {
              toast.success(`NCRP Inflow: ${data.complaint_number} (₹${Number(data.amount_lost_inr).toLocaleString('en-IN')})`, {
                icon: '🚨',
                duration: 4000
              });
            } else if (eventType === 'new_alert') {
              incrementUnreadAlerts();
              toast.error(`ALERT [${data.severity}]: ${data.title}`, {
                icon: '⚠️',
                duration: 5000
              });
            } else if (eventType === 'vasp_found') {
              toast.success(`VASP ATTRIBUTED: ${data.vasp_name} (${data.confidence_score}% Confidence)`, {
                icon: '🏛️',
                duration: 6000
              });
            } else if (eventType === 'hop_discovered' && data.narration) {
              setNarration(data.narration);
            }
          } catch (e) {
            console.error('WS parse error:', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
          ws.close();
        };
      } catch (err) {
        setWsConnected(false);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [topic, onEvent, setWsConnected, incrementUnreadAlerts, setNarration]);

  return wsRef;
}

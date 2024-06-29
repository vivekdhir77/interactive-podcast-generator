import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';

export default function Home() {
  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState('30');
  const [podcastContent, setPodcastContent] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [podcastContent]);

  const startPodcast = async () => {
    setIsStreaming(true);
    setPodcastContent([]);
    const response = await fetch('http://localhost:8000/generate-podcast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, duration: parseInt(duration) }),
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const decodedChunk = decoder.decode(value, { stream: true });
      const lines = decodedChunk.split('\n');
      lines.forEach((line) => {
        if (line.trim() !== '') {
          if (line.trim() === 'END_OF_PODCAST') {
            setIsStreaming(false);
          } else {
            setPodcastContent((prev) => [...prev, line]);
          }
        }
      });
    }
  };

  const askQuestion = async () => {
    const response = await fetch('http://localhost:8000/ask-question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    setPodcastContent((prev) => [...prev, `Listener: ${question}`, data.answer]);
    setQuestion('');
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">AI Podcast Generator</h1>
      <div className="mb-4">
        <Input
          type="text"
          placeholder="Enter podcast topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="mb-2"
        />
        <Input
          type="number"
          placeholder="Duration (minutes)"
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          className="mb-2"
        />
        <Button onClick={startPodcast} disabled={isStreaming}>
          Start Podcast
        </Button>
      </div>
      <div
        ref={contentRef}
        className="bg-gray-100 p-4 h-96 overflow-y-auto mb-4"
      >
        {podcastContent.map((content, index) => (
          <p key={index}>{content}</p>
        ))}
      </div>
      <div className="flex">
        <Input
          type="text"
          placeholder="Ask a question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-grow mr-2"
        />
        <Button onClick={askQuestion} disabled={!isStreaming}>
          Ask
        </Button>
      </div>
    </div>
  );
}
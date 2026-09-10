// Browser Web Speech API Service with asynchronous voice loading & clean state recovery

class SpeechService {
  constructor() {
    this.synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
    this.voices = [];
    this.recognition = null;
    
    if (this.synth) {
      this.loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this.loadVoices();
      }
    }
    this.initRecognition();
  }

  loadVoices() {
    if (this.synth) {
      this.voices = this.synth.getVoices();
    }
  }

  initRecognition() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
      }
    }
  }

  speak(text, onEndCallback) {
    if (!this.synth || !text) return;

    this.synth.cancel();

    // Clean markdown formatting characters for speech
    const cleanText = text
      .replace(/```[\s\S]*?```/g, 'Code block omitted.')
      .replace(/!\[.*?\]\(.*?\)/g, 'Generated image.')
      .replace(/[*_#`~]/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    if (this.voices.length === 0) this.loadVoices();

    const preferredVoice = this.voices.find(v => 
      (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David') || v.name.includes('Zira')) && v.lang.startsWith('en')
    ) || this.voices.find(v => v.lang.startsWith('en'));

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    if (onEndCallback) {
      utterance.onend = onEndCallback;
      utterance.onerror = onEndCallback;
    }

    this.synth.speak(utterance);
  }

  stopSpeech() {
    if (this.synth) {
      this.synth.cancel();
    }
  }

  startListening(onResultCallback, onErrorCallback, onEndCallback) {
    if (!this.recognition) {
      if (onErrorCallback) onErrorCallback('Speech recognition is not supported in this browser.');
      return;
    }

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResultCallback) onResultCallback(transcript);
    };

    this.recognition.onerror = (event) => {
      if (onErrorCallback) onErrorCallback(event.error);
    };

    this.recognition.onend = () => {
      if (onEndCallback) onEndCallback();
    };

    try {
      this.recognition.start();
    } catch (err) {
      console.warn('Recognition start warning:', err);
    }
  }

  stopListening() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.warn(err);
      }
    }
  }
}

export const speechService = new SpeechService();

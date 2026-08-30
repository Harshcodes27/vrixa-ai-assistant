class JarvisBrain {
  constructor() {
    this.responses = {
      'hi': ['Hello! Harsh Sir, I am ready to assist you.', 'Hi Harsh Sir, I am standing by for your command.'],
      'greetings': ['Hello Harsh Sir, all systems are operational.'],
      'how are you': ['I am operating at peak efficiency, thank you for asking Harsh Sir.'],
      'hello': ['Hello Harsh Sir, I am ready to assist you.'],
      'thank you jarvis': ['Always a pleasure to assist you, Harsh Sir!'],
      'introduce': ['I am Jarvis, your personal AI assistant created by Harsh Sir (Roll No: 23035004049).'],
      'who created you': ['I am Jarvis, your intelligent AI assistant created by Harsh Sir (Roll No: 23035004049) at NGF College, Palwal!'],
      'friend': ['Your close friends are:\n• Harshit\n• Ayush\n• Kartikey\n• Kartik\n• Aniket\n• Bhupender\n\nAlways ready to assist you and your friends, Harsh Sir!'],
      'friends': ['Your close friends are:\n• Harshit\n• Ayush\n• Kartikey\n• Kartik\n• Aniket\n• Bhupender\n\nAlways ready to assist you and your friends, Harsh Sir!'],
      'dost': ['Your close friends are:\n• Harshit\n• Ayush\n• Kartikey\n• Kartik\n• Aniket\n• Bhupender\n\nAlways ready to assist you and your friends, Harsh Sir!'],
    };
  }

  getMemories() {
    try {
      const saved = localStorage.getItem('JARVIS_LONG_TERM_MEMORY');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  }

  saveMemory(fact) {
    if (!fact || typeof fact !== 'string') return;
    const cleanFact = fact.trim();
    if (!cleanFact) return;

    const memories = this.getMemories();
    const exists = memories.some(m => m.toLowerCase() === cleanFact.toLowerCase());
    
    if (!exists) {
      memories.push(cleanFact);
      localStorage.setItem('JARVIS_LONG_TERM_MEMORY', JSON.stringify(memories));
    }
  }

  detectAndStoreMemory(text) {
    const lower = text.toLowerCase();
    if (lower.includes("remember that") || lower.includes("remember this") || lower.includes("remember ")) {
      const cleanFact = text.replace(/remember that|remember this|remember/gi, "").trim();
      if (cleanFact) {
        this.saveMemory(cleanFact);
        return `Got it, Sir! I have saved to my long-term memory: "${cleanFact}".`;
      }
    }
    if (lower.includes("my friend") || lower.includes("my name is") || lower.includes("i live in")) {
      this.saveMemory(text);
    }
    return null;
  }

  getPredefinedResponse(input) {
    const lower = input.toLowerCase();
    for (let key in this.responses) {
      if (lower.includes(key)) {
        const list = this.responses[key];
        return list[Math.floor(Math.random() * list.length)];
      }
    }
    return null;
  }

  async playAlarmChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const audioCtx = new AudioCtx();
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
      osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1.5);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 1.5);
    } catch (e) {
      console.warn("Audio Context error:", e);
    }
  }

  async fetchLiveWeather(city) {
    try {
      const cleanCity = city.trim();
      if (!cleanCity) return "Please specify a city name, Sir.";

      const res = await fetch(`https://wttr.in/${encodeURIComponent(cleanCity)}?format=j1`);
      if (!res.ok) throw new Error("Weather service unreachable");
      const data = await res.json();
      const current = data.current_condition[0];
      const tempC = current.temp_C;
      const desc = current.weatherDesc[0].value;
      const humidity = current.humidity;
      const windSpeed = current.windspeedKmph;

      return `Current Weather in ${cleanCity.toUpperCase()}: ${tempC}°C, ${desc}. Humidity: ${humidity}%, Wind: ${windSpeed} km/h.`;
    } catch (e) {
      return `Sorry Sir, I could not fetch live weather data for ${city} right now.`;
    }
  }

  async processInput(userInput, attachments = [], customApiKey = '') {
    const text = userInput.trim();
    const lower = text.toLowerCase();

    // 1. Check AI Image Generation commands
    if (lower.startsWith("generate image") || lower.startsWith("draw") || lower.startsWith("create image") || lower.startsWith("make an image")) {
      const imagePrompt = text.replace(/generate image of|generate image|draw|create image of|create image|make an image of|make an image/gi, "").trim();
      if (imagePrompt) {
        const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(imagePrompt)}?width=1024&height=1024&seed=${Math.floor(Math.random() * 100000)}&nologo=true`;
        return `Here is your generated image for **"${imagePrompt}"**, Sir:\n\n![${imagePrompt}](${imageUrl})`;
      }
    }

    // 2. Check Reminder / Alarm commands (Flexible RegEx)
    const reminderMatch = lower.match(/(?:set\s+)?(?:remind me in|timer|alarm|remind me)\s*(?:for|in)?\s*(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\s*(?:to|for)?\s*(.*)/i);
    if (reminderMatch) {
      const num = parseInt(reminderMatch[1]);
      const unit = reminderMatch[2].toLowerCase();
      const task = reminderMatch[3] ? reminderMatch[3].trim() : "your scheduled task";

      let multiplier = 1000;
      if (unit.startsWith("min")) multiplier = 60 * 1000;
      if (unit.startsWith("hour") || unit.startsWith("hr")) multiplier = 3600 * 1000;

      const durationMs = num * multiplier;

      setTimeout(() => {
        this.playAlarmChime();
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("JARVIS Reminder", { body: `Sir, time to: ${task}`, icon: "/favicon.ico" });
        } else {
          alert(`⏰ JARVIS REMINDER: Sir, time to ${task}!`);
        }
      }, durationMs);

      if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
      }

      return `Alarm set Sir! I will remind you to "${task}" in ${num} ${unit}.`;
    }

    // 3. Check Live Weather queries
    if (lower.includes("weather")) {
      const cityMatch = text.match(/weather\s+(?:in|of|for|at)?\s*([a-zA-Z\s]+)/i);
      if (cityMatch && cityMatch[1] && cityMatch[1].trim().length > 1) {
        return await this.fetchLiveWeather(cityMatch[1].trim());
      }
    }

    // 4. Check memory detection
    const memoryConfirmation = this.detectAndStoreMemory(text);
    if (memoryConfirmation && attachments.length === 0) {
      return memoryConfirmation;
    }

    // 5. Web Automation commands
    if (lower.includes("open youtube")) {
      window.open("https://www.youtube.com", "_blank");
      return "Opening YouTube Sir.";
    }
    if (lower.includes("open google")) {
      window.open("https://www.google.com", "_blank");
      return "Opening Google Sir.";
    }
    if (lower.includes("play music") || lower.includes("play song")) {
      window.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s", "_blank");
      return "Playing your favourite song Sir.";
    }

    // 6. Predefined responses (only if no attachments)
    if (attachments.length === 0) {
      const predefined = this.getPredefinedResponse(lower);
      if (predefined) return predefined;
    }

    // 7. Gemini REST API with Comprehensive Multi-Model Fallback Engine
    const apiKey = customApiKey || localStorage.getItem('GEMINI_API_KEY') || import.meta.env.VITE_GEMINI_API_KEY || '';
    if (!apiKey) {
      return "Sir, please configure your Gemini API Key in Settings to analyze files, images, or answer AI queries.";
    }

    const memories = this.getMemories();
    let memoryContext = "";
    if (memories.length > 0) {
      memoryContext = `\n[GLOBAL MEMORY STORED ABOUT USER ACROSS ALL CHATS]:\n- ${memories.join('\n- ')}\n`;
    }

    let promptText = `You are Jarvis, an advanced AI assistant inspired by Iron Man.${memoryContext}\nUser prompt: ${text || "Please analyze the attached files/images."}`;

    const partsPayload = [];
    if (attachments.length > 0) {
      attachments.forEach(att => {
        if (att.type === 'image') {
          const base64Data = att.data.split(',')[1];
          partsPayload.push({
            inline_data: {
              mime_type: att.mimeType,
              data: base64Data
            }
          });
        } else if (att.type === 'document') {
          promptText += `\n\n[ATTACHED FILE CONTEXT - ${att.name}]:\n${att.data.substring(0, 12000)}`;
        }
      });
    }

    partsPayload.unshift({ text: promptText });

    // Comprehensive model candidate array across v1beta endpoints
    const modelCandidates = [
      'gemini-3.6-flash',
      'gemini-flash-latest',
      'gemini-3.5-flash',
      'gemini-3.5-flash-lite',
      'gemini-2.5-flash-lite',
      'gemini-2.5-flash',
      'gemini-2.0-flash',
      'gemini-1.5-flash'
    ];

    let lastError = null;

    for (const model of modelCandidates) {
      try {
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts: partsPayload }] })
        });

        if (res.ok) {
          const resData = await res.json();
          const reply = resData.candidates?.[0]?.content?.parts?.[0]?.text;
          if (reply) return reply.trim();
        } else {
          const errJson = await res.json().catch(() => ({}));
          lastError = errJson.error?.message || `Status ${res.status}`;
        }
      } catch (err) {
        lastError = err.message;
      }
    }

    return `Sorry Sir, error processing AI request: ${lastError || 'Check API key or model availability.'}`;
  }
}

export const jarvisBrain = new JarvisBrain();
